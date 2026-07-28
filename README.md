[English](README.md) | [简体中文](docs/translations/zh/README.md) | [한국어](docs/translations/ko/README.md) | [日本語](docs/translations/ja/README.md)

## MangaTranslator

Gradio-based web application for automating the translation of manga/comic page images using AI. Targets speech bubbles and text outside of speech bubbles. Supports 60 languages and custom font pack usage.

<div align="left">
  <table>
    <tr>
      <th style="text-align: left">Original</th>
      <th style="text-align: left">Translated (w/ a single click)</th>
    </tr>
    <tr>
      <td><img src="docs/images/example_original.jpg" width="400" /></td>
      <td><img src="docs/images/example_translation.jpg" width="400" /></td>
    </tr>
  </table>
</div>

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)
- [Post-Install Setup](#post-install-setup)
- [Run](#run)
- [Documentation](#documentation)
- [Updating](#updating)
- [License & Credits](#license--credits)

## Features

- **Detection**: Speech bubble detection & segmentation (YOLO, SAM 2.1/3)
- **Cleaning**: Inpaint speech bubbles and OSB text (FLUX.2 Klein, FLUX.1 Kontext, or OpenCV)
- **Translation**: LLM-powered OCR & translation (60 languages)
- **Rendering**: Text rendering with alignment and custom font packs
- **Upscaling**: 2x-AnimeSharpV4 for enhanced output quality
- **Processing**: Single/batch processing with directory preservation and ZIP support
- **Interfaces**: Web UI (Gradio) and CLI
- **Automation**: One-click translation; no intervention required

## Requirements

- Python 3.10+
- PyTorch (CPU, CUDA, ROCm, XPU, MPS)
- Font pack with `.ttf`/`.otf` files; included with portable package
- LLM for Japanese source text; VLM for other languages (API or local)

## Install

### Portable Package (Recommended)

Download the standalone zip from the releases page: [Portable Build](https://github.com/meangrinch/MangaTranslator/releases/tag/portable)

**Requirements:**

- **Windows:** Bundled Python/Git included; no additional requirements
- **Linux/macOS:** Python 3.10+ and Git must be installed on your system

**Setup:**

1. Extract the zip file
2. Run the setup script for your platform:
   - **Windows:** Double-click `setup.bat`
   - **Linux/macOS:** Run `./setup.sh` in terminal
3. PyTorch version is automatically detected and installed based on your system
4. Open the launcher script created in `./MangaTranslator/`:
   - **Windows:** `start-webui.bat`
   - **Linux/macOS:** `start-webui.sh`

Included font packs:

- _Komika_ (normal text)
- _Comicka_ (normal/OSB text)
- _Roboto_ (supports accents)
- _Noto Sans SC_ (Simplified Chinese)
- _Noto Sans KR_ (Korean)
- _Noto Sans JP_ (Japanese)
- _Noto Sans Thai_ (Thai)

> [!TIP]
> In the event that you need to transfer to a fresh portable package:
>
> - You can safely move the `fonts`, `models`, and `output` directories to the new portable package
> - You might be able to move the `runtime` directory over, assuming the same setup configuration is wanted

### Manual install

1. Clone and enter the repo

```bash
git clone https://github.com/meangrinch/MangaTranslator.git
cd MangaTranslator
```

2. Create and activate a virtual environment (recommended)

```bash
python -m venv venv
# Windows PowerShell/CMD
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Install PyTorch (see: [PyTorch Install](https://pytorch.org/get-started/locally/))

```bash
# Example (CUDA 13.0)
pip install torch==2.11.0+cu130 torchvision==0.26.0+cu130 --extra-index-url https://download.pytorch.org/whl/cu130
# Example (ROCm 7.1)
pip install torch==2.11.0+rocm7.1 torchvision==0.26.0+rocm7.1 --extra-index-url https://download.pytorch.org/whl/rocm7.1
# Example (XPU)
pip install torch==2.11.0+xpu torchvision==0.26.0+xpu --extra-index-url https://download.pytorch.org/whl/xpu
# Example (MPS/CPU)
pip install torch==2.11.0 torchvision==0.26.0
```

4. Install Nunchaku (optional, for FLUX.1 Kontext via Nunchaku backend)

- Nunchaku wheels are not on PyPI. Install directly from the v1.3.0dev20260213 GitHub release URL, matching your OS and Python version. CUDA only, and requires a 2000-series card or newer.

```bash
# Example (Windows, Python 3.13, PyTorch 2.11.0, CUDA 13.0)
pip install https://github.com/nunchaku-ai/nunchaku/releases/download/v1.3.0dev20260213/nunchaku-1.3.0.dev20260213+cu13.0torch2.11-cp313-cp313-win_amd64.whl

# Example (Linux, Python 3.13, PyTorch 2.11.0, CUDA 13.0)
pip install https://github.com/nunchaku-ai/nunchaku/releases/download/v1.3.0dev20260213/nunchaku-1.3.0.dev20260213+cu13.0torch2.11-cp313-cp313-linux_x86_64.whl
```

> [!NOTE]
> Nunchaku is not necessary for the use of Flux models via the sd.cpp/SDNQ backends.

5. Install dependencies

```bash
pip install -r requirements.txt
```

## Post-Install Setup

### Models

- The application will automatically download and use all required models

### Fonts

- Put font packs as subfolders in `fonts/` with `.otf`/`.ttf` files
- Prefer filenames that include `italic`/`bold` or both so variants are detected
- Example structure:

```text
fonts/
├─ CC Wild Words/
│  ├─ CCWildWords-Regular.otf
│  ├─ CCWildWords-Italic.otf
│  ├─ CCWildWords-Bold.otf
│  └─ CCWildWords-BoldItalic.otf
└─ Komika/
   ├─ KOMIKA-HAND.ttf
   └─ KOMIKA-HANDBOLD.ttf
```

### LLM setup

- Providers: Google, OpenAI, Anthropic, SpaceXAI, DeepSeek, Z.ai, Moonshot AI, Xiaomi MiMo, OpenRouter, OpenAI-Compatible
- Web UI: configure provider/model/key in the Config tab (stored locally)
- CLI: pass keys/URLs as flags or via env vars
- Env vars: `GOOGLE_API_KEY` / `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `SPACEXAI_API_KEY` / `XAI_API_KEY`, `DEEPSEEK_API_KEY`, `ZAI_API_KEY`, `MOONSHOT_API_KEY`, `MIMO_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_COMPATIBLE_API_KEY`
- OpenAI-compatible default URL: `http://localhost:8080/v1`

> [!NOTE]
> The following models are automatically detected when used via the OpenAI-Compatible provider and receive optimized prompting. They are text-only and require two-step translation + local OCR. The `special_instructions` field maps to their corresponding glossary/terminology (one entry per line, e.g., `term -> translation`).
>
> - **YanoljaNEXT-Rosetta** (e.g., `yanolja/YanoljaNEXT-Rosetta-4B-2511-GGUF`)
> - **Hy-MT2** (e.g., `tencent/Hy-MT2-7B`). Also pre-fills the model's recommended sampling parameters

### OSB text setup (optional)

If you want to use the OSB text pipeline, you need a Hugging Face token with access to the following repositories:

- `deepghs/AnimeText_yolo`

#### Steps to create a token:

1. Sign in or create a Hugging Face account
2. Visit and accept the terms on:
   - [AnimeText_yolo](https://huggingface.co/deepghs/AnimeText_yolo)
   - [FLUX.1 Kontext (dev)](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev) (optional, if using FLUX.1 Kontext via Nunchaku backend)
   - [SAM 3](https://huggingface.co/facebook/sam3) (optional, if using SAM 3)
3. Create a new access token in your Hugging Face settings with read access to gated repos ("Read access to contents of public gated repos")
4. Add the token to the app:
   - Web UI: set `hf_token` in Config
   - Env var (alternative): set `HF_TOKEN`
5. Save config to preserve the token across sessions

### Remote stable-diffusion.cpp Flux backend (optional)

MangaTranslator can send Flux inpainting to an already-running
[`sd-server`](https://github.com/leejet/stable-diffusion.cpp) instead of downloading GGUF
weights and managing the server process itself. Useful when the GPU lives on another
machine, or when you want to run `sd-server` with your own flags.

1. Start `sd-server` yourself, loaded with the model matching your inpainting method
   (see [Equivalent `sd-server` commands](#equivalent-sd-server-commands) below).
2. Web UI: select **Remote sd.cpp** as the Flux Backend and enter `http://127.0.0.1:1234`
   in **Remote sd.cpp URL**.
3. CLI: pass `--osb-flux-backend sdcpp_remote` with `--osb-flux-sdcpp-remote-url`, or set
   `MANGA_TRANSLATOR_FLUX_SDCPP_URL`.

The app health-checks `<base-url>/v1/models`, submits jobs to `<base-url>/sdcpp/v1/img_gen`,
and polls the job endpoint the server returns. It never downloads models for, starts, or
stops a remote server, so the **Flux Model Quant**, **Text Encoder Model Quant** and
**Cache Method** settings are hidden for this backend — the server owns them. A failed
remote job falls back to OpenCV inpainting for that region.

> **Point this at a single `sd-server`, not a load balancer.** `sd-server` keeps jobs in the
> memory of the process that accepted them, so a proxy that spreads requests over several
> replicas will sometimes route a poll to a replica that has never heard of the job and
> answer `404`. Scattered failures are retried, but sustained ones fail the region. If you
> host `sd-server` behind an autoscaler (Modal, Cloud Run, a k8s Service), pin it to one
> replica or enable session affinity.

#### Equivalent `sd-server` commands

These reproduce what the managed `sd.cpp` backend launches. Substitute your own paths; the
managed backend keeps its downloads under `models/flux/sdcpp/`, so you can point at those
files directly if you have already used it once.

**Flux.2 Klein 4B** (`--osb-inpainting-method flux_klein_4b`):

```bash
sd-server --listen-ip 127.0.0.1 --listen-port 1234 \
  --diffusion-model models/flux/sdcpp/flux-2-klein-4b-Q4_K_M.gguf \
  --llm          models/flux/sdcpp/Qwen3-4B-UD-Q4_K_XL.gguf \
  --vae          models/flux/sdcpp/flux2-vae.safetensors \
  --fa --eager-load --offload-to-cpu \
  --cfg-scale 1.0 --img-cfg-scale 1.0 --guidance 1.0 \
  --sampling-method euler --steps 4
```

**Flux.2 Klein 9B** (`flux_klein_9b`) — same as above with the 9B pair:

```bash
  --diffusion-model models/flux/sdcpp/flux-2-klein-9b-Q4_K_M.gguf \
  --llm          models/flux/sdcpp/Qwen3-8B-UD-Q4_K_XL.gguf \
```

**Flux.1 Kontext** (`flux_kontext`) — different encoders, and guidance `2.5`:

```bash
sd-server --listen-ip 127.0.0.1 --listen-port 1234 \
  --diffusion-model models/flux/sdcpp/kontext/flux1-kontext-dev-Q4_K_M.gguf \
  --clip_l       models/flux/sdcpp/kontext/clip_l.safetensors \
  --t5xxl        models/flux/sdcpp/kontext/t5-v1_1-xxl-encoder-Q4_K_M.gguf \
  --vae          models/flux/sdcpp/kontext/ae.safetensors \
  --fa --eager-load --offload-to-cpu \
  --cfg-scale 1.0 --img-cfg-scale 1.0 --guidance 2.5 \
  --sampling-method euler --steps 8
```

**Which flags actually matter.** MangaTranslator sends `sample_method`, `sample_steps` and
the guidance values in every request, so `--sampling-method`, `--steps`, `--guidance`,
`--cfg-scale` and `--img-cfg-scale` are only startup defaults and are overridden per job —
they are listed above for parity, not because they must match. What you *do* need to get
right is the model quartet (`--diffusion-model`, text encoder, `--vae`) for the inpainting
method you select in MangaTranslator, since the app cannot tell what a remote server has
loaded. `--fa`, `--eager-load`, `--offload-to-cpu` and the cache flags are launch-only and
cannot be set remotely; tune them for your hardware.

**Weights.** Download the quant you want from Hugging Face — diffusion models from
`unsloth/FLUX.2-klein-4B-GGUF`, `unsloth/FLUX.2-klein-9B-GGUF` or
`unsloth/FLUX.1-Kontext-dev-GGUF`; text encoders from `unsloth/Qwen3-4B-GGUF`,
`unsloth/Qwen3-8B-GGUF` (Klein) or `city96/t5-v1_1-xxl-encoder-gguf` (Kontext). The Klein
VAE is `Comfy-Org/flux2-dev` → `split_files/vae/flux2-vae.safetensors`; Kontext uses
`comfyanonymous/flux_text_encoders` → `clip_l.safetensors` and
`Comfy-Org/Lumina_Image_2.0_Repackaged` → `split_files/vae/ae.safetensors`.

**Cache modes.** The managed backend's **Cache Method** maps to these launch flags, where
`W = ceil(steps / 4)`. Append whichever you want to your `sd-server` command:

| Cache Method | Flags |
| --- | --- |
| `none` | *(no cache flags)* |
| `spectrum` | `--cache-mode spectrum --cache-option warmup=W,window=2,stop=0.8` |
| `cache-dit` | `--cache-mode cache-dit --cache-option Fn=4,Bn=0,threshold=0.10,warmup=W --scm-policy dynamic` |
| `taylorseer` | `--cache-mode taylorseer --cache-option Fn=4,Bn=0,warmup=W` |
| `dbcache` | `--cache-mode dbcache --cache-option Fn=8,Bn=0,threshold=0.08,warmup=W` |

> [!WARNING]
> This integration sends no authentication. Keep `sd-server` on localhost or a trusted
> private network, or put it behind an authenticating proxy. Upstream also changes its API
> fairly often, so keep the server version compatible when upgrading.

## Run

### Web UI (Gradio)

- **Portable package:**
  - Windows: Double-click `start-webui.bat` inside the `MangaTranslator` folder
  - Linux/macOS: Run `./start-webui.sh` inside the `MangaTranslator` folder
- **Manual install:**
  - Windows: Run `python app.py --open-browser`

Options: `--models` (default `./models`), `--fonts` (default `./fonts`), `--port` (default `7676`), `--cpu`.
First launch can take ~1–2 minutes.

Once launched, configure your LLM provider in the Config tab, then upload images and click Translate.

### CLI

Examples:

```bash
# Single image, Japanese → English, Google provider
python main.py --input <image_path> \
  --font-dir "fonts/Komika" --provider Google --google-api-key <AI...>

# Batch folder, custom source/target languages, OpenAI-Compatible provider (llama.cpp)
python main.py --input <folder_path> --batch \
  --font-dir "fonts/Komika" \
  --input-language <src_lang> --output-language <tgt_lang> \
  --provider OpenAI-Compatible --openai-compatible-url http://localhost:8080/v1 \
  --output ./output

# Single Image, Japanese → English (Google), OSB text pipeline, custom OSB text font
python main.py --input <image_path> \
  --font-dir "fonts/Komika" --provider Google --google-api-key <AI...> \
  --osb-enable --osb-font-dir "fonts/Clementine"

# OSB inpainting through a separately managed stable-diffusion.cpp server
python main.py --input <image_path> --cleaning-only \
  --osb-enable --osb-inpainting-method flux_klein_4b \
  --osb-flux-backend sdcpp_remote \
  --osb-flux-sdcpp-remote-url http://127.0.0.1:1234

# Cleaning-only mode (no translation/text rendering)
python main.py --input <image_path> --cleaning-only

# Upscaling-only mode (no detection/translation, only upscale)
python main.py --input <image_path> --upscaling-only --image-upscale-mode final --image-upscale-factor 2.0

# Test mode (no translation; render placeholder text)
python main.py --input <image_path> --test-mode

# Full options
python main.py --help
```

## Documentation

- [Hardware Requirements](docs/HARDWARE_REQUIREMENTS.md)
- [Recommended Fonts](docs/FONTS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Updating

### Portable Package

- Windows: Run `update.bat` from the portable package root
- Linux/macOS: Run `./update.sh` from the portable package root

### Manual Install

From the repo root:

```bash
git pull
pip install -r requirements.txt  # Or activate venv first if present
```

## License & credits

- License: Apache-2.0 (see [LICENSE](LICENSE))
- Author: [grinnch](https://github.com/meangrinch)
<details>
<summary><b>ML Models & Libraries</b></summary>

- YOLOv8m Speech Bubble Detector: [kitsumed](https://huggingface.co/kitsumed/yolov8m_seg-speech-bubble)
- Manga109 Speech Bubble Detector: [huyvux3005](https://huggingface.co/huyvux3005/manga109-segmentation-bubble)
- Comic Text and Bubble Detector RT-DETR-v2: [ogkalu](https://huggingface.co/ogkalu/comic-text-and-bubble-detector)
- Manga109 YOLO: [deepghs](https://huggingface.co/deepghs/manga109_yolo)
- AnimeText YOLO: [deepghs](https://huggingface.co/deepghs/AnimeText_yolo)
- SAM 2.1: Segment Anything in Images and Videos: [Meta AI](https://huggingface.co/facebook/sam2.1-hiera-large)
- SAM 3: [Meta AI](https://huggingface.co/facebook/sam3)
- Manga OCR: [kha-white](https://github.com/kha-white/manga-ocr)
- PaddleOCR-VL-1.6: [PaddlePaddle](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6)
- FLUX.1 Kontext: [Black Forest Labs](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev)
- FLUX.2 Klein 4B: [Black Forest Labs](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- FLUX.2 Klein 9B: [Black Forest Labs](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)
- Nunchaku: [Nunchaku AI](https://github.com/nunchaku-ai/nunchaku)
- SDNQ Quants: [Disty0](https://huggingface.co/Disty0)
- Unsloth Quants: [Unsloth](https://huggingface.co/unsloth)
- stable-diffusion.cpp: [leejet](https://github.com/leejet/stable-diffusion.cpp)
- 2x-AnimeSharpV4: [Kim2091](https://huggingface.co/Kim2091/2x-AnimeSharpV4)

</details>
