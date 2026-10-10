# Project film source

20-second, 1280×720, 24fps silent landscape film. The plan and composition brief
are in the parent directory. Source screenshots come from the actual application
using the public fictional PDF. GSAP 3.14.2 is vendored locally with its upstream
copyright/license header. Generic font stacks avoid external font dependencies.

Requires Node 22+, Chrome, and FFmpeg. From the repository root:

```bash
npx --yes hyperframes@0.8.145 check brag-output/composition
npx --yes hyperframes@0.8.145 snapshot brag-output/composition --at 2,6,12,19
npx --yes hyperframes@0.8.145 render brag-output/composition \
  --quality high --fps 24 --workers 2 --output "$PWD/brag-output/brag.mp4"
```

The reviewed scene at 12 seconds shows the answer and citation. Extract that
poster and place it at frame zero for a useful idle thumbnail:

```bash
ffmpeg -y -ss 12 -i brag-output/brag.mp4 -frames:v 1 brag-output/brag.jpg
ffmpeg -y -i brag-output/brag.mp4 -i brag-output/brag.jpg \
  -filter_complex "[0:v][1:v]overlay=enable='eq(n,0)'" \
  -c:v libx264 -crf 16 -pix_fmt yuv420p -an -frames:v 480 \
  -movflags +faststart /tmp/brag-poster.mp4
cp /tmp/brag-poster.mp4 brag-output/brag.mp4
cp brag-output/brag.mp4 doc/assets/brag.mp4
cp brag-output/brag.jpg doc/assets/brag.jpg
```

Review the rendered MP4 and final frame, not only the composition preview.
No narration or third-party soundtrack is included. The two structural warnings
recommend modular sub-compositions; this short film deliberately keeps one file.
Runtime, layout and contrast checks passed with zero errors.
