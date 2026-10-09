"""Write the HyperFrames intro/outro card compositions for both aspect ratios."""
from pathlib import Path

HERE = Path(__file__).parent

STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: {W}px; height: {H}px; overflow: hidden; background: transparent; }
#root { position: relative; width: 100%; height: 100%; font-family: "Inter Display", Inter, sans-serif; }
.shade { position: absolute; left: 0; right: 0; bottom: 0; height: 75%;
  background: linear-gradient(to top, rgba(6,10,24,.92), rgba(6,10,24,.65) 40%, rgba(6,10,24,0)); }
.stack { position: absolute; left: {LEFT}; right: {RIGHT}; top: {TOP}; display: flex; flex-direction: column;
  align-items: {ALIGN}; text-align: {TALIGN}; }
.mask { overflow: hidden; padding: 0 20px; }
.kicker { color: #dfe3ea; font-weight: 600; font-size: {K}px; letter-spacing: .42em; }
.big { color: #fff; font-weight: 900; font-size: {B}px; line-height: .95; letter-spacing: -.02em;
  text-shadow: 0 6px 30px rgba(0,0,0,.45); }
.tartan { height: {T}px; width: {TW}px; margin: {TM}px 0; transform-origin: left center; border-radius: 3px;
  background:
    linear-gradient(90deg, transparent 0 18px, rgba(255,206,0,.95) 18px 21px, transparent 21px) 0 0 / 64px 100%,
    linear-gradient(0deg, transparent 0 9px, rgba(255,206,0,.9) 9px 11px, transparent 11px) 0 0 / 100% 32px,
    linear-gradient(90deg, rgba(8,30,70,.75) 0 12px, transparent 12px 40px, rgba(10,60,30,.7) 40px 52px, transparent 52px) 0 0 / 64px 100%,
    linear-gradient(0deg, rgba(8,30,70,.55) 0 6px, transparent 6px 20px, rgba(10,60,30,.5) 20px 26px, transparent 26px) 0 0 / 100% 32px,
    #c8102e; box-shadow: 0 4px 18px rgba(0,0,0,.4); }
.sub { color: #f2f2f2; font-weight: 600; font-size: {S}px; letter-spacing: .04em; }
.sub b { color: #ff3b4f; font-weight: 800; }
.pills { display: flex; gap: {G}px; margin-top: {PM}px; }
.pill { font-weight: 900; font-size: {P}px; letter-spacing: .06em; color: #fff; padding: .45em 1em;
  border-radius: 999px; background: #c8102e; box-shadow: 0 6px 22px rgba(200,16,46,.45); }
.pill.alt { background: #fff; color: #0b1530; box-shadow: 0 6px 22px rgba(0,0,0,.35); }
"""

INTRO_BODY = """
<div class="shade clip" id="shade" data-start="0" data-duration="{D}"></div>
<div class="stack">
  <div class="mask"><div class="kicker" id="k">UNBOXING</div></div>
  <div class="tartan" id="t"></div>
  <div class="mask"><div class="big" id="b">BAGPIPE</div></div>
  <div class="mask"><div class="sub" id="s">McCallum Bagpipes <b>&middot;</b> Scotland</div></div>
</div>
"""

INTRO_JS = """
tl.fromTo("#shade", {opacity: 0}, {opacity: 1, duration: .5, ease: "power2.out"}, 0);
tl.fromTo("#t", {scaleX: 0}, {scaleX: 1, duration: .55, ease: "power3.out"}, .15);
tl.fromTo("#k", {y: 60, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "power3.out"}, .35);
tl.fromTo("#b", {y: 260}, {y: 0, duration: .7, ease: "expo.out"}, .5);
tl.fromTo("#s", {y: 60, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "power3.out"}, .9);
tl.fromTo("#b", {scale: 1}, {scale: 1.04, duration: 3.4, ease: "none"}, 1.2);
tl.to(["#k", "#s"], {y: -50, opacity: 0, duration: .4, ease: "power2.in"}, {OUT});
tl.to("#b", {y: -260, duration: .45, ease: "power3.in"}, {OUT});
tl.to("#t", {scaleX: 0, duration: .4, ease: "power2.in"}, {OUT2});
tl.to("#shade", {opacity: 0, duration: .5}, {OUT2});
"""

OUTRO_BODY = """
<div class="shade clip" id="shade" data-start="0" data-duration="{D}"></div>
<div class="stack">
  <div class="tartan" id="t"></div>
  <div class="mask"><div class="big" id="b" style="font-size:{OB}px">{LINE1}</div></div>
  <div class="mask"><div class="sub" id="s">{LINE2}</div></div>
  <div class="pills">{PILLS}</div>
</div>
"""

OUTRO_JS = """
tl.fromTo("#shade", {opacity: 0}, {opacity: 1, duration: .6}, 0);
tl.fromTo("#t", {scaleX: 0}, {scaleX: 1, duration: .55, ease: "power3.out"}, .1);
tl.fromTo("#b", {y: 200}, {y: 0, duration: .7, ease: "expo.out"}, .3);
tl.fromTo("#s", {y: 50, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "power3.out"}, .7);
document.querySelectorAll(".pill").forEach((p, i) => {
  tl.fromTo(p, {scale: 0, opacity: 0}, {scale: 1, opacity: 1, duration: .45, ease: "back.out(2.2)"}, 1.0 + i * .18);
});
"""

PAGE = """<!doctype html>
<html lang="ms">
<head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<script src="./gsap.min.js"></script><style>{STYLE}</style></head>
<body>
<div id="root" data-composition-id="{ID}" data-start="0" data-duration="{D}" data-width="{W}" data-height="{H}">
{BODY}
</div>
<script>
const tl = gsap.timeline({ paused: true });
{JS}
window.__timelines["{ID}"] = tl;
tl.seek(0);
</script>
</body></html>
"""

SIZES = {
    "16x9": dict(W=1920, H=1080, TOP="52%", LEFT="96px", RIGHT="auto", ALIGN="flex-start", TALIGN="left",
                 K=38, B=180, T=32, TW=640, TM=16, S=40, G=26, PM=34, P=34, OB=118),
    "9x16": dict(W=1080, H=1920, TOP="62%", LEFT="0", RIGHT="0", ALIGN="center", TALIGN="center",
                 K=38, B=176, T=30, TW=620, TM=16, S=40, G=18, PM=34, P=30, OB=110),
}

OUTRO_TEXT = {
    "16x9": ("TERIMA KASIH!", "Sudah tonton sampai habis? Jangan lupa:",
             ["LIKE", "KOMEN", "SUBSCRIBE"]),
    "9x16": ("TERIMA KASIH!", "Suka video ni? Jangan lupa:", ["FOLLOW", "LIKE", "SHARE"]),
}


def fill(template, values):
    for k, v in values.items():
        template = template.replace("{" + k + "}", str(v))
    return template


def write(name, aspect, body, js, dur):
    size = SIZES[aspect]
    style = fill(STYLE, size)
    page = fill(PAGE, {**size, "STYLE": style, "ID": name, "D": dur, "BODY": body, "JS": js})
    (HERE / f"{name}.html").write_text(page)


def main():
    for aspect in SIZES:
        size = SIZES[aspect]
        intro_d = 5.5
        write(f"intro_{aspect}", aspect, fill(INTRO_BODY, {"D": intro_d}),
              fill(INTRO_JS, {"OUT": 4.7, "OUT2": 4.9}), intro_d)
        l1, l2, pills = OUTRO_TEXT[aspect]
        pills_html = "".join(
            f'<div class="pill{" alt" if i % 2 else ""}">{p}</div>' for i, p in enumerate(pills))
        write(f"outro_{aspect}", aspect,
              fill(OUTRO_BODY, {"D": 6, "LINE1": l1, "LINE2": l2, "PILLS": pills_html, "OB": size["OB"]}),
              OUTRO_JS, 6)


if __name__ == "__main__":
    main()
