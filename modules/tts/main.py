from AssistentCore import AssistantCore, AssistantState
from modules.AudioEngine import AudioEngine
from piper.voice import PiperVoice
import numpy as np
import threading
import queue
from modules.Logging import Log
import re


class TTS:
    def __init__(self, model_path, speaker: AudioEngine,Assistant:AssistantCore = None):
        self.log = Log("TTS").log

        if not isinstance(model_path, str):
            raise TypeError("model_path must be a string")
        
        self.log("loading PiperVoice Model",model_path)
        self.voice = PiperVoice.load(model_path)
        self.log("loaded model Successfully")

        syn = self.voice.config
        syn.length_scale = 1.2
        
        self.SR = speaker.SR
        self.speaker = speaker
        self.Assistant = Assistant

        # Queue and worker thread for non-blocking TTS
        self.q = queue.Queue()
        self.running = True
        #self.speaking = False  # Indicates if currently speaking
        
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()


    # ---------------------------
    # Public API
    # ---------------------------
    def enqueue(self, text: str,slow = None):
        """Add text to TTS queue for non-blocking speech"""
        self.log("Putting Query")
        self.q.put((text,slow))

    def stop(self):
        """Stop current speaking"""
        self.log("Stoping BG music")
        self.speaker.stop_bg()  # Stop background or current playback
        #self.speaking = False

    def shutdown(self):
        """Stop the TTS worker"""
        self.log("Shuting Down")
        self.running = False
        self.q.put(None)

    # ---------------------------
    # Internal worker
    # ---------------------------
    def _worker(self):
        
        while self.running:
            text, slow = self.q.get()
            syn = self.voice.config
            if slow:
                syn.length_scale = 1.8  # ~10–15% slower
            else:
                syn.length_scale = 1.2

            self.Assistant.start_state(AssistantState.SPEAKING)
            for samples in self.synthesize_stream(text):
                self.speaker.play_samples(samples)
            self.Assistant.end_state(AssistantState.SPEAKING)
            self.q.task_done()

    # ---------------------------
    # Streaming synthesis
    # ---------------------------

    def synthesize_stream(self, text, syn_config=None):
        text = self.remove_emoji(text)
        self.log("Synthesizing text:",text)
        for chunk in self.voice.synthesize(text, syn_config=syn_config):
            samples = chunk.audio_float_array
            if samples is not None:
                yield np.asarray(samples, dtype=np.float32)
    
    def remove_emoji(self, text):
        # More comprehensive emoji removal
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)