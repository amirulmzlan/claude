"""Denoise a 48 kHz mono WAV with DPDFNet (sherpa-onnx).

Usage: python3 tools/denoise.py in.wav out.wav [attenuation_limit_db]
"""
import sys
import wave

import numpy as np
import sherpa_onnx

MODEL = "/opt/models/dpdfnet2_48khz_hr.onnx"


def main():
    src, dst = sys.argv[1:3]
    limit = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    with wave.open(src) as w:
        rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    cfg = sherpa_onnx.OfflineSpeechDenoiserConfig(
        model=sherpa_onnx.OfflineSpeechDenoiserModelConfig(
            dpdfnet=sherpa_onnx.OfflineSpeechDenoiserDpdfNetModelConfig(
                model=MODEL, attenuation_limit_db=limit),
            num_threads=4))
    den = sherpa_onnx.OfflineSpeechDenoiser(cfg)
    out = den(pcm.astype(np.float32) / 32768, rate)
    data = np.clip(np.array(out.samples) * 32767, -32768, 32767).astype(np.int16)
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(out.sample_rate)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    main()
