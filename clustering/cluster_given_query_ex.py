import csv
import json
import os
from pyexpat import model
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN, AgglomerativeClustering
import numpy as np
import re
import nltk
from sklearn.metrics.pairwise import cosine_similarity
nltk.download('punkt')
from nltk.tokenize import word_tokenize


def get_list():
    # with open('/Users/alisongunzler/Desktop/FP_IWRA/WAandIRFinalProject/possible_word_vars/combo_with_big_list.txt', 'r') as f:
    #     vocab = f.readlines()

    # vocab = [line.strip() for line in vocab]

    # vocab = vocab[1:]

    # # print(vocab)
    # vocab = set(vocab)
    # vocab = list(vocab)
    # return vocab
    
    vocab = []

    with open("/Users/alisongunzler/Desktop/FP_IWRA/WAandIRFinalProject/possible_word_vars/refines_big_list.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        # add category for better cluster
        for row in reader:
            ex = ""
            label = row[2]
            if label == 1 or label == 6:
                ex = "personality trait: character is a person who is "
            elif label == 2 or label == 3:
                ex = "appearance trait: character is a person who is " 
            elif label == 4:
                ex = "sexuality: character is a person who is "
            elif label == 5:
                ex = "relationship trait: character is a person who is "
            else:
                ex = ""
                
            vocab.append(ex + row[0])
    vocab = [line.strip() for line in vocab]
    vocab = set(vocab)
    vocab = list(vocab)
    return vocab


def get_tropes_from_json():
    tropes_list = []
    chars_list = []
    tvtropes = "../data/raw/tvtropes"
    for filename in os.listdir(tvtropes):
        # print(filename)
        if filename.endswith(".json"):
            with open(os.path.join(tvtropes, filename), "r") as f:
                df = pd.read_json(f)
                chars = df["characters"]
                for char in chars:
                    tropes_list.extend(char["tropes"])
                
    # print(tropes_list)
    tropes_list = set(tropes_list)
    tropes_list = list(tropes_list)
    return tropes_list

def get_docs_from_tropes(tropes_list):
    docs = {}  # store all JSON contents

    for trope in tropes_list:
        file_path = f"data/raw/tvtropes_tropes/{trope}.json"  # build file name
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)  # parse JSON
                body_txt = data.get("body_txt", "")  # get body text
                tokens = word_tokenize(body_txt.lower())
                together = " ".join(tokens)
                docs[trope] = together  # store in dict
                # print(tokens)
        else:
            print(f"File not found: {file_path}")
            
    return docs

def cluster_docs(docs, vocab, output_dir="created_clusters_given_ex_v2"):

    model = SentenceTransformer('all-MiniLM-L6-v2')

    titles = list(docs.keys())
    bodies = list(docs.values())

    # encode vocab labels
    word_embeddings = model.encode(vocab, normalize_embeddings=True)

    # encode document bodies
    sentence_embeddings = model.encode(bodies, normalize_embeddings=True)

    classified = []

    for title, sent_emb in zip(titles, sentence_embeddings):

        sims = cosine_similarity([sent_emb], word_embeddings)[0]

        best_idx = np.argmax(sims)
        best_word = vocab[best_idx]
        best_score = sims[best_idx]

        classified.append({
            "title": title,
            "label": best_word,
            "score": float(best_score)
        })

    os.makedirs(output_dir, exist_ok=True)

    # append each trope to its label file
    for item in classified:
        if(item["score"] > 0.3):  # threshold for "unclassified"
            filepath = os.path.join(
                output_dir,
                f"cluster_{item['label']}.txt"
            )

            with open(filepath, "a", encoding="utf-8") as f:
                f.write(
                    f"{item['title']} "
                    f"({item['score']:.3f})\n"
                )

            print(
                f"{item['title']} => "
                f"{item['label']} "
                f"({item['score']:.3f})"
            )
        else:
            filepath = os.path.join(
                output_dir,
                f"unclassed.txt"
            )

            with open(filepath, "a", encoding="utf-8") as f:
                f.write(
                    f"{item['title']} "
                    f"{item['label']} "
                    f"({item['score']:.3f})\n"
                )

    return classified
    
    # clustering = AgglomerativeClustering()
    # labels = clustering.fit_predict(embeddings)

    # clusters = {}
    # for tag, label in zip(titles, labels):
    #     clusters.setdefault(label, []).append(tag)

    # os.makedirs(output_dir, exist_ok=True)
    # for cluster_id, cluster_tags in clusters.items():
    #     filepath = os.path.join(output_dir, f"cluster_{cluster_id}.txt")
    #     with open(filepath, "w", encoding="utf-8") as f:
    #         for title in cluster_titles:
    #             f.write(f"{title}\n")
    #     print(f"Cluster {cluster_id}: {len(cluster_tags)}")
    # dbscan = DBSCAN(metric='cosine', eps=0.35, min_samples=10)
    
    # labels = dbscan.fit_predict(embeddings)
    
    # clusters = {}
    # for title, label in zip(titles, labels):
    #     clusters.setdefault(label, []).append(title)

    # os.makedirs(output_dir, exist_ok=True)
    # for cluster_id, cluster_titles in clusters.items():
    #     filepath = os.path.join(output_dir, f"cluster_{cluster_id}.txt")
    #     with open(filepath, "w", encoding="utf-8") as f:
    #         for title in cluster_titles:
    #             f.write(f"{title}\n")
    #     print(f"Cluster {cluster_id}: {len(cluster_titles)}")
    
print(f"Getting tropes list...")
tropes = get_tropes_from_json()
vocab = get_list()
print(f"Getting docs list...")
docs = get_docs_from_tropes(tropes)
print(f"Clustering...")
cluster_docs(docs, vocab)
print(f"Done!")



