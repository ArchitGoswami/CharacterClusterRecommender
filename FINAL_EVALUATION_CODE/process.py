import os
import re

title_dirs = ['with_full_title.txt', 'with_sep_title.txt', 'without_title.txt']
vocab_dirs = ['small_vocab.txt', 'large_vocab.txt']


title_data = []

for fil in title_dirs:
    curr_data = []
    current = None  

    with open(fil, "r", encoding="utf-8") as f:
        print("reading:", fil, "size:", os.path.getsize(fil))
        for line in f:
            line = line.strip()
            if not line:
                continue

            m = re.match(r"(\d+):\s*(.+)", line)
            if m:
                if current:
                    curr_data.append(current)

                current = {
                    "index": int(m.group(1)),
                    "name": m.group(2),
                    "avg_score": None,
                    "meaning": None,
                    "scores": []
                }
                continue

            if current is None:
                continue 

            if line.startswith("average score:"):
                current["avg_score"] = float(line.split(":")[1].strip())
                continue

            if line.startswith("human assigned meaning:"):
                current["meaning"] = line.split(":", 1)[1].strip()
                continue

            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                current["scores"].append(int(parts[1]))

    if current:
        curr_data.append(current)

    # print(curr_data)
    title_data.append(curr_data)
# print(title_data)

for name, data in zip(title_dirs, title_data) :
    tot_syns = 0
    tot_ants = 0
    tot_unr = 0
    tot = 0
    lens = 0
    print(f"{name}:") 
    print() 
    for entry in data:
        syns = 0
        ants = 0
        unr = 0
        for score in entry["scores"]:
            if score == 1:
                syns += 1
            elif score == 0:
                ants += 1
            else: 
                unr += 1
        tot += entry["avg_score"]
        tot_syns += syns
        tot_ants += ants
        tot_unr += unr
        print(f"{entry["name"]}:") 
        print(f"meaning: {entry["meaning"]}")
        print(f"{syns} synonyms, {ants} antonyms, {unr} unrelated")
        print(f"average score: {entry["avg_score"]}") 
        print(f"accuracy: {(syns - unr) / len(entry["scores"])}") 
        lens += len(entry["scores"])
    print(f"Overall:") 
    print(f"{tot_syns} synonyms, {tot_ants} antonyms, {tot_unr} unrelated")
    print(f"average score: {tot/10}:")
    print(f"accuracy: {(tot_syns - tot_unr)/lens}")    
    print()    
              

vocab_data = []

for fil in vocab_dirs:
    curr_data = []
    current = None  

    with open(fil, "r", encoding="utf-8") as f:
        print("reading:", fil, "size:", os.path.getsize(fil))
        for line in f:
            line = line.strip()
            if not line:
                continue

            m = re.match(r"(\d+):\s*(.+)", line)
            if m:
                if current:
                    curr_data.append(current)

                current = {
                    "index": int(m.group(1)),
                    "name": m.group(2),
                    "avg_score": None,
                    "scores": []
                }
                continue

            if current is None:
                continue 

            if line.startswith("Average Score:"):
                current["avg_score"] = float(line.split(":")[1].strip())
                # print("yes")
                continue

            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                current["scores"].append(int(parts[1]))

    if current:
        curr_data.append(current)

    # print(curr_data)
    vocab_data.append(curr_data)
    

for name, data in zip(vocab_dirs, vocab_data) :
    tot_syns = 0
    tot_ants = 0
    tot_unr = 0
    tot = 0
    lens = 0
    print(f"{name}:") 
    print() 
    for entry in data:
        syns = 0
        ants = 0
        unr = 0
        for score in entry["scores"]:
            if score == 1:
                syns += 1
            elif score == 0:
                ants += 1
            else: 
                unr += 1
        tot += entry["avg_score"]
        tot_syns += syns
        tot_ants += ants
        tot_unr += unr
        print(f"{entry["name"]}:") 
        print(f"{syns} synonyms, {ants} antonyms, {unr} unrelated")
        print(f"average score: {entry["avg_score"]}:") 
        print(f"accuracy: {(syns - unr) / len(entry["scores"])}:") 
        lens += len(entry["scores"])
    print(f"Overall:") 
    print(f"{tot_syns} synonyms, {tot_ants} antonyms, {tot_unr} unrelated")
    print(f"average score: {tot/10}:")
    print(f"accuracy: {(tot_syns - tot_unr)/lens}")    
    print()    