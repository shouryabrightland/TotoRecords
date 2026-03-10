# ================= IMPORTS =================

from _csv import _reader
from io import Reader
import json
import re
import csv
from typing import Any, Literal, LiteralString

from AssistentCore import AssistantState, AssistantCore
from modules.Logging import Log
from modules.fuzzy import fuzzy
from Server.serve import Request, Response, ServerRuntime

import screen as gui


# ================= INITIALIZATION =================

Assistant = AssistantCore(AssistantState.LOADING)

DATA_DIR = "data"
FUZZY_THRESHOLD = 0.9

log = Log("Request Handler (main.py)")
fz = fuzzy()


# ================= TEXT UTILITIES =================

def tokenize(text: str)  -> list[Any]:
    return re.findall(r"\b\w+\b", text)


# ================= CSV DATA =================

def loadClassFile(filepath):# -> dict:

    students = {}

    with open(filepath, "r", newline="", encoding="utf-8") as file:

        reader: Reader = csv.reader(file)
        header = next(reader)

        for row in reader:

            name = row[0]
            student_data = {}

            for key, value in zip(header[1:], row[1:]):
                student_data[key] = value

            students[name] = student_data

    return students


# ================= USER CONFIRMATION =================

def confirm(req: Request, question: str,
            options: list[str] = ["yes", "no"],
            timeout=None,
            update_gui=True):

    answer = req.input_direct(
        question + " (yes or no)",
        timeout=timeout,
        update_gui=update_gui
    )

    return fz.fuzzy_match_basic(answer, options)[0][0]


# ================= STUDENT MATCHING =================

def ask_for_student(req: Request, res: Response, NameList: list[str]):

    while True:

        rawName = req.input_direct(
            "What is Your Name?",
            ", ".join(NameList)
        )

        fuzzy_result = fz.fuzzy_match(rawName, NameList)

        if len(fuzzy_result) and (fuzzy_result[0][1] >= FUZZY_THRESHOLD or \
           confirm(req, f"Do you mean {fuzzy_result[0][0]}?") == "yes"):
            return fuzzy_result[0][0]
        else:
            spellname = req.input(
                "Could you give me the spelling of your last name?",
                ", ".join(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            )

            spellname = "".join(
                re.findall(r"\b[A-Za-z]{1}\b", spellname)
            )

            fuzzy_result = fz.fuzzy_match(spellname, NameList)

            if len(fuzzy_result) and (fuzzy_result[0][1] >= FUZZY_THRESHOLD or \
               confirm(req, f"Do you mean {fuzzy_result[0][0]}?") == "yes"):

                return fuzzy_result[0][0]

            else:
                res.send("Sorry, I couldn't find your name.")
                return False


# ================= CLASS FILE HANDLING =================

def get_class(text: str) -> LiteralString | Literal[False]:

    tokens = tokenize(text)

    try:
        index = tokens.index("class")
    except ValueError:
        return False

    return " ".join(tokens[index+1:])


def ask_for_class_file(req: Request, res: Response, classname=None):

    while True:

        if not classname:

            inp = req.input_direct(
                "Confirm your class Please?",
                ", ".join([f"class {i}" for i in range(1, 13)])
            ).lower()

            classname = get_class(inp)

            if not classname:
                res.send("Improper reply. [Hint: Say 'class 9']")
                continue
############################################################################################################
        check_list = fz.fuzzy_file_match(classname + ".csv", DATA_DIR)

        if len(check_list) and (check_list[0][1] >= FUZZY_THRESHOLD or \
           confirm(req, f"Do you mean {check_list[0][0].split('.',1)[0]}?") == "yes"):

            return DATA_DIR + "/" + check_list[0][0]
        else:
            res.send("Provide")

        classname = None


# ================= TTS FORMATTER =================

def dict_to_tts(data: dict) -> str:

    subjects = []
    metadata = []

    for key, value in data.items():

        spoken_key = key.replace("_", " ")
        spoken_key = re.sub(r"([a-z])([A-Z])", r"\1 \2", spoken_key)
        spoken_key = spoken_key.title()

        if isinstance(value, str):
            value = value.replace("+", " plus").replace("-", " minus")

        if key.lower() in {"total","grade","percentage","result"}:
            metadata.append(f"The {spoken_key} is {value}.")
        else:
            subjects.append(f"{spoken_key} {value}")

    parts = []

    if subjects:
        parts.append("The marks are as follows.")
        parts.append(", ".join(subjects) + ".")

    parts.extend(metadata)

    return " ".join(parts)


# ================= REPORT TABLE =================

def format_report_table(data: dict):

    rows = [(k.replace("_"," ").title(), str(v)) for k,v in data.items()]

    key_w = max(len(k) for k,_ in rows)
    val_w = max(len(v) for _,v in rows)

    def line(l,m,r):
        return l + "─"*(key_w+2) + m + "─"*(val_w+2) + r

    out = []

    out.append(line("┌","┬","┐"))
    out.append(f"│ {'REPORT CARD'.center(key_w+val_w+3)} │")
    out.append(line("├","┬","┤"))

    for k,v in rows:
        out.append(f"│ {k:<{key_w}} │ {v:>{val_w}} │")

    out.append(line("└","┴","┘"))

    return "\n".join(out)


# ================= GUI STATE HANDLER =================

def onStateGUI(state, is_start):

    if gui.state["screen"] != "report":

        if state == AssistantState.SPEAKING and not is_start:
            if gui.state["screen"] == "message":
                gui.show_eyes()

        if state == AssistantState.THINKING and is_start:
            if gui.state["screen"] == "eyes":
                gui.set_emotion(gui.Emotion.CURIOUS)

        elif state == AssistantState.THINKING and not is_start:
            if gui.state["screen"] == "eyes":
                gui.set_emotion(gui.Emotion.NORMAL)


# ================= MAIN SERVER =================

def server(req: Request, res: Response):

    req.default_vad_timeout = 15

    gui.start_gui()
    res.gui = req.gui = gui

    Assistant.on_state_change(onStateGUI)

    log.info("Server ready.")

    while req.detect_call():

        gui.show_eyes()

        try:

            classname = "data/12.csv"

            StudentList = loadClassFile(classname)
            NameList = [x.lower() for x in StudentList.keys()]

            studentname = ask_for_student(req, res, NameList)

            if studentname:

                StudentInfo = StudentList[studentname]

                gui.show_report(StudentInfo)

                table = format_report_table(StudentInfo)

                log.info(f"Generated report for {studentname}:\n{table}")

                print("\n"*2 + table + "\n"*2)

                if confirm(req,"Do you want me to speak it?") == "yes":
                    res.send(dict_to_tts(StudentInfo), update_gui=False)

        except TimeoutError:

            res.send("Recording timed out.", update_gui=False)
            print("\n[VAD] Timeout reached.\n")

        except KeyboardInterrupt:

            res.send("Goodbye!", update_gui=False)
            print("\n[System] Shutdown.\n")
            break


# ================= RUNTIME =================

ServerRuntime(server, Assistant)