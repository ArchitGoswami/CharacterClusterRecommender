import os
import pandas as pd

char_name = input("Enter a character: ")
# Miss Catherine "Kitty" Bennet, Nightingale (Kaur, Quinn)

clusters = {}

for filename in os.listdir("../FINAL_CLUSTERS/clustering_with_sep_title"):
        if not filename.endswith(".txt"):
            continue

        cluster_name = filename.replace(".txt", "")
        if cluster_name == "cluster_-1_unclustered":
            cluster_name = "No Cluster"
        path = os.path.join("../FINAL_CLUSTERS/clustering_with_sep_title", filename)

        with open(path, "r", encoding="utf-8") as f:
            words = [
                line.strip()
                for i, line in enumerate(f)
                if i >= 2 and line.strip()
            ]
        for word in words:
            clusters[word] = cluster_name
            
chars_list = []
target_tropes = []
char_media = ""

for file in os.listdir("../data/raw/tvtropes"):
    if file.endswith(".json"):
        with open(os.path.join("../data/raw/tvtropes", file), "r", encoding="utf-8") as f:
            df = pd.read_json(f)
            chars = df["characters"]
            for char in chars:
                # print(char.get("name"))
                if char.get("name") == char_name: #and char.get("media_title") == char_media:
                    print(char.get("name"))
                    char_media = char.get("media_title")
                    target_tropes.extend(char["tropes"])
                elif char.get("name") !=  "open/close all folders":
                    chars_list.append(char)
                    char["clusters"] = []
                    for trope in char["tropes"]:
                        char["clusters"].append(clusters.get(trope, "No Cluster"))

target_clusters = []
for trope in target_tropes:
    target_clusters.append(clusters.get(trope, "No Cluster"))

print(char_media)
# print(target_tropes)
# print(target_clusters)
# print(chars_list[0])

# TODO 
weight_tropes = 3
weight_clusters = 1

for char in chars_list:
    count_tropes = 0
    count_clusters = 0
    common_tropes = []
    common_clusters = []
    for trope in char["tropes"]:
        if trope in target_tropes:
            count_tropes += 1
            common_tropes.append(trope)
    for cluster in char["clusters"]:
        if cluster in target_clusters and cluster != "No Cluster":
            count_clusters += 1
            common_clusters.append(cluster)
    char["score"] = count_tropes * weight_tropes + count_clusters * weight_clusters
    # count_tropes * weight_tropes + count_clusters * weight_clusters + count personality vec * w + 
    # person -> <1, 0, >
    # scale happy-sad
    
    # tropes, personality clusters
    # <1, 1, 1, 1, 0, 1> * w1, <0,1,1, 0, 0, 1> * w2 f(v1, v2) = v3 sim(q3, v3)
    # tropes -> traits
    # LLM?
    char["common_tropes"] = common_tropes
    char["common_clusters"] = common_clusters
    
# print(chars_list[0])

top_5 = sorted(chars_list, key=lambda d: d["score"], reverse=True)[:5]
for best in top_5:
    print(f"Best match: {best['name']} from {best['media_title']} with score {best['score']}")
    print(f"Common tropes: {best['common_tropes']}")
    print(f"Common clusters: {best['common_clusters']}")