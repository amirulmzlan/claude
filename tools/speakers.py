"""Label transcript segments by speaker, clustering voice embeddings across all clips.

Usage: python3 tools/speakers.py audio_dir tx_dir clip [clip ...]
Adds "spk" (cluster id) and "spk_sim" to each segment of tx_dir/<clip>.json in place.
"""
import json
import sys
import wave

import numpy as np
import sherpa_onnx

MODEL = "/opt/models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"


def load(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def main():
    audio_dir, tx_dir, *clips = sys.argv[1:]
    ext = sherpa_onnx.SpeakerEmbeddingExtractor(
        sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=MODEL, num_threads=4))
    refs, embs = [], []
    for clip in clips:
        pcm = load(f"{audio_dir}/{clip}.wav")
        tx = json.load(open(f"{tx_dir}/{clip}.json"))
        for i, seg in enumerate(tx["segments"]):
            chunk = pcm[int(seg["start"] * 16000):int(seg["end"] * 16000)]
            if len(chunk) < 16000 * 0.6:
                continue
            s = ext.create_stream()
            s.accept_waveform(16000, chunk)
            s.input_finished()
            e = np.array(ext.compute(s))
            embs.append(e / np.linalg.norm(e))
            refs.append((clip, i, seg["end"] - seg["start"]))
    X = np.stack(embs)
    # Greedy agglomerative clustering on cosine similarity, longest segments seed first.
    order = np.argsort([-r[2] for r in refs])
    centroids, members, labels = [], [], np.full(len(refs), -1)
    for idx in order:
        sims = [float(X[idx] @ (c / np.linalg.norm(c))) for c in centroids]
        if sims and max(sims) > 0.45:
            k = int(np.argmax(sims))
            centroids[k] = centroids[k] + X[idx] * refs[idx][2]
            members[k].append(idx)
        else:
            k = len(centroids)
            centroids.append(X[idx] * refs[idx][2])
            members.append([idx])
        labels[idx] = k
    # Renumber clusters by total speaking time, so speaker 0 talks most.
    talk = [sum(refs[i][2] for i in m) for m in members]
    rank = {k: r for r, k in enumerate(np.argsort(talk)[::-1])}
    txs = {c: json.load(open(f"{tx_dir}/{c}.json")) for c in clips}
    for idx, (clip, i, _) in enumerate(refs):
        k = labels[idx]
        c = centroids[k] / np.linalg.norm(centroids[k])
        txs[clip]["segments"][i]["spk"] = int(rank[k])
        txs[clip]["segments"][i]["spk_sim"] = round(float(X[idx] @ c), 3)
    for c, tx in txs.items():
        json.dump(tx, open(f"{tx_dir}/{c}.json", "w"), indent=1, ensure_ascii=False)
    for k in sorted(rank, key=rank.get):
        print(f"speaker {rank[k]}: {talk[k]:.0f}s in {len(members[k])} segments")


if __name__ == "__main__":
    main()
