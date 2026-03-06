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
        self.log = Log("Recorder", Log.DEBUG)

        self.active_event = threading.Event()

        self.wake = WakeEngine(model_path, config)
        self.vad = VADEngine(config)

        self.stt = stt

        self.audio_buffer = deque(maxlen=int(self.cfg.sr * self.cfg.window_sec))
        self.pre_roll = deque(maxlen=int(self.cfg.sr * self.cfg.pre_roll_sec))

        self.recording = False
        self.command_queue = Queue()

        self.output_queue = None
        self.prompt_queue = None

        self.mode = RecordingMode.IDLE
        self.wake_detected = threading.Event()

        threading.Thread(
            target=self._transcriber_worker,
            daemon=True
        ).start()

        self.timeout_event = self.vad.timeout_event
        self.finished_recording_event = threading.Event()

    # ----------------------------------------------------------

    def _audio_callback(self, indata, frames, time_info, status):

        if status:
            self.log.warn(status)

        if not self.active_event.is_set():
            self.reset()
            return
        
        if self.Assistant.current_state == AssistantState.SPEAKING:
            self.log.debug("Currently speaking, ignoring audio input.")
            return

        chunk = indata[:, 0].copy()

        self.audio_buffer.extend(chunk)
        self.pre_roll.extend(chunk)

        if self.mode == RecordingMode.WAKE:
            if self.wake.detect(self.audio_buffer):
                self.wake_detected.set()
                self.active_event.clear()
            return


        if not self.recording:
            if self.wake.detect(self.audio_buffer) or self.mode == RecordingMode.DIRECT:
                self.Assistant.start_state(AssistantState.LISTENING)
                self._start_recording()

        else:
            finished, audio = self.vad.process(chunk)
            if finished:
                self.Assistant.end_state(AssistantState.LISTENING)

                if audio is None:
                    self.log.info("No speech detected, discarding.")
                    self.reset()
                else:
                    self.recording = False
                    self.command_queue.put(audio)
                    self.active_event.clear()

                self.finished_recording_event.set()

    # ----------------------------------------------------------

    def _start_recording(self):
        self.recording = True
        self.vad.recorded_audio = []
        self.vad.total_recorded = 0
        self.vad.silence_counter = 0

    def reset(self):
        self.log.debug("Resetting recorder states.")
        self.active_event.clear()
        self.wake_detected.clear()
        self.mode = RecordingMode.IDLE
        self.vad.recorded_audio = []
        self.vad.total_recorded = 0
        self.vad.silence_counter = 0

    def detect_wake(self):
        self.log.info("Waiting for wake word...")
        self.reset()
        self.mode = RecordingMode.WAKE
        self.active_event.set()
        t = self.wake_detected.wait()
        self.reset()
        return t
    
    def set_timeout(self, timeout_sec):
        self.vad.set_timeout(timeout_sec)

    # ----------------------------------------------------------
    def _transcriber_worker(self):
        self.log.info("Transcriber started")

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
                self.log.error("Transcription error:", e)
                continue

            if self.output_queue:
                self.output_queue.put(text)

            self.log.info("User:", text)

    # ----------------------------------------------------------
    
    def start(self, output_queue: Queue, prompt_queue: Queue):
        self.output_queue = output_queue
        self.prompt_queue = prompt_queue

        self.log.info("Listening...")

        with sd.InputStream(
            samplerate=self.cfg.sr,
            channels=1,
            blocksize=int(self.cfg.sr * self.cfg.hop_sec),
            dtype="float32",
            callback=self._audio_callback,
            device="pipewire"
        ):
            while True:
                time.sleep(0.1)

# ==========================================================
# MODE
# ==========================================================

class RecordingMode(Enum):
    WAKE = 1
    IDLE = 2
    DIRECT = 3
