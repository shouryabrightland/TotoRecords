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
    #config
    req.default_vad_timeout = 10  # Set default VAD timeout to 10 seconds
    log.info("Server is ready to handle requests.")
    while req.detect_call():
        print("restarting request loop")
        try:

            #get the class file
            classname = ask_for_class_file(req,res)
            #classname = "data/12.csv"
            #load class file

            StudentList = loadClassFile(classname)
            NameList = list(StudentList.keys())
            #we got students list

            studentname = ask_for_student(req,res,NameList)
            if studentname:
                StudentInfo = StudentList[studentname]
                table = format_report_table(StudentInfo)
                log.info(f"Generated report for {studentname}:\n{table}")
                print("\n"*2+table,end="\n"*2)
                if "yes" == confirm(req,"Do u want me to speak out loud?"):
                    res.send(dict_to_tts(StudentInfo))
        except TimeoutError:
            res.send("Recording timed out.")
            print("\n[VAD] Timeout reached, no speech detected.\n")
        finally:
            res.send("Going back to sleep mode.")
            continue

def confirm(req:Request,question:str,options:list[str] = ["yes","no"],timeout=None):
        answer = req.input_no_wait(question+" (yes or no)",timeout=timeout)
        return fz.fuzzy_match(answer,options)[0][0]


def ask_for_student(req:Request,res:Response,NameList:list[str]):
    while True:
        rawName = req.input_no_wait("What is Your Name?",", ".join(NameList))

        fuzzy_result = fz.fuzzy_match(rawName,NameList)

        if fuzzy_result[0][1] >= fz_threshold or "yes" == confirm(req,"Do you mean "+fuzzy_result[0][0]+"?"):
            return fuzzy_result[0][0]
        
        else:
            spellname = req.input("Could you give me the spelling of your last name?",", ".join(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
            spellname = "".join(re.findall(r"\b[A-Za-z]{1}\b", spellname))
            fuzzy_result = fz.fuzzy_match(spellname,NameList)

            if fuzzy_result[0][1] >= fz_threshold or "yes" == confirm(req,"Do you mean "+fuzzy_result[0][0]+"?"):
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
            inp = req.input_no_wait("Confirm your class Please?",", ".join(["class "+str(i) for i in range(1,13)])).lower()
            classname = get_class(inp)
            if not classname:
                res.send("Inproper reply. [Hint: Say 'class 9, class 10']")
                continue
        check_list = fz.fuzzy_file_match(classname+".csv",DATA_DIR)
        if check_list[0][1] >= fz_threshold or "yes" == confirm(req,"Do you mean "+check_list[0][0].split(".",1)[0]+"?"):
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
                    student_data[key] = value
            students[name] = student_data
    return students
    
def tokenize(text:str):
    '''tokenise the text'''
    return re.findall(r"\b\w+\b",text)

def dict_to_tts(data: dict) -> str:

    subjects = []
    metadata = []

    for key, value in data.items():

        spoken_key = key.replace("_", " ")
        spoken_key = re.sub(r"([a-z])([A-Z])", r"\1 \2", spoken_key)
        spoken_key = spoken_key.title()

        if isinstance(value, str):
            value = value.replace("+", " plus").replace("-", " minus")

        if key.lower() in {"total", "grade", "percentage", "result"}:
            metadata.append(f"The {spoken_key} is {value}.")
        else:
            subjects.append(f"{spoken_key} {value}")

    parts = []

    if subjects:
        parts.append("The marks are as follows.")
        parts.append(", ".join(subjects) + ".")

    parts.extend(metadata)

    return " ".join(parts)


def format_report_table(data: dict, use_color=True) -> str:

    # ANSI colors
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    def color(text, c):
        return f"{c}{text}{RESET}" if use_color else text

    # normalize keys
    rows = [(k.replace("_", " ").title(), str(v)) for k, v in data.items()]

    summary_keys = {"total", "grade", "percentage", "result"}

    subjects = []
    summary = []

    for k, v in rows:
        if k.lower() in summary_keys:
            summary.append((k, v))
        else:
            subjects.append((k, v))

    # widths
    key_w = max(len(k) for k, _ in rows)
    val_w = max(len(v) for _, v in rows)

    def line(l, m, r):
        return l + "─" * (key_w + 2) + m + "─" * (val_w + 2) + r

    out = []

    # header
    out.append(line("┌", "┬", "┐"))

    title = "REPORT CARD"
    total_width = key_w + val_w + 5
    out.append(f"│ {color(title.center(total_width-2), CYAN)} │")

    out.append(line("├", "┬", "┤"))

    # subjects
    for k, v in subjects:
        out.append(
            f"│ {k:<{key_w}} │ {color(v, GREEN):>{val_w + (9 if use_color else 0)}} │"
        )

    # summary section
    if summary:
        out.append(line("├", "┼", "┤"))

        for k, v in summary:
            out.append(
                f"│ {color(k, YELLOW):<{key_w + (9 if use_color else 0)}} │ {v:>{val_w}} │"
            )

    out.append(line("└", "┴", "┘"))

    return "\n".join(out) 



serve(server,Assistant)

