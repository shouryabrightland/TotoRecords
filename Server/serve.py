from AssistentCore import AssistantCore, AssistantState
from modules.AudioEngine import AudioEngine
from modules.Logging import Log
from modules.tts.main import TTS
from modules.stt.main import STT
from types import FunctionType
from queue import Queue
import threading
import Server.Recorder as Recorder
import screen as gui
print("Modules imported, starting server...")

def ServerRuntime(server: FunctionType,Assistant:AssistantCore):
        
        log = Log("Server")

        log.info("Loading Services...")
        Audio = AudioEngine(16000,Assistant=Assistant)
        Assistant.start_state(AssistantState.LOADING)
        tts = TTS("voices/en_US-lessac-low.onnx",Audio,Assistant)
        stt = STT("base.en")
        Res = Response(tts,Audio)
        recorder = Recorder.Recorder("models/toto_v2.onnx",stt=stt,Assistant=Assistant)
        Req = Request(tts=tts,audio=Audio,recorder=recorder,Assistant=Assistant)
        threading.Thread(target=recorder.start, daemon=True, args=(Req.queue,Req.Promptqueue,)).start()
        tts.enqueue("Welcome from Toto Assistent!")
        Assistant.end_state(AssistantState.LOADING)

        while not Res.isTerminated:
            server(Req,Res)
            Res.end() 



class Request:
    def __init__(self,tts:TTS,audio:AudioEngine,recorder:Recorder.Recorder,Assistant:AssistantCore,vad_timeout_sec=None,gui:gui=None):
        self.tts = tts
        self.audio = audio
        self.log = Log("Server REQ")
        self.queue = Queue()
        self.recorder = recorder
        self.Assistant = Assistant
        self.payload = None
        self.Promptqueue = Queue()
        self.needforceWake = False
        self.gui = gui

        self.default_vad_timeout = vad_timeout_sec

        self.Assistant.on_state_change(self.on_assistant_state_change)
    
    def input(self,question:str,prompt="",timeout=None,update_gui=True):
        self.tts.enqueue(question)
        self.recorder.set_timeout(timeout or self.default_vad_timeout)
        self.recorder.active_event.set()
        print(question)
        if update_gui:
            self.gui.set_message(question)
        self.Promptqueue.put(prompt)
        #wait for recording to finish or timeout
        self.recorder.finished_recording_event.wait()
        self.recorder.finished_recording_event.clear()

        self.log.info("Received recording, now waiting for processing...")
        if self.recorder.timeout_event.is_set():
            self.recorder.timeout_event.clear()
            raise TimeoutError("Recording timed out")
        else:
            val = self.queue.get().strip()

        self.check_exit(val)
        self.recorder.active_event.clear()
        self.recorder.set_timeout(self.default_vad_timeout) #reset timeout after use
        return val.lower()
    
    def input_direct(self,question:str,prompt="",timeout=None,update_gui=True):
        self._force_wake()
        return self.input(question,prompt,timeout=timeout,update_gui=update_gui)
    
    
    def detect_call(self):
        return self.recorder.detect_wake()
    
    
    def on_assistant_state_change(self,state:AssistantState,is_start:bool):
        if self.Assistant.current_state == AssistantState.IDLE and self.needforceWake and not is_start:
            self.recorder.mode = Recorder.RecordingMode.DIRECT
            self.needforceWake = False
            
    
    def _force_wake(self):
        self.needforceWake = True
    
    def check_exit(self,val:str):
        if val in ["exit","quit","close"]:
            raise KeyboardInterrupt("Exit command received")






class Response:
    def __init__(self,tts:TTS,speaker:AudioEngine):
        self.isTerminated = False
        self.current_expectation = None
        self.tts = tts
        self.speaker = speaker
        self.payload = {}
        self.log = Log("Server RES")
        self.stopflag = threading.Event()
        self.gui = None

    def send(self,message,update_gui=True):
        self.tts.enqueue(message)
        if update_gui:
            self.gui.set_message(message)
    
    def end(self):
        self.log.debug("Ending response, stopping TTS and Speaker...")
        self.speaker.stop_bg()
        self.log.debug("waiting for tts to shut it's mouth")
        self.tts.q.join() #wait for tts to complete..
        self.log.debug("waiting for speaker to shut it's mouth")
        self.speaker.q.join() #wait for speaker 
        self.stopflag.set()
        return self
    
    def exit(self):
        self.end()
        self.isTerminated = True
    
    def exit_no_wait(self):
        self.isTerminated = True
