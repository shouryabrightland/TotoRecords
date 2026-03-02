import re
import csv
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = "data"

def tokenize(text:str):
    '''tokenise the text r"\\b\w+\\b"'''
    return re.findall(r"\b\w+\b",text)

def similarity(a, b):
    '''returns score of match'''
    return SequenceMatcher(None, a, b).ratio()

def fuzzy_file_check(target_filename, directory="."):
    '''returns file list with match score'''
    directory = Path(directory)
    files = [f.name for f in directory.iterdir() if f.is_file()]
    
    results = []
    for f in files:
        score = similarity(target_filename, f)
        results.append((f, score))
    
    # sort by highest similarity
    results.sort(key=lambda x: x[1], reverse=True)
    return results



def getclassfile():
    '''takes class name from user'''
    while True:
        inp = input("Confirm your class, Please?")
        tokens = tokenize(inp)
        print(tokens)
        try:
            index = tokens.index("class")
        except ValueError:
            print("Inproper reply. [Hint: Say 'class 9, class 10']")
            continue
        
        #got index of "class"
        classname = " ".join(tokens[index+1:])
        check_list = fuzzy_file_check(classname+".csv",DATA_DIR)
        if check_list[0][1] == 1.0 or "yes" in input("Do you mean "+check_list[0][0]+"? (yes / no)"):
            return DATA_DIR+"/"+check_list[0][0]
        else:
            continue

def processClassFile(filepath):
    '''gives dict from csv'''
    students = {}
    with open(filepath, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            name = row[0]
            
            student_data = {}
            for key, value in zip(header[1:], row[1:]):
                if key != "Grade":
                    student_data[key] = int(value)
                else:
                    student_data[key] = value
            
            students[name] = student_data
    return students

print(processClassFile(DATA_DIR+"/12.csv"))




