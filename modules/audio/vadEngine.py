
from collections import deque
import threading

import numpy as np
import torch
from modules.Logging import Log
from modules.audio.recoderConfig import RecorderConfig


class VADEngine:
    def __init__(self, config: RecorderConfig):
        self.cfg = config
        self.log = Log("VADEngine", Log.DEBUG)

        self.vad_model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False
        )

        self.vad_model.eval()
        self.vad_model.reset_states()

        self.recorded_audio = []
        self.total_recorded = 0
        self.silence_counter = 0

        self.pre_buffer = deque(maxlen=int(self.cfg.sr * 0.5))
        self.recording = False

        self.frame_buffer = np.array([], dtype=np.float32)

        self.min_samples = int(self.cfg.sr * self.cfg.min_recording_sec)
        self.silence_samples = int(self.cfg.sr * self.cfg.vad_silence_sec)

        self.timeout_sec = None
        self.timeout_frames = None
        self.frame_count = 0

        self.timeout_event = threading.Event()

    def set_timeout(self, timeout_sec):
        self.timeout_sec = timeout_sec
        self.timeout_frames = int(self.timeout_sec * self.cfg.sr)


    def process(self, chunk):

        self.frame_buffer = np.concatenate((self.frame_buffer, chunk))
        self.frame_count += len(self.frame_buffer)

        while len(self.frame_buffer) >= self.cfg.vad_frame:

            frame = self.frame_buffer[:self.cfg.vad_frame]
            self.frame_buffer = self.frame_buffer[self.cfg.vad_frame:]

            speech_prob = self._run_silero(frame)

            print(f"\r[VAD] Speech Probability: {speech_prob:.4f}", end="")

            # ----------------------
            # NOT RECORDING
            # ----------------------
            if not self.recording:
                self.log.debug("Not recording. VAD prob:", speech_prob)
                # maintain rolling 0.5s buffer
                self.pre_buffer.extend(frame)

                if self.frame_count >= self.timeout_frames:
                    self.log.info("VAD timeout reached")
                    self.timeout_event.set()
                    self.frame_count = 0
                    return True, None

                if speech_prob > self.cfg.vad_threshold:

                    self.recording = True
                    self.log.info("Speech detected, starting recording")

                    # flush buffer into recording
                    self.recorded_audio.extend(self.pre_buffer)

                    # DO NOT count this in total_recorded
                    self.pre_buffer.clear()

                    self.recorded_audio.extend(frame)

                    self.total_recorded += len(frame)
                    self.silence_counter = 0

            # ----------------------
            # RECORDING
            # ----------------------
            else:

                if speech_prob > self.cfg.vad_threshold:

                    self.recorded_audio.extend(frame)
                    self.total_recorded += len(frame)

                    self.silence_counter = 0
                    self.log.debug("Speech detected. Total recorded samples:", self.total_recorded, self.total_recorded / self.cfg.sr, "sec")

                else:

                    self.silence_counter += len(frame)
                    self.log.debug("Silence detected. Silence counter:", self.silence_counter,self.silence_samples)

                    if self.silence_counter > self.silence_samples:

                        if self.total_recorded > self.min_samples:

                            audio = np.array(self.recorded_audio, dtype=np.float32)

                            self._reset()
                            self.frame_count = 0

                            self.log.info("Speech ended")

                            return True, audio

                        else:
                            if self.frame_count >= self.timeout_frames:
                                self.log.info("VAD timeout reached during recording")
                                self.timeout_event.set()
                                self.frame_count = 0
                                return True, None
                            self.log.debug(self.frame_count,self.timeout_frames,"frame count and timeout frames")
                            
                            self.log.info("Discarding recording, too short:", self.total_recorded / self.cfg.sr, "sec")
                            self._reset()
                            return False, None

        return False, None

    def _run_silero(self, frame):
        rms = np.sqrt(np.mean(frame ** 2)) + 1e-6
        gain = min(0.1 / rms, 10.0)
        frame = np.clip(frame * gain, -1.0, 1.0)

        tensor = torch.from_numpy(frame).float()

        with torch.no_grad():
            return self.vad_model(tensor, self.cfg.sr).item()

    def _reset(self):
        self.recorded_audio = []
        self.total_recorded = 0
        self.silence_counter = 0
        self.vad_model.reset_states()

    