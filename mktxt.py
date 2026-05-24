with open("problem_councils.txt") as f:
    i = 0
    for line in f:
        i += 1
        if i < 3:       continue
        with open(line.replace(".json", ".txt"), "w") as f2:
            f2.write("")
        print(f"made file for {line}")
        
