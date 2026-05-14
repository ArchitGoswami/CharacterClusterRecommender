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


# get vocabulary
def get_list(mode = "small"):
    vocab = []

    # large or small set
    if mode == "large":
        dir = "possible_word_vars/combo_in_pitch_rew.txt"
    else:
        dir = "possible_word_vars/combo_with_big_list.txt"
        
    # read file
    with open(dir, 'r') as f:
        vocab = f.readlines()
        # add category for better cluster
        for i, line in enumerate(vocab): 
            vocab[i] = "character trait: " + line.strip()
    vocab = [line.strip() for line in vocab][1:] # first line is metadata
    # remove duplicates
    vocab = set(vocab)
    vocab = list(vocab)
    return vocab


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

def cluster_docs(docs, vocab, output_dir="test"):

    model = SentenceTransformer('all-MiniLM-L6-v2')

    titles = list(docs.keys())
    bodies = list(docs.values())

    # encode vocab labels
    word_embeddings = model.encode(vocab, normalize_embeddings=True)

    # encode document bodies
    sentence_embeddings = model.encode(bodies, normalize_embeddings=True)

    classified = []
    scores = {}
    cts = {}
    tot_s = 0
    ct = 0
    
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
        
        scores[best_word] = scores.get(best_word, 0) + best_score
        cts[best_word] = cts.get(best_word, 0) + 1
        tot_s = tot_s + best_score
        ct = ct + 1
         
    print(
        f"Score: {tot_s/ct}: "
    )

    os.makedirs(output_dir, exist_ok=True)

    for word in vocab:
        filepath = os.path.join( output_dir, f"cluster_{word}.txt" )
        with open(filepath, "a", encoding="utf-8") as f:
            f.write( f"Score: {scores.get(word,0)/cts.get(word,1)}\n" )

    # append each trope to its label file
    for item in classified:
        if(item["score"] > 0.25):  # threshold for "unclassified"
            filepath = os.path.join( output_dir, f"cluster_{item['label']}.txt" )

            with open(filepath, "a", encoding="utf-8") as f:
                f.write( f"{item['title']}\n" )

            print(
                f"{item['title']}: "
                f"{item['label']} "
                f"({item['score']:.3f})"
            )
        else:
            filepath = os.path.join( output_dir, f"unclassed.txt" )

            with open(filepath, "a", encoding="utf-8") as f:
                f.write( f"{item['title']}\n" )
    
print(f"Getting tropes list...")
tropes = get_tropes_from_json()
vocab = get_list()
print(f"Getting docs list...")
docs = get_docs_from_tropes(tropes)
print(f"Clustering...")
cluster_docs(docs, vocab)
print(f"Done!")



