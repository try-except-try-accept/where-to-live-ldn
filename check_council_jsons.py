from os import listdir
import json

problems = []

for fn in listdir():
    if fn.endswith("json"):
        if not "London" in fn:  continue
        with open(fn) as f:
            data = json.load(f)
        print(f"===\n{fn}\n===")
        print(data.keys())

        if input("ok") != "":
            problems.append(fn)
        
with open("problem_councils.txt", "w") as f:
    for p in problems:
        p = p.replace("_London_Borough_Council_Election.json", "")
        f.write(p+"\n")