# 4K Video Downloader

A responsive frontend plus a FastAPI/yt-dlp backend. Supports extraction attempts for YouTube, Instagram, Facebook, Pinterest and TikTok, subject to each platform's access controls and current compatibility.

## Run locally
1. Install Python 3.12 and FFmpeg.
2. `pip install -r requirements.txt`
3. `uvicorn app:app --reload`
4. Open http://127.0.0.1:8000

## Deploy
Push this folder to a GitHub repository, then create a Render Blueprint from that repository. `render.yaml` configures a Docker web service. Free hosting may sleep when idle and has limited CPU/memory; video processing can exceed free-tier limits. For production, use a paid server with sufficient bandwidth and storage.

## Important limitations
- This software does not bypass DRM, paywalls, private-account controls, or login requirements.
- Some platforms may block automated access or change their delivery systems. A link may work today and fail later.
- Use only content you own or have permission to download, and comply with platform terms and local law.
- No cookies, account credentials, or DRM workarounds are collected or supported.
- Downloads are limited to 500 MB per file. Temporary files are deleted after the response.
- This starter has basic validation but is not a hardened public service. Add rate limiting, abuse monitoring, request quotas, and stronger resource isolation before exposing it to large public traffic.
