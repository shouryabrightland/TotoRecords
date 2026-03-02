from dataclasses import dataclass

@dataclass
class RecorderConfig:
    sr: int = 16000

    # Wake
    window_sec: float = 1.5
    hop_sec: float = 0.2
    threshold: float = 0.6
    vote_window: int = 5
    vote_required: int = 3
    cooldown_sec: float = 1.0

    # Recording
    min_recording_sec: float = 0.8 # minimum length of recording to be considered valid
    pre_roll_sec: float = 0.3

    # VAD
    vad_threshold: float = 0.6
    vad_silence_sec: float = 0.8
    vad_frame: int = 512
