"""Transcribe a 16 kHz mono WAV into word-timed JSON using sherpa-onnx.

Usage: python3 tools/transcribe.py {parakeet|small|turbo} in.wav out.json [language]
"""
import json
import re
import sys
import wave

import numpy as np
import sherpa_onnx

MODELS = "/opt/models"
VAD = "/opt/silero_vad.onnx"


def load(path):
    with wave.open(path) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return pcm.astype(np.float32) / 32768


def recognizer(kind, language):
    if kind == "parakeet":
        d = f"{MODELS}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
        return sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx",
            joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt",
            model_type="nemo_transducer", num_threads=4)
    d = f"{MODELS}/sherpa-onnx-whisper-{kind}"
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{d}/{kind}-encoder.int8.onnx", decoder=f"{d}/{kind}-decoder.int8.onnx",
        tokens=f"{d}/{kind}-tokens.txt", language=language, task="transcribe",
        num_threads=4, tail_paddings=800)


def collapse_loops(text):
    """Whisper sometimes loops ("dah dah dah ..."); keep at most two repeats of a phrase."""
    return re.sub(r"\b((?:\S+\s+){0,3}?\S+)(?:\s+\1\b){2,}", r"\1 \1", text)


def spread_words(text, t0, t1):
    """Whisper here has no word timings: spread words over the segment by character length."""
    toks = text.split()
    if not toks:
        return []
    weights = [len(t) + 2 for t in toks]
    total, t, words = sum(weights), t0, []
    for tok, wt in zip(toks, weights):
        dur = (t1 - t0) * wt / total
        words.append({"w": tok, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    return words


def speech_segments(samples):
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = VAD
    cfg.silero_vad.min_silence_duration = 0.2
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = 7
    cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    window = cfg.silero_vad.window_size
    out = []
    for i in range(0, len(samples), window):
        vad.accept_waveform(samples[i:i + window])
        while not vad.empty():
            out.append((vad.front.start, np.array(vad.front.samples)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        out.append((vad.front.start, np.array(vad.front.samples)))
        vad.pop()
    return out


def words_from(result, offset, seg_end):
    words = []
    for tok, ts in zip(result.tokens, result.timestamps):
        t = offset + ts
        starts_word = tok.startswith((" ", "▁")) or not words
        text = tok.replace("▁", " ")
        if starts_word:
            if words:
                words[-1]["end"] = round(t, 3)
            words.append({"w": text.strip(), "start": round(t, 3), "end": None})
        else:
            words[-1]["w"] += text
    if words:
        words[-1]["end"] = round(seg_end, 3)
    for a, b in zip(words, words[1:]):
        # A word cannot run into the gap before the next one by more than ~0.6s.
        a["end"] = round(min(a["end"], a["start"] + 0.6 + 0.08 * len(a["w"])), 3)
    return [w for w in words if w["w"]]


def main():
    kind, wav, out = sys.argv[1:4]
    language = sys.argv[4] if len(sys.argv) > 4 else ""
    samples = load(wav)
    rec = recognizer(kind, language)
    segs = []
    for start, chunk in speech_segments(samples):
        s = rec.create_stream()
        s.accept_waveform(16000, chunk)
        rec.decode_stream(s)
        r = s.result
        t0, t1 = start / 16000, (start + len(chunk)) / 16000
        seg = {"start": round(t0, 3), "end": round(t1, 3), "text": r.text.strip()}
        if kind == "parakeet" and r.timestamps:
            seg["words"] = words_from(r, t0, t1)
        if kind != "parakeet":
            seg["text"] = collapse_loops(seg["text"])
            seg["lang"] = getattr(r, "lang", "")
            seg["words"] = spread_words(seg["text"], t0, t1)
        segs.append(seg)
    json.dump({"duration": len(samples) / 16000, "segments": segs}, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
