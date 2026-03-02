import time
import threading
from enum import Enum
from collections import deque
from queue import Queue, Empty
import sounddevice as sd
from AssistentCore import AssistantCore, AssistantState
from modules.Logging import Log
from modules.audio.recoderConfig import RecorderConfig
from modules.audio.vadEngine import VADEngine
from modules.audio.wakeEngine import WakeEngine
from modules.stt.main import STT

class Recorder:

    def __init__(
        self,
        model_path: str,
        stt: STT,
        Assistant: AssistantCore,
        config: RecorderConfig = RecorderConfig(),
    ):
        self.Assistant = Assistant
        self.cfg = config
        self.log = Log("Recorder").log

        self.active_event = threading.Event()
        self.force_wake = threading.Event()

        self.wake = WakeEngine(model_path, config)
        self.vad = VADEngine(config)

        self.stt = stt

        self.audio_buffer = deque(maxlen=int(self.cfg.sr * self.cfg.window_sec))
        self.pre_roll = deque(maxlen=int(self.cfg.sr * self.cfg.pre_roll_sec))

        self.recording = False
        self.command_queue = Queue()

        self.output_queue = None
        self.prompt_queue = None

        threading.Thread(
            target=self._transcriber_worker,
            daemon=True
        ).start()

    # ----------------------------------------------------------

    def _audio_callback(self, indata, frames, time_info, status):

        if status:
            self.log(status)

        if not self.active_event.is_set():
            return

        chunk = indata[:, 0].copy()

        self.audio_buffer.extend(chunk)
        self.pre_roll.extend(chunk)

        if not self.recording:
            if self.wake.detect(self.audio_buffer) or self.force_wake.is_set():
                self.Assistant.start_state(AssistantState.LISTENING)
                self._start_recording()

        else:
            finished, audio = self.vad.process(chunk)
            if finished:
                self.recording = False
                self.command_queue.put(audio)
                self.active_event.clear()
                self.force_wake.clear()
                self.Assistant.end_state(AssistantState.LISTENING)

    # ----------------------------------------------------------

    def _start_recording(self):
        self.recording = True
        self.vad.recorded_audio = list(self.pre_roll)
        self.vad.total_recorded = len(self.pre_roll)
        self.vad.silence_counter = 0

    # ----------------------------------------------------------
    def _transcriber_worker(self):
        self.log("Transcriber started")

        while True:
            audio = self.command_queue.get()
            if audio is None:
                continue
            try:
                try:
                    prompt = self.prompt_queue.get_nowait()
                    self.Assistant.start_state(AssistantState.THINKING)
                    text = self.stt.transcribe(audio, prompt)
                except Empty:
                    text = self.stt.transcribe(audio)
                
                finally:
                    self.Assistant.end_state(AssistantState.THINKING)

            except Exception as e:
                self.log("Transcription error:", e)
                continue

            if self.output_queue:
                self.output_queue.put(text)

            self.log("User:", text)

    # ----------------------------------------------------------
    
    def start(self, output_queue: Queue, prompt_queue: Queue):
        self.output_queue = output_queue
        self.prompt_queue = prompt_queue

        threading.Thread(
            target=self._transcriber_worker,
            daemon=True
        ).start()

        self.log("Listening...")

        with sd.InputStream(
            samplerate=self.cfg.sr,
            channels=1,
            blocksize=int(self.cfg.sr * self.cfg.hop_sec),
            dtype="float32",
            callback=self._audio_callback,
        ):
            while True:
                time.sleep(0.1)

# ==========================================================
# MODE
# ==========================================================

class RecordingMode(Enum):
    WAKE = 1
    DIRECT = 2