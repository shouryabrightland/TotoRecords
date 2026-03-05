import threading
import queue
import sounddevice as sd
import soundfile as sf
import numpy as np
from AssistentCore import AssistantState
from modules.Logging import Log 

class AudioEngine:
    def __init__(self, samplerate=16000, blocksize=1024,Assistant=None):
        self.SR = samplerate
        self.BLOCK = blocksize
        self.Assistant = Assistant
        self.log = Log("Audio Engine")

        self.q = queue.Queue()
        self.running = True

        # Thread-safe stop signal for background audio
        self.bg_stop_event = threading.Event()

        self.bgAllow = True

        # Output stream
        self.stream = sd.OutputStream(
            samplerate=self.SR,
            channels=1,
            dtype="float32",
            blocksize=self.BLOCK,
            device="pipewire"
        )
        self.stream.start()

        # Worker thread
        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self.thread.start()
        self.log.info("Started")
        self.Assistant.on_state_change(self.AudioUXUpdate)

        self.NoBGlist = [AssistantState.LISTENING,AssistantState.SPEAKING]
        self.NoSoundlist = [AssistantState.LISTENING]

    # ─────────────────────────────
    # PUBLIC API
    # ─────────────────────────────

    def play_bg_file(self, file_path, volume=0.4):
        """Looping background sound (e.g. for thinking music)"""
        if self.Assistant.current_state in self.NoBGlist:
            self.log.warn("Currently in state that blocks BG play",self.Assistant.current_state,file_path)
            return
        self.log.info("putting Query bg file",file_path)
        self.q.put(("bg", file_path, volume))

    def play_file(self, file_path, volume=1.0):
        """Foreground sound (e.g. for effects)"""
        self.log.info("putting Query file",file_path)
        self.q.put(("afx", file_path, volume))

    # def play_samples(self, samples: np.ndarray):
    #     """Raw samples playback (preempts BG)"""
    #     self.log.info("putting Samples Query",samples.shape)
    #     self.q.put(("samples", samples, None))

    def speak(self, samples: np.ndarray):
        """Raw samples playback (preempts BG)"""

        if self.Assistant.current_state in self.NoSoundlist:
            self.log.info("Currently in state that blocks speaking",self.Assistant.current_state)
            return

        if samples is None:
            self.log.info("putting End of Speech")
            self.q.put(("tts", None, None))
            return
            
        self.log.info("putting Samples to Speak",samples.shape)
        self.q.put(("tts", samples, None))


    def stop_bg(self):
        """Stop background audio immediately"""
        self.log.info("BG stop flag setted")
        self.bg_stop_event.set()

    def shutdown(self):
        """Clean shutdown"""
        self.log.info("Shuting Down...")
        self.running = False
        self.bg_stop_event.set()
        self.q.put(("exit", None, None))

    # ─────────────────────────────
    # WORKER LOOP
    # ─────────────────────────────

    def _run(self):
        while self.running:
            job, a, b = self.q.get()

            if job == "exit":
                break

            if job == "bg" and self.Assistant.current_state not in self.NoBGlist:
                self._play_bg_loop(a, b)

            elif job == "afx":
                self._play_file(a, b)

            elif job == "tts":
                self._speak(a)

            self.q.task_done()

        self.stream.stop()
        self.stream.close()

    # ─────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────

    def _play_bg_loop(self, file_path, volume):
        self.log.info("Playing BG loop",file_path)
        data, sr = sf.read(file_path, dtype="float32")

        if data.ndim > 1:
            data = data.mean(axis=1)

        if sr != self.SR:
            data = self._resample(data, sr)

        data *= volume
        length = len(data)

        self.bg_stop_event.clear()

        while not self.bg_stop_event.is_set():
            for i in range(0, length, self.BLOCK):
                
                if self.bg_stop_event.is_set():
                    return
                self.stream.write(data[i:i + self.BLOCK])

    def _play_file(self, file_path, volume):
        self.log.info("Playing file", file_path)
        self.bg_stop_event.set()

        data, sr = sf.read(file_path, dtype="float32")

        if data.ndim > 1:
            data = data.mean(axis=1)

        if sr != self.SR:
            data = self._resample(data, sr)

        self.stream.write(data * volume)

    # def _play_samples(self, samples):
    #     self.log.info("Playing Samples")
    #     self.bg_stop_event.set()
    #     #print(self.bg_stop_event.is_set(),"o")
    #     if samples.ndim > 1:
    #         samples = samples.mean(axis=1)

    #     self.stream.write(samples.astype(np.float32))

    def _speak(self, samples):
        if self.Assistant.current_state != AssistantState.SPEAKING:
            self.log.warn("Not in SPEAKING state, starting it. Set in speaking state to speak")
            return
        
        if samples is None:
            self.log.info("End of TTS stream")
            self.Assistant.end_state(AssistantState.SPEAKING)
            return

        self.log.info("Speaking Samples")
        self.bg_stop_event.set()
        #print(self.bg_stop_event.is_set(),"o")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        self.stream.write(samples.astype(np.float32))

    def _resample(self, data, sr):
        self.log.warn("ReSampling")
        ratio = self.SR / sr
        x_old = np.arange(len(data))
        x_new = np.linspace(0, len(data) - 1, int(len(data) * ratio))
        return np.interp(x_new, x_old, data).astype(np.float32)
    
    def AudioUXUpdate(self,state:AssistantState,is_start:bool):
        if state == AssistantState.LISTENING:
            if is_start:
                self.play_file("effects/recordingstart.mp3", volume=1)
            else:
                self.play_file("effects/recordingend.mp3", volume=1)
        elif state == AssistantState.THINKING:
            if is_start:
                self.play_bg_file("effects/think.mp3", volume=0.5)
            else:
                self.stop_bg()


