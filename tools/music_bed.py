"""Generate an original, loopable music bed tuned to the bagpipes (A = 490 Hz).

Usage: python3 tools/music_bed.py out.wav [seconds]
A Celtic-flavoured A-G-D-A progression: plucked arpeggio, warm pad, bass and light
percussion. The first loop has no drums so the track can build.
"""
import subprocess
import sys
import wave

import numpy as np

SR = 48000
A4 = 490.0  # measured pitch of the pipes' chanter A
BPM = 92
BEAT = 60 / BPM
rng = np.random.default_rng(7)


def hz(semis_from_a4):
    return A4 * 2 ** (semis_from_a4 / 12)


# Chords as semitone offsets from A4: root note (bass) and chord tones.
CHORDS = [
    (-24, [-12, -8, -5]),   # A  (A, C#, E)
    (-26, [-14, -10, -7]),  # G  (G, B, D)
    (-31, [-19, -15, -12]), # D  (D, F#, A)
    (-24, [-12, -8, -5]),   # A
]
BARS_PER_CHORD = 2


def env(n, attack, release):
    e = np.ones(n, dtype=np.float32)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pluck(freq, dur, bright=0.5):
    n = int(dur * SR)
    period = max(int(SR / freq), 2)
    y = np.zeros(n + period, dtype=np.float32)
    y[:period] = rng.uniform(-1, 1, period) * np.hanning(period)
    decay = 0.996
    for start in range(period, n + period, period):
        prev = y[start - period:start]
        nxt = np.roll(prev, -1)
        seg = decay * (bright * prev + (1 - bright) * 0.5 * (prev + nxt))
        end = min(start + period, n + period)
        y[start:end] = seg[:end - start]
    return y[period:] * env(n, 0.002, 0.05)


def pad_voice(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    for detune in (-0.12, 0.12):
        f = freq * 2 ** (detune / 12)
        for k in range(1, 7):
            out += np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) / (k ** 1.6)
    return out * env(n, 0.5, 0.6) * 0.12


def bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return tone * np.exp(-t / 0.35) * env(n, 0.005, 0.03)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 45 + 75 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def noise_hit(dur, decay, hp):
    n = int(dur * SR)
    x = rng.uniform(-1, 1, n).astype(np.float32)
    x = x - np.convolve(x, np.ones(hp) / hp, mode="same")  # crude high-pass
    return x * np.exp(-np.arange(n) / SR / decay)


def add(buf, x, at, gain):
    i = int(at * SR)
    j = min(i + len(x), len(buf))
    if i < len(buf):
        buf[i:j] += x[:j - i] * gain


def render(seconds):
    loop_len = len(CHORDS) * BARS_PER_CHORD * 4 * BEAT
    loops = int(np.ceil(seconds / loop_len))
    buf = np.zeros(int(loops * loop_len * SR) + SR, dtype=np.float32)
    arp = [0, 1, 2, 3, 2, 1, 3, 2]
    for L in range(loops):
        drums = L > 0
        for c, (root, tones) in enumerate(CHORDS):
            bar0 = (L * len(CHORDS) + c) * BARS_PER_CHORD * 4 * BEAT
            chord_dur = BARS_PER_CHORD * 4 * BEAT
            for tone in tones:
                add(buf, pad_voice(hz(tone), chord_dur + 0.6), bar0, 1.0)
            notes = [hz(tones[0] + 12), hz(tones[1] + 12), hz(tones[2] + 12), hz(tones[0] + 24)]
            for step in range(BARS_PER_CHORD * 8):
                at = bar0 + step * BEAT / 2
                add(buf, pluck(notes[arp[step % 8]], 0.9, 0.35), at, 0.32 if step % 2 else 0.4)
                if step % 2 == 0:
                    add(buf, bass(hz(root), BEAT * 0.95), at, 0.5 if step % 4 == 0 else 0.35)
                if drums:
                    beat = step / 2
                    if step % 4 == 0:
                        add(buf, kick(), at, 0.7)
                    if step % 4 == 2:
                        add(buf, noise_hit(0.18, 0.05, 6), at, 0.18)
                    add(buf, noise_hit(0.05, 0.012, 3), at + BEAT / 4, 0.05)
                    del beat
    return buf[:int(seconds * SR)]


def main():
    out = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 90
    x = render(seconds)
    x /= np.max(np.abs(x)) + 1e-9
    tmp = out + ".dry.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 0.8 * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    "aecho=0.8:0.6:47|83|131|197:0.30|0.22|0.16|0.11,"
                    "highpass=f=35,alimiter=limit=0.9,loudnorm=I=-18:TP=-2",
                    "-ar", str(SR), "-ac", "1", out], check=True)


if __name__ == "__main__":
    main()
