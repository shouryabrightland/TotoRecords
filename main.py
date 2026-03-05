import json
import re
import csv
from AssistentCore import AssistantState,AssistantCore
Assistant = AssistantCore(AssistantState.LOADING)


from modules.Logging import Log
from modules.fuzzy import fuzzy

from Server.serve import serve,Request,Response

DATA_DIR = "data"

log = Log("Request Handler (main.py)")
fz = fuzzy()
fz_threshold = 0.9

def server(req:Request, res:Response):

    #get the class file
    classname = ask_for_class_file(req,res)
    #classname = "data/12.csv"
    #load class file

    StudentList = loadClassFile(classname)
    NameList = list(StudentList.keys())
    #we got students list

    inp = None

    while True:
        studentname = ask_for_student(req,res,NameList,inp=inp)
        if studentname:
            StudentInfo = StudentList[studentname]
            print(" ".join(tokenize(str(StudentInfo))))
            if "yes" in req.input_no_wait("Do u want me to speak out loud?","yes no"):
                res.send(",".join(tokenize(str(StudentInfo))))
            inp = req.input("call me and say another name or class, when you done.")

        else:
            inp = req.input("call me and say another name or class to continue.")

        classname = get_class(inp)
        if classname:
            classname = ask_for_class_file(req,res,classname)
            res.send("okey, feching "+classname)
            StudentList = loadClassFile(classname)
            NameList = list(StudentList.keys())
            inp = None
        

        
    res.exit()

def ask_for_student(req:Request,res:Response,NameList:list[str],inp:str=None):
    while True:

        if inp:
            rawName = inp
        else:
            rawName = req.input_no_wait("What is Your Name?"," ".join(NameList))

        fuzzy_result = fz.fuzzy_match(rawName,NameList)

        if fuzzy_result[0][1] >= fz_threshold or "yes" in req.input_no_wait("Do you mean "+fuzzy_result[0][0]+"? (yes or no)?","yes no").lower():
            return fuzzy_result[0][0]
        
        else:
            spellname = req.input("Spell your name please",", ".join(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
            spellname = "".join(re.findall(r"\b[A-Za-z]{1}\b", spellname))
            fuzzy_result = fz.fuzzy_match(spellname,NameList)

            if fuzzy_result[0][1] >= fz_threshold or "yes" in req.input_no_wait("Do you mean "+fuzzy_result[0][0]+"? (yes or no)?","yes no").lower():
                return fuzzy_result[0][0]
            
            else:
                res.send("Sorry, I couldn't find your name.")
                return False

def get_class(text:str):
    '''check if user has mentioned class in text'''
    tokens = tokenize(text)
    try:
        index = tokens.index("class")
    except ValueError:
        return False
    return " ".join(tokens[index+1:])

def ask_for_class_file(req:Request,res:Response,classname:str=None):
    '''takes class name from user'''
    while True:
        if not classname:
            inp = req.input_no_wait("Confirm your class, Please?","class").lower()
            classname = get_class(inp)
            if not classname:
                res.send("Inproper reply. [Hint: Say 'class 9, class 10']")
                continue     
        check_list = fz.fuzzy_file_match(classname+".csv",DATA_DIR)
        if check_list[0][1] >= fz_threshold or "yes" in req.input_no_wait("Do you mean "+check_list[0][0]+"? (yes or no)?","yes no").lower():
            return DATA_DIR+"/"+check_list[0][0]
        classname = None

def loadClassFile(filepath):
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
    



def tokenize(text:str):
    '''tokenise the text'''
    return re.findall(r"\b\w+\b",text)


    

serve(server,Assistant)

