"""Edit decision lists for the bagpipe unboxing.

Each shot: (clip, in_s, out_s, speed, audio, caption, opts)
  audio: "raw"   original sound untouched (chanter / pipes)
         "clean" denoised natural sound with all speech gated out
         "mute"  no source sound, music only
  caption: on-screen Bahasa Melayu story caption, or None
  opts: cx = horizontal crop centre for 9:16 (0..1), cap_at = caption delay (s),
        cap_dur = caption duration (s), cap2 = (delay, text) second caption
"""

YOUTUBE = [
    # Cold open: one blast of the finished pipes, then the sealed box.
    ("230", 5.0, 8.0, 1, "raw", None, {}),
    ("208", 0.0, 6.0, 1, "clean", None, {"intro": True}),
    ("208", 8.0, 14.0, 1, "clean", "Terus dari McCallum Bagpipes, Scotland.", {}),
    # Wrap and outer boxes, speed-ramped.
    ("210", 0.0, 44.0, 4, "mute", "Langkah pertama: buang balutan plastik...",
     {"cap2": (5.5, "...yang tak habis-habis.")}),
    ("210", 44.0, 66.0, 2, "mute", "Eh, ada DUA kotak!", {"cap_at": 1.5}),
    ("210", 66.0, 172.0, 6, "mute", "Buka satu-satu. Sabar...", {}),
    ("214", 0.0, 14.0, 1.5, "clean", "Bubble wrap di mana-mana.", {"cap_at": 3}),
    ("214", 14.0, 75.0, 6, "mute", None, {}),
    # The long box: the instrument itself.
    ("216", 60.0, 78.0, 3, "mute", "Kotak terakhir. Yang paling penting.", {}),
    ("216", 78.0, 92.0, 1, "clean", "Detik yang ditunggu...", {"cap_at": 1}),
    ("216", 92.0, 135.0, 3, "mute", "Satu demi satu bahagian keluar.", {}),
    ("216", 135.0, 160.0, 1.25, "clean", "Drone, tali, tassel... semua ada.", {"cap_at": 4}),
    ("216", 160.0, 200.0, 2.5, "mute", None, {}),
    ("216", 200.0, 246.0, 2, "mute", "Lengkap satu set!", {"cap_at": 11, "cap_dur": 4}),
    # Detail montage.
    ("222", 0.0, 5.0, 1, "mute", "Tengok kemasan dia.", {}),
    ("220", 9.0, 13.0, 1, "mute", "Ukiran McCallum pada chanter.", {}),
    ("222", 5.0, 10.0, 1, "mute", None, {}),
    ("218", 15.0, 20.0, 1, "mute", None, {}),
    ("222", 15.0, 20.0, 1, "mute", None, {}),
    ("222", 33.0, 38.0, 1, "mute", None, {}),
    ("222", 24.0, 28.0, 1, "mute", None, {}),
    # First sounds.
    ("224", 5.0, 14.0, 1, "raw", "Uji chanter dulu.", {}),
    ("226", 4.0, 20.0, 1, "raw", "Bunyi pertama!", {"cap_at": 1}),
    ("228", 0.0, 30.0, 3, "mute", "Pasang reed, laras, cuba lagi.", {}),
    ("228", 53.5, 57.0, 1, "raw", None, {}),
    ("228", 62.0, 65.0, 1, "raw", None, {}),
    ("228", 70.0, 73.5, 1, "raw", None, {}),
    ("228", 78.0, 118.0, 4, "mute", "Pasang drone pada beg.", {}),
    ("228", 118.0, 127.0, 1, "clean", "Dah siap. Jom main!", {"cap_at": 2}),
    # Finale.
    ("230", 0.0, 21.6, 1, "raw", "Dan inilah bunyinya...", {"cap_dur": 2.2, "outro": True}),
]

TIKTOK = [
    ("230", 5.0, 8.0, 1, "raw", "Bagpipe baru sampai dari Scotland!",
     {"cx": 0.33, "cap_at": 0, "cap_dur": 3}),
    ("208", 2.0, 8.0, 2, "mute", "Jom unbox!", {"cap_at": 0.2}),
    ("210", 0.0, 172.0, 14, "mute", "Balutan dia... tak habis-habis.", {"cap_at": 1.5, "cap_dur": 4}),
    ("214", 0.0, 14.0, 3, "mute", None, {}),
    ("216", 80.0, 88.0, 1.25, "clean", "Detik yang ditunggu...", {}),
    ("216", 135.0, 160.0, 3, "mute", "Satu demi satu...", {}),
    ("216", 225.0, 231.0, 1, "mute", "Lengkap satu set!", {"cap_at": 1}),
    ("222", 0.0, 2.5, 1, "mute", "Kemasan dia, wow.", {"cap_dur": 5}),
    ("220", 9.0, 11.5, 1, "mute", None, {}),
    ("218", 16.0, 18.5, 1, "mute", None, {}),
    ("222", 33.0, 35.5, 1, "mute", None, {}),
    ("226", 5.0, 10.0, 1, "raw", "Bunyi pertama!", {}),
    ("228", 118.0, 124.0, 2, "mute", "Jom main!", {}),
    ("230", 2.0, 21.6, 1, "raw", None, {"cx": 0.47, "outro": True}),
]
