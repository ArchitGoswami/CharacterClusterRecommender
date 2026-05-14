import os

cts = {}
dir = "./FINAL_CLUSTERS/clustering_with_full_title/"
for file in os.listdir(dir):
    with open(os.path.join(dir, file), "r") as f:
        for line in f:
            cts[file] = cts.get(file, 0) + 1
            
print("regular title clusters:")     
reg_top = sorted(cts.items(), key=lambda d: d[1], reverse=True)[:11]
for cluster, count in reg_top:
    print(f"{cluster}: {count}")


cts2 = {}
dir = "./FINAL_CLUSTERS/clustering_with_sep_title/"
for file in os.listdir(dir):
    with open(os.path.join(dir, file), "r") as f:
        for line in f:
            cts2[file] = cts2.get(file, 0) + 1

print("broken title clusters:") 
brok_top = sorted(cts2.items(), key=lambda d: d[1], reverse=True)[:11]
for cluster, count in brok_top:
    print(f"{cluster}: {count}")

cts3 = {}
dir = "./FINAL_CLUSTERS/clustering_without_title/"
for file in os.listdir(dir):
    with open(os.path.join(dir, file), "r") as f:
        for line in f:
            cts3[file] = cts3.get(file, 0) + 1

print("no title clusters:") 
no_top = sorted(cts3.items(), key=lambda d: d[1], reverse=True)[:11]
for cluster, count in no_top:
    print(f"{cluster}: {count}")
