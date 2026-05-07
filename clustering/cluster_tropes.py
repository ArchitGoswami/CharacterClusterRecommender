import json
import os
from pyexpat import model
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
import re
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

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
                chars_list.append(chars)
                tropes_list.extend(chars_list[0][0]["tropes"])
                
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

def cluster_docs(docs):
    titles = list(docs.keys())
    bodies = list(docs.values())
    print(bodies)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(bodies)
    dbscan = DBSCAN(metric='cosine', eps=0.35, min_samples=2)
    
    labels = dbscan.fit_predict(embeddings)
    
    clusters = {}
    for title, label in zip(titles, labels):
        clusters.setdefault(label, []).append(title)

    for cluster_id, cluster_titles in clusters.items():
        print(f"Cluster {cluster_id}: {cluster_titles}")
    

docs = get_docs_from_tropes(get_tropes_from_json())
cluster_docs(docs)



