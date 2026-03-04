from AssistentCore import AssistantCore, AssistantState
from modules.AudioEngine import AudioEngine
from modules.Logging import Log
from modules.tts.main import TTS
print("Loading Assistant...")
from modules.stt.main import STT
from types import FunctionType
from queue import Queue
import threading
import Server.Recorder as Recorder

class serve:
    def __init__(self,server: FunctionType,Assistant:AssistantCore):
        
        Audio = AudioEngine(16000,Assistant=Assistant)

        Assistant.start_state(AssistantState.LOADING)
        tts = TTS("voices/en_US-lessac-low.onnx",Audio,Assistant)
        self.log = Log("Server").log
        self.log("Loading Services...")
        stt = STT("base.en")
        Res = Response(tts,Audio)
        recorder = Recorder.Recorder("models/toto_v2.onnx",stt=stt,Assistant=Assistant)
        Req = Request(tts=tts,audio=Audio,recorder=recorder,Assistant=Assistant)
        Req.queue = Queue()
        threading.Thread(target=recorder.start, daemon=True, args=(Req.queue,Req.Promptqueue,)).start()
        tts.enqueue("Welcome from Toto Assistent!")
        Assistant.end_state(AssistantState.LOADING)
        while not Res.isTerminated:
            Req.start()
            server(Req,Res)
            Res.end() 



class Request:
    def __init__(self,tts:TTS,audio:AudioEngine,recorder:Recorder.Recorder,Assistant:AssistantCore):
        self.tts = tts
        self.audio = audio
        self.log = Log("Server REQ").log
        self.queue = Queue()
        self.recorder = recorder
        self.Assistant = Assistant
        self.payload = None
        self.Promptqueue = Queue()
        self.needforceWake = False

        self.Assistant.on_state_change(self.on_assistant_state_change)
    
    def input(self,question:str,prompt=""):
        self.recorder.active_event.set()
        self.tts.enqueue(question)
        print(question)
        self.Promptqueue.put(prompt)
        val = self.queue.get().strip()
        self.recorder.active_event.clear()
        return val.lower()
    
    def input_no_wait(self,question:str,prompt=""):
        self.force_wake()
        return self.input(question,prompt)
    
    
    def on_assistant_state_change(self,state:AssistantState,is_start:bool):
        if self.Assistant.current_state == AssistantState.IDLE and self.needforceWake and not is_start:
            self.recorder.force_wake.set()
            self.needforceWake = False
            
    
    def force_wake(self):
        self.needforceWake = True
    

    def start(self):
        pass






class Response:
    def __init__(self,tts:TTS,speaker:AudioEngine):
        self.isTerminated = False
        self.current_expectation = None
        self.tts = tts
        self.speaker = speaker
        self.payload = {}
        self.log = Log("Server RES").log
        self.stopflag = threading.Event()

    def send(self,message):
        self.tts.enqueue(message)
    
    def end(self):
        self.speaker.stop_bg()
        self.log("waiting for tts to shut it's mouth")
        self.tts.q.join() #wait for tts to complete..
        self.log("waiting for speaker to shut it's mouth")
        self.speaker.q.join() #wait for speaker 
        self.stopflag.set()
        return self
    
    def exit(self):
        self.end()
        self.isTerminated = True
    
    def exit_no_wait(self):
        self.isTerminated = True
