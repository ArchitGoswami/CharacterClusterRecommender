import json
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
import numpy as np
import re
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import umap 
# stop words for labelling
stop_words = set(stopwords.words('english'))

# build list of character tropes 
def get_tropes_from_json():
    tropes_list = []
    chars_list = []
    tvtropes = "data/raw/tvtropes"
    for filename in os.listdir(tvtropes):
        if filename.endswith(".json"):
            with open(os.path.join(tvtropes, filename), "r") as f:
                df = pd.read_json(f)
                chars = df["characters"]
                for char in chars:
                    if char.get("name") !=  "open/close all folders":
                        tropes_list.extend(char["tropes"])
    # remove duplicates
    tropes_list = set(tropes_list)
    tropes_list = list(tropes_list)
    
    return tropes_list

# for each trope, get corresponding article (already crawled for)
def get_docs_from_tropes(tropes_list):
    docs = {}  
    for trope in tropes_list:
        file_path = f"data/raw/tvtropes_tropes/{trope}.json"  # build file name
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f) 
                body_txt = data.get("body_txt", "")  
                tokens = word_tokenize(body_txt.lower())
                together = " ".join(tokens)
                docs[trope] = together 
        else:
            print(f"File not found: {file_path}")
            
    return docs

def cluster_docs(docs_dict, output_dir="FINAL_CLUSTERS/clustering_with_sep_title", mode = "none"):
    # get trope + document
    titles = list(docs_dict.keys())
    bodies = list(docs_dict.values())
    
    # embed as vector
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # mode (whether to include titles)
    if mode == "full":
        texts = [ 
            f"{title}. {title}. {body}"
            for title, body in zip(titles, bodies)
        ]
        embeddings = model.encode(texts)
    elif mode == "sep":
        texts = [
            f"{re.sub(r'(?<!^)(?=[A-Z])', ' ', title)}. {re.sub(r'(?<!^)(?=[A-Z])', ' ', title)}. {body}"
            for title, body in zip(titles, bodies)]
        embeddings = model.encode(texts)
    else:
        embeddings = model.encode(bodies)
        
    # reduce dimensionality to improve performance
    # https://umap-learn.readthedocs.io/en/latest/clustering.html
    reducer = umap.UMAP(
        n_neighbors=15,
        n_components=10,
        metric='cosine',
        n_jobs=1
    )
    reduced = reducer.fit_transform(embeddings)

    # actual clustering (hierarchical density-based clustering)
    clusterer = HDBSCAN(
        min_cluster_size=5,
        metric='euclidean'
    )
    labels = clusterer.fit_predict(reduced)
    avg_confidence = np.mean(clusterer.probabilities_)
    
    clusters = {}
    for title, label in zip(titles, labels):
        clusters.setdefault(label, []).append(title)

    # simple tf-idf to label clusters with common words
    cluster_labels = {}
    # additional trope-specific stopwords, these for some reason turn up a lot in contexts they shouldn't. For example, multiple clusters were named "english_ritual_fat"...
    exclude = ["trope", "character", "plot", "story", "also", "characters", "tropes", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "ojou", "may", "often", "person", "even", "usually", "like", "hero", "see", "shoulder"]
    for cluster_id, titles in clusters.items():
        title_to_body = docs_dict
        if cluster_id == -1:  # skip unclustered
            continue
        # build docs
        docs = []
        for t in titles:
            b = title_to_body[t]
            tt = re.sub(r'(?<!^)(?=[A-Z])', ' ', t)
            add = []
            for word in re.findall(r"\b\w+\b", b.lower()):
                if word.lower() not in exclude:
                    add.append(word)
            # title words are 4x more important, so add 4x
            for word in re.findall(r"\b\w+\b", tt.lower()):
                if word.lower() not in exclude:
                    add.append(word)
                    add.append(word)
                    add.append(word)
                    add.append(word)
            docs.append(" ".join(add))
        vec = TfidfVectorizer(stop_words=list(stop_words))
        tfidf = vec.fit_transform(docs)

        # sum tf-idf across documents in cluster
        scores = np.asarray(tfidf.sum(axis=0)).ravel()
        terms = vec.get_feature_names_out()

        # top 3 words occurring
        top3_idx = scores.argsort()[-3:][::-1]
        top3_words = terms[top3_idx]
        best_word = "_".join(top3_words)

        # add these as cluster label
        cluster_labels[cluster_id] = best_word
    # if unclustered (-1)
    cluster_labels[-1] = "unclustered"
    
    # get average probability (cluster effectiveness)
    avg_probs = {}
    for cluster_id in set(labels):
        if cluster_id != -1: 
            idx = np.where(labels == cluster_id)[0]
            avg_probs[cluster_id] = np.mean(clusterer.probabilities_[idx])

    # put clusters in txt files
    os.makedirs(output_dir, exist_ok=True)
    # see how many were recorded (debugging)
    ct = 0
    for cluster_id, cluster_titles in clusters.items():
        filepath = os.path.join(output_dir, f"cluster_{cluster_id}_{cluster_labels[cluster_id]}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            ct = ct + 1
            f.write(f"{cluster_id}: {cluster_labels[cluster_id]}\n")
            if(cluster_id != -1):
                f.write(f"score: {avg_probs[cluster_id]}\n")
            for title in cluster_titles:
                f.write(f"{title}\n")
        print(f"Cluster {cluster_id}: {len(cluster_titles)}")
    print(f"\nSaved {ct} clusters to files")
    print(f"Average confidence was: {avg_confidence}\n")


# run full pipeline
print(f"Getting tropes list...")
tropes = get_tropes_from_json()
print(f"Got {len(tropes)} tropes.")
print(f"Getting docs list...")
docs = get_docs_from_tropes(tropes)
print(f"Got {len(docs)} docs.")
print(f"Clustering...")
cluster_docs(docs, dir = "FINAL_CLUSTERS/without_title", mode="none")
print(f"Done!")



