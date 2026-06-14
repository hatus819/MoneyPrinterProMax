# Money Printer Pro Max 💸 — Automated Short-Video Generator

**English** | [Português (Brasil)](README.pt-BR.md)

Turn a text topic into a finished, captioned vertical (or landscape) short video — script, voiceover, stock footage, subtitles, and ready-to-paste metadata, all generated automatically.

This is an enhanced fork of [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) with several added features (see [Features](#-features)).

> ⚠️ **It does not upload anywhere for you.** Each video is saved as a file you publish yourself. See [Important notes](#-important-notes).

---

## ✨ Features

- **Topic → full video** using a local LLM (Ollama) for the script — no paid AI API required.
- **Multiple aspect ratios**: `9:16` (Shorts/TikTok/Reels), `16:9` (YouTube), `1:1` (Instagram), `4:5` (feed).
- **Minimum video length** control — guarantee videos are at least N seconds (e.g. 60s).
- **Auto-generated metadata** — every video gets a `.txt` with a Title, Description, Hashtags, and Keywords, ready to paste when you publish.
- **Accurate captions** via AssemblyAI (optional) or local timing.
- **Batch mode** — queue a whole list of topics from a text file and walk away.
- **Persistent output** — every video is saved with a unique name in `output/` so jobs never overwrite each other.
- **Reliable queue** — a database-backed job queue (Postgres) with a separate worker, so it survives restarts.

## 🧱 How it works

```
Your topic → Ollama (script) → Pexels (stock footage) → TikTok TTS (voiceover)
          → subtitles → video assembly (9:16/16:9/…) → output/<name>.mp4 + <name>.txt
```

Components run in Docker: a **frontend** (web UI), a **backend** API, a **worker** that renders videos, and **Postgres** for the queue. **Ollama** runs on your host machine.

---

## ✅ Prerequisites

| Tool | Why | Notes |
|---|---|---|
| **Docker + Docker Compose** | Runs the whole stack | [Install Docker](https://docs.docker.com/get-docker/) |
| **Ollama** | Generates the script locally | [Install Ollama](https://ollama.com/download) |
| **Pexels API key** | Stock footage (free) | https://www.pexels.com/api/ |
| **TikTok `sessionid`** | Text-to-speech voice (free) | From your browser cookies on tiktok.com |
| **AssemblyAI API key** | *Optional* — better caption timing (free tier) | https://www.assemblyai.com/ |

> ImageMagick and FFmpeg are **already included** in the Docker image — you don't need to install them.

---

## 🚀 Setup

### 1. Clone and configure

```bash
git clone <your-repo-url> MoneyPrinter
cd MoneyPrinter
cp .env.example .env
```

Edit `.env` and fill in:

```env
PEXELS_API_KEY="your_pexels_key"
TIKTOK_SESSION_ID="your_tiktok_sessionid"
ASSEMBLY_AI_API_KEY=""          # optional, for better captions

# Lets the Docker containers reach Ollama running on your host:
OLLAMA_BASE_URL="http://host.docker.internal:11434"
OLLAMA_MODEL="llama3.1:8b"
```

**How to get the keys:**
- **Pexels:** sign up at https://www.pexels.com/api/ → copy "Your API Key".
- **TikTok `sessionid`:** log in at tiktok.com → open DevTools (`F12` / `Cmd+Opt+I`) → **Application → Cookies → tiktok.com** → copy the value of the `sessionid` cookie.

### 2. Start Ollama (on your host)

Ollama must listen on all interfaces so the Docker containers can reach it:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve     # leave this running in one terminal
ollama pull llama3.1:8b                     # in another terminal, once
```

> 🔒 Binding Ollama to `0.0.0.0` exposes it on your local network. That's required for Docker → host access. On a trusted machine this is fine; otherwise restrict it with your firewall.

### 3. Start the app

```bash
docker compose up -d --build
```

The **first build takes a few minutes** (it compiles ImageMagick). After it's up:

- **Web UI:** http://localhost:8001
- **Backend API:** http://localhost:8080

To stop: `docker compose down`.

---

## 🎬 Usage

### Option A — Web UI (single video)

1. Open http://localhost:8001
2. Enter a **video subject**.
3. Expand the options and set:
   - **Aspect Ratio** — 9:16 / 16:9 / 1:1 / 4:5
   - **Min Duration** — minimum length in seconds (e.g. `60`; set `0` to use the Paragraphs count instead)
   - **Subtitle position / color**, **Threads** (render speed), etc.
4. Pick the **Ollama model** from the dropdown.
5. Click **Generate** and watch the live log.
6. The finished video + its metadata appear in the [`output/`](output/) folder.

### Option B — Batch mode (many videos)

Edit `topics.txt` (one topic per line) and run:

```bash
python3 batch_generate.py
```

`topics.txt` format:

```text
# Lines starting with '#' are ignored
3 surprising facts about the deep ocean
The history of coffee in 60 seconds
The science of why we dream | 16:9      # optional per-line aspect override
```

Useful flags:

```bash
python3 batch_generate.py mytopics.txt \
  --aspect 16:9 \          # default aspect for all lines
  --min-duration 60 \      # minimum seconds per video
  --threads 6 \            # render threads
  --voice en_us_001 \
  --wait                   # wait for each to finish (shows result paths)
```

Videos are queued and rendered **one at a time** in the background — close your laptop and come back to a full `output/` folder.

---

## 📁 Output

Each generated video produces two files in `output/`:

```
the-history-of-coffee-6517a129.mp4   ← the video
the-history-of-coffee-6517a129.txt   ← TITLE / DESCRIPTION / HASHTAGS / KEYWORDS
```

Open the `.txt` and copy-paste the title, description, and hashtags when you publish.

---

## ⚙️ Configuration reference (`.env`)

| Variable | Required | Description |
|---|---|---|
| `PEXELS_API_KEY` | ✅ | Pexels stock-video API key |
| `TIKTOK_SESSION_ID` | ✅ | TikTok `sessionid` cookie (for TTS voice) |
| `OLLAMA_BASE_URL` | ✅ (Docker) | `http://host.docker.internal:11434` so containers reach host Ollama |
| `OLLAMA_MODEL` | – | Fallback model (default `llama3.1:8b`) |
| `ASSEMBLY_AI_API_KEY` | – | Optional; enables AssemblyAI captions |
| `IMAGEMAGICK_BINARY` | – | Leave empty (handled inside Docker) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | – | Postgres defaults |
| `DATABASE_URL` | – | Leave empty to use the bundled Postgres |

---

## 🛠️ Troubleshooting

- **UI shows no models / "could not connect to Ollama":** make sure Ollama is running with `OLLAMA_HOST=0.0.0.0:11434` and that `OLLAMA_BASE_URL` in `.env` is `http://host.docker.internal:11434`. Test: `curl http://localhost:8080/api/models`.
- **A render fails at the end / captions error:** usually a subtitle/timing edge case — try a different topic or set an `ASSEMBLY_AI_API_KEY`.
- **Voiceover fails:** TikTok TTS is region-sensitive; refresh your `TIKTOK_SESSION_ID` (it expires) or use a US-based session.
- **Renders are slow:** longer videos take longer — the bottleneck is burning subtitles frame-by-frame, so render time scales with video length more than with `Threads`.
- **Check the queue / logs:** `docker compose logs -f worker`.

---

## 📝 Important notes

- **No automatic uploading.** The app produces a file; you publish it manually. Automated uploading to TikTok via session cookies violates their Terms of Service and risks account bans, so it is intentionally not included.
- **Content quality & platform rules.** Platforms increasingly limit mass-produced, repetitive AI content. Lean into a specific niche and vary your format.
- **Voice quality.** The built-in TikTok TTS is robotic. For production quality, consider integrating a licensed TTS provider.

---

## 🙏 Credits & License

- Based on [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter).
- Licensed under the **MIT License** — see [`LICENSE`](LICENSE). You are free to use, modify, and distribute, including commercially.
