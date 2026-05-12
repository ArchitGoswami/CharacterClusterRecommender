import json
import os
from pyexpat import model
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
import numpy as np
import re
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from sklearn.preprocessing import normalize
import umap 

def get_tropes_from_json():
    tropes_list = []
    chars_list = []
    tvtropes = "/Users/alisongunzler/Desktop/FP_IWRA/WAandIRFinalProject/data/raw/tvtropes"
    for filename in os.listdir(tvtropes):
        # print(filename)
        if filename.endswith(".json"):
            with open(os.path.join(tvtropes, filename), "r") as f:
                df = pd.read_json(f)
                chars = df["characters"]
                for char in chars:
                    if char.get("name") !=  "open/close all folders":
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

def cluster_docs(docs, output_dir="created_clusters_retry_weight"):
    
    # get trope + document
    titles = list(docs.keys())
    bodies = list(docs.values())
    
    # weight title 2x more than body text
    texts = [ 
        f"{title}. {title}. {body}"
        for title, body in zip(titles, bodies)
    ]
    
    # embed as vector
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    
    # reduce dimensionality so more things are clustered
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
    
    clusters = {}
    
    ## TODO w/in each cluster, check pos/neg sentiment 
    ## TODO name clusters based on most common words in the cluster (after removing stop words)
    
    for title, label in zip(titles, labels):
        clusters.setdefault(label, []).append(title)

    # put clusters in txt files
    os.makedirs(output_dir, exist_ok=True)
    for cluster_id, cluster_titles in clusters.items():
        filepath = os.path.join(output_dir, f"cluster_{cluster_id}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            for title in cluster_titles:
                f.write(f"{title}\n")
        print(f"Cluster {cluster_id}: {len(cluster_titles)}")
    
print(f"Getting tropes list...")
tropes = get_tropes_from_json()
print(f"Got {len(tropes)} tropes.")
print(f"Getting docs list...")
docs = get_docs_from_tropes(tropes)
print(f"Clustering...")
cluster_docs(docs)
print(f"Done!")



