"""Assemble the bagpipe unboxing edit.

Usage: python3 edit/build.py {youtube|tiktok} WORK_DIR OUT.mp4 [MUSIC.wav]

WORK_DIR must hold audio/<clip>.wav (16 kHz, for the speech map), tx/<clip>.json
(VAD speech segments) and clean/<clip>.wav (48 kHz denoised). Without MUSIC.wav a
drone pad is derived from the finale's own bagpipe drones.
"""
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from edl import TIKTOK, YOUTUBE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/bagpipe-unbox"
CARDS = ROOT / "edit/cards/out"
FPS = 30
SR = 48000
GRADE = "eq=contrast=1.06:saturation=1.12:gamma=0.98"


def sh(*args):
    subprocess.run(args, check=True)


def src(clip):
    return next(SRC.glob(f"*_{clip}.mov"))


def read_wav(path):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels()).mean(axis=1), w.getframerate()


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if data.ndim == 1 else data.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def source_audio(clip, start, end):
    """Raw camera audio at 48 kHz mono."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start}", "-t", f"{end - start}", "-i", str(src(clip)),
         "-vn", "-ac", "1", "-ar", str(SR), "-af", "highpass=f=50", "-f", "s16le", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768


def speech_gate(work, clip, start, n):
    """Gain curve that silences every VAD speech segment (with soft 120 ms edges)."""
    gain = np.ones(n, dtype=np.float32)
    for seg in json.load(open(work / f"tx/{clip}.json"))["segments"]:
        a = int((seg["start"] - 0.15 - start) * SR)
        b = int((seg["end"] + 0.15 - start) * SR)
        if b > 0 and a < n:
            gain[max(a, 0):min(b, n)] = 0
    k = int(0.12 * SR)
    return np.convolve(gain, np.ones(k) / k, mode="same").astype(np.float32)


def stretch(x, speed):
    """Tempo change without pitch shift, via ffmpeg atempo."""
    if speed == 1:
        return x
    tmp = Path("/tmp/_st.wav")
    write_wav(tmp, x)
    chain = []
    s = speed
    while s > 2:
        chain.append("atempo=2")
        s /= 2
    chain.append(f"atempo={s}")
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp), "-af", ",".join(chain),
                          "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768


def fit(x, n):
    return x[:n] if len(x) >= n else np.pad(x, (0, n - len(x)))


def edge_fade(x, ms=20):
    k = min(int(SR * ms / 1000), len(x) // 2)
    if k:
        ramp = np.linspace(0, 1, k, dtype=np.float32)
        x[:k] *= ramp
        x[-k:] *= ramp[::-1]
    return x


def drone_pad(seconds):
    """Loopable Highland drone bed made from the finale's own drones."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", "5.0", "-t", "3.2", "-i", str(src("230")), "-vn", "-ac", "1",
         "-ar", str(SR), "-af", "highpass=f=60,lowpass=f=300,lowpass=f=300,lowpass=f=300",
         "-f", "s16le", "-"], check=True, capture_output=True).stdout
    loop = np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768
    loop /= np.max(np.abs(loop)) + 1e-9
    xf = int(0.8 * SR)
    step = len(loop) - xf
    n = int(seconds * SR) + len(loop)
    pad = np.zeros(n, dtype=np.float32)
    win = np.ones(len(loop), dtype=np.float32)
    win[:xf] = np.sqrt(np.linspace(0, 1, xf))
    win[-xf:] = np.sqrt(np.linspace(1, 0, xf))
    for i in range(0, n - len(loop), step):
        pad[i:i + len(loop)] += loop * win
    t = np.arange(n) / SR
    pad *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 9.0)
    return pad[:int(seconds * SR)] * 0.5


def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def captions(events, vertical):
    if vertical:
        play, size, margin_v, wrap = "1080x1920", 76, 640, 22
    else:
        play, size, margin_v, wrap = "1920x1080", 64, 84, 40
    w, h = play.split("x")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display Black,{size},&H00FFFFFF,&H00FFFFFF,&H002E10C8,&H64000000,0,0,0,0,100,100,0,0,3,18,0,2,80,80,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for t0, t1, text in events:
        words, rows, row = text.split(), [], ""
        for word in words:
            if row and len(row) + 1 + len(word) > wrap:
                rows.append(row)
                row = word
            else:
                row = f"{row} {word}".strip()
        rows.append(row)
        body = r"\N".join(rows)
        anim = r"{\fad(140,200)\fscx70\fscy70\t(0,220,\fscx106\fscy106)\t(220,320,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,{anim}{body}")
    return head + "\n".join(lines) + "\n"


