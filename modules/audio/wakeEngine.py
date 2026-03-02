import numpy as np
import onnxruntime as ort
from modules.Logging import Log
from modules.audio.recoderConfig import RecorderConfig
from collections import deque
import time
class WakeEngine:
    def __init__(self, model_path: str, config: RecorderConfig):
        self.cfg = config
        self.log = Log("WakeEngine").log

        self.samples = int(self.cfg.sr * self.cfg.window_sec)

        self.log("Wake model loaded")

        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = 1
        sess_options.inter_op_num_threads = 1

        self.session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=["CPUExecutionProvider"],
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        self.score_buffer = deque(maxlen=self.cfg.vote_window)
        self.last_trigger = 0.0

        self.log("Wake model loaded")

    def detect(self, audio_buffer: deque):
        if len(audio_buffer) < self.samples:
            return False

        audio = np.array(audio_buffer, dtype=np.float32)
        audio = audio / (np.max(np.abs(audio)) + 1e-6)

        x = audio[np.newaxis, ..., np.newaxis].astype(np.float32)

        outputs = self.session.run(
            [self.output_name],
            {self.input_name: x}
        )

        score = float(outputs[0][0][0])
        print(f"\rWake score: {score:.4f}",end="")
        self.score_buffer.append(score)

        positives = sum(s >= self.cfg.threshold for s in self.score_buffer)

        now = time.time()

        if positives >= self.cfg.vote_required and (
            now - self.last_trigger
        ) > self.cfg.cooldown_sec:

            self.last_trigger = now
            self.score_buffer.clear()
            self.log("Wake word detected")
            return True

        return False

