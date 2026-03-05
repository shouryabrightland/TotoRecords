
import numpy as np
import torch
from modules.Logging import Log
from modules.audio.recoderConfig import RecorderConfig


class VADEngine:
    def __init__(self, config: RecorderConfig):
        self.cfg = config
        self.log = Log("VADEngine")

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

        self.frame_buffer = np.array([], dtype=np.float32)

        self.min_samples = int(self.cfg.sr * self.cfg.min_recording_sec)
        self.silence_samples = int(self.cfg.sr * self.cfg.vad_silence_sec)



    def process(self, chunk):
        self.frame_buffer = np.concatenate((self.frame_buffer, chunk))

        while len(self.frame_buffer) >= self.cfg.vad_frame:

            frame = self.frame_buffer[:self.cfg.vad_frame]
            self.frame_buffer = self.frame_buffer[self.cfg.vad_frame:]

            speech_prob = self._run_silero(frame)
            print(f"\r[VAD] Speech Probability: {speech_prob:.4f}",end="")

            if speech_prob > 0.2:
                self.recorded_audio.extend(frame) # Only add to recorded audio if speech is detected, otherwise just count silence

            if speech_prob < self.cfg.vad_threshold:
                self.silence_counter += len(frame)
            else:
                self.silence_counter = 0
                self.total_recorded += len(frame)

            if (
                self.silence_counter > self.silence_samples
                and self.total_recorded > self.min_samples
            ):
                audio = np.array(self.recorded_audio, dtype=np.float32)
                self._reset()
                self.log.info("Speech ended")
                return True, audio

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

    