def main():
    version, work, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    music_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    edl = YOUTUBE if version == "youtube" else TIKTOK
    vertical = version == "tiktok"
    seg_dir = work / f"segs_{version}"
    seg_dir.mkdir(parents=True, exist_ok=True)

    t = 0.0
    sfx_parts, music_gain, cap_events, files = [], [], [], []
    intro_at = outro_at = None
    for i, (clip, a, b, speed, audio, cap, opt) in enumerate(edl):
        dur = (b - a) / speed
        frames = round(dur * FPS)
        dur = frames / FPS
        n = int(round(dur * SR))
        vf = [f"setpts=(PTS-STARTPTS)/{speed}", f"fps={FPS}"]
        if vertical:
            cx = opt.get("cx", 0.5)
            vf += [f"crop=ih*9/16:ih:x='min(max({cx}*iw-ow/2,0),iw-ow)':y=0",
                   "scale=1080:1920:flags=lanczos", "unsharp=5:5:0.6"]
        else:
            vf += ["scale=1920:1080:flags=lanczos"]
        vf.append(GRADE)
        seg = seg_dir / f"{i:03d}.mp4"
        if not seg.exists():
            sh("ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a + 1}", "-i", str(src(clip)),
               "-an", "-vf", ",".join(vf), "-frames:v", str(frames), "-c:v", "libx264", "-crf", "12",
               "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS), str(seg))
        files.append(seg)

        if audio == "raw":
            x = fit(stretch(source_audio(clip, a, b), speed), n)
            g = 0.0
        elif audio == "clean":
            clean, _ = read_wav(work / f"clean/{clip}.wav")
            x = clean[int(a * SR):int(b * SR)]
            x = x * fit(speech_gate(work, clip, a, len(x)), len(x)) * 1.6
            x = fit(stretch(x, speed), n)
            g = 0.55
        else:
            x = np.zeros(n, dtype=np.float32)
            g = 1.0
        sfx_parts.append(edge_fade(x.astype(np.float32)))
        music_gain.append(np.full(n, g, dtype=np.float32))

        if cap:
            c0 = t + opt.get("cap_at", 0.3)
            c1 = min(c0 + opt.get("cap_dur", 3.2), t + dur - 0.1)
            cap2 = opt.get("cap2")
            if cap2:
                c1 = min(c1, t + cap2[0] - 0.05)
            cap_events.append((c0, c1, cap))
            if cap2:
                cap_events.append((t + cap2[0], min(t + cap2[0] + 3.2, t + dur - 0.1), cap2[1]))
        if opt.get("intro"):
            intro_at = t
        if opt.get("outro"):
            outro_at = t + dur - 6.0
        t += dur

    total = t
    sfx = np.concatenate(sfx_parts)
    gain = np.concatenate(music_gain)
    k = int(0.7 * SR)
    gain = np.convolve(np.pad(gain, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    if music_path:
        music, _ = read_wav(music_path)
        reps = int(np.ceil(len(sfx) / len(music)))
        music = np.tile(music, reps)[:len(sfx)] * 0.55
    else:
        music = drone_pad(total)[:len(sfx)] * 0.30
    music = fit(music, len(sfx))
    fade = int(1.5 * SR)
    music[:fade] *= np.linspace(0, 1, fade)
    mix = sfx + music * gain
    write_wav(work / f"mix_{version}.wav", mix)

    (work / f"caps_{version}.ass").write_text(captions(cap_events, vertical))
    lst = work / f"list_{version}.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    sh("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
       str(work / f"body_{version}.mp4"))

    if os.environ.get("REMIX") and out.exists():
        # Video is already final: swap in the new mix without re-encoding picture.
        tmp = out.with_suffix(".remix.mp4")
        sh("ffmpeg", "-v", "error", "-y", "-i", str(out), "-i", str(work / f"mix_{version}.wav"),
           "-map", "0:v", "-map", "1:a", "-af", "aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-t", f"{total:.3f}",
           "-movflags", "+faststart", str(tmp))
        tmp.replace(out)
        print(f"{out}: remixed audio, {total:.1f}s")
        return

    aspect = "9x16" if vertical else "16x9"
    inputs = ["-i", str(work / f"body_{version}.mp4"), "-i", str(work / f"mix_{version}.wav")]
    graph, last, idx = [], "0:v", 2
    for at, name in ((intro_at, "intro"), (outro_at, "outro")):
        if at is None:
            continue
        inputs += ["-itsoffset", f"{at:.3f}", "-i", str(CARDS / f"{name}_{aspect}.mov")]
        graph.append(f"[{last}][{idx}:v]overlay=0:0:eof_action=pass:format=auto[v{idx}]")
        last, idx = f"v{idx}", idx + 1
    ass = str(work / f"caps_{version}.ass").replace(":", r"\:")
    graph.append(f"[{last}]ass='{ass}',format=yuv420p[vout]")
    graph.append("[1:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    sh("ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph),
       "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
       "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-profile:v", "high", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-movflags", "+faststart", str(out))
    print(f"{out}: {total:.1f}s, {len(cap_events)} captions")


if __name__ == "__main__":
    main()
