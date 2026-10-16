# Technical demonstration

- **Video:** [Before_the_Merge_technical_demo.mp4](Before_the_Merge_technical_demo.mp4) (4:48, 1080p, captions burned in)
- **Subtitles:** [Before_the_Merge_technical_demo.en.srt](Before_the_Merge_technical_demo.en.srt)
- **Narration and shot list:** [../DEMO_SCRIPT.md](../DEMO_SCRIPT.md)

Every frame shows commands and outputs taken from the real runs
(`runs/20261015T052758Z-daba50c83a0b`, `runs/20261016T000750Z-75c221157a38`,
`runs/20261015T033503Z-f6539b3bc938`). The narration voice is synthesized locally.

## Rebuild

```bash
pip install kokoro-onnx soundfile pillow
KOKORO_DIR=/path/to/kokoro-models python3 demo/source/render.py      # writes demo/source/build/
cd demo/source/build
ffmpeg -f concat -safe 0 -i scenes.txt -i narration.wav \
  -vf "fps=30,format=yuv420p,subtitles=captions.srt:force_style='FontSize=12,BorderStyle=4,MarginV=14'" \
  -c:v libx264 -crf 20 -c:a aac -shortest demo.mp4
```
