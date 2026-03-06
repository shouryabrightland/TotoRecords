import time
from faster_whisper import WhisperModel
from modules.Logging import Log
# ---------------------------
# Whisper API class
# ---------------------------
class STT:
    def __init__(self, model_name="base.en"):
        """
        model_name: "tiny", "small", "medium", "large" (tiny is best for Pi)
        """
        self.log = Log("WhisperAPI")
        self.log.info("Loading Whisper",model_name,"model...")
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8"
        )
        self.log.info("loaded Model successfully...")
    #---------------------------------------

    def transcribe(self,audio,prompt=""):
        """
         immediately transcribes audio
        """
        audio = audio.astype("float32")
        #time.sleep(5)---------------------
        t1 = time.perf_counter()
        self.log.info("transcripting Audio...")
        segments, _ = self.model.transcribe(
            audio,
            language="en",
            task="transcribe",
            beam_size=2,
            initial_prompt=prompt,
            temperature=0.0,
            vad_filter=False,
            condition_on_previous_text=False,
            max_new_tokens=32
        )
        text = " ".join([s.text for s in segments]).strip(" ")
        self.log.info("Transcribed:", text)
        t2 = time.perf_counter()
        self.log.info("time taken in transcription",(t2-t1)*1000,"ms")
        return text