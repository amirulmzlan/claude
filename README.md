# Bagpipe unboxing renders

Full-quality renders, split into parts under GitHub's 100 MB file limit.

| File | Format | Length |
|---|---|---|
| `bagpipe-unboxing-youtube.mp4` | 1920x1080, 30 fps, H.264 + AAC 320k, -14 LUFS | 4:46 |
| `bagpipe-unboxing-tiktok.mp4` | 1080x1920, 30 fps, H.264 + AAC 320k, -14 LUFS | 1:21 |

Join the parts back into the original files (macOS/Linux):

```bash
cat bagpipe-unboxing-youtube.mp4.part-* > bagpipe-unboxing-youtube.mp4
cat bagpipe-unboxing-tiktok.mp4.part-* > bagpipe-unboxing-tiktok.mp4
shasum -a 256 -c SHA256SUMS
```
