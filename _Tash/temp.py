import onnx

model = onnx.load("models/silero_vad_16k_op15.onnx")
print(model.opset_import)

import numpy as np
import sounddevice as sd
import onnxruntime as ort
import time

MODEL_PATH = "models/silero_vad_16k_op15.onnx"
SR = 16000
FRAME_SIZE = 512

# ----------------------------
# Load ONNX
# ----------------------------

vad = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

for i in vad.get_inputs():
    print("INPUT:", i.name, i.shape)

for o in vad.get_outputs():
    print("OUTPUT:", o.name, o.shape)

input_name = vad.get_inputs()[0].name
state_name = vad.get_inputs()[1].name
sr_name = vad.get_inputs()[2].name

state = np.zeros((2, 1, 128), dtype=np.float32)
sr_tensor = np.array(SR, dtype=np.int64)

print("\nListening...\n")
print(vad.opset_import)

# ----------------------------
# Audio Callback
# ----------------------------

buffer = np.array([], dtype=np.float32)


def callback(indata, frames, time_info, status):
    global buffer, state

    if status:
        print(status)

    chunk = indata[:, 0].copy()

    # Print raw audio stats
    print(
        "Peak:", np.max(np.abs(chunk)),
        "STD:", np.std(chunk)
    )

    buffer = np.concatenate((buffer, chunk))

    while len(buffer) >= FRAME_SIZE:
        frame = buffer[:FRAME_SIZE]
        buffer = buffer[FRAME_SIZE:]

        x = frame.reshape(1, -1).astype(np.float32)

        outputs = vad.run(
            None,
            {
                input_name: x,
                state_name: state,
                sr_name: sr_tensor,
            },
        )

        speech_prob = float(outputs[0][0][0])
        state = outputs[1]

        print("VAD prob:", round(speech_prob, 4))


# ----------------------------
# Start Stream
# ----------------------------

with sd.InputStream(
    samplerate=SR,
    channels=1,
    blocksize=FRAME_SIZE,
    dtype="float32",
    callback=callback,
):
    print("REAL samplerate:", SR)
    while True:
        time.sleep(0.1)