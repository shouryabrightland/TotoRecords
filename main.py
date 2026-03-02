import json
import re
import csv

from AssistentCore import AssistantState,AssistantCore
Assistant = AssistantCore(AssistantState.LOADING)


from modules.Logging import Log
from modules.fuzzy import fuzzy
from Server.serve import serve,Request,Response

DATA_DIR = "data"

log = Log("Request Handler").log
fz = fuzzy()


def server(req:Request, res:Response):

    #get the class file
    classname = ask_for_class_file(req,res)
    #load class file

    StudentList = loadClassFile(classname)
    NameList = list(StudentList.keys())
    #we got students list
    while True:
        studentname = ask_for_student(req,res,NameList)

        StudentInfo = StudentList[studentname]
        if "yes" in req.input_no_wait("Do u want me to speak out loud?","yes no"):
            print(" ".join(tokenize(str(StudentInfo))))
            res.send(",".join(tokenize(str(StudentInfo))))
        req.input("call me and say next, whe you done.")
        
    res.exit()

def ask_for_student(req:Request,res:Response,NameList:list[str]):
    while True:
        rawName = req.input_no_wait("What is Your Name?"," ".join(NameList))
        fuzzy_result = fz.fuzzy_match(rawName,NameList)
        if fuzzy_result[0][1] == 1.0 or "yes" in req.input_no_wait("Do you mean "+fuzzy_result[0][0]+"? (yes or no)?","yes no").lower():
            return fuzzy_result[0][0]


def ask_for_class_file(req:Request,res:Response):
    '''takes class name from user'''
    while True:
        inp = req.input_no_wait("Confirm your class, Please?","class").lower()
        tokens = tokenize(inp)
        log(tokens)
        try:
            index = tokens.index("class")
        except ValueError:
            res.send("Inproper reply. [Hint: Say 'class 9, class 10']")
            continue
        
        #got index of "class"
        classname = " ".join(tokens[index+1:])
        check_list = fz.fuzzy_file_match(classname+".csv",DATA_DIR)
        if check_list[0][1] == 1.0 or "yes" in req.input_no_wait("Do you mean "+check_list[0][0]+"? (yes or no)?","yes no").lower():
            return DATA_DIR+"/"+check_list[0][0]

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

