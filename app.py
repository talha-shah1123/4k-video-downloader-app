import os, re, shutil, tempfile
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from starlette.background import BackgroundTask
import yt_dlp

app = FastAPI(title="4K Video Downloader", docs_url=None, redoc_url=None)
BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

PLATFORMS = {
    "youtube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.watch"),
    "pinterest": ("pinterest.com", "pin.it"),
    "tiktok": ("tiktok.com",),
}

class LinkRequest(BaseModel):
    url: HttpUrl

def platform_for(url: str) -> str:
    host = (urlparse(str(url)).hostname or "").lower().removeprefix("www.")
    for name, domains in PLATFORMS.items():
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    raise HTTPException(status_code=400, detail="Supported links: YouTube, Instagram, Facebook, Pinterest and TikTok.")

def clean_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "", value or "video")
    return value.strip()[:100] or "video"

def ydl_options(**extra):
    opts = {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "socket_timeout": 20, "retries": 1, "fragment_retries": 1,
        "ignoreerrors": False, "nocheckcertificate": False,
        "cachedir": False,
    }
    opts.update(extra)
    return opts

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/info")
def info(req: LinkRequest):
    url = str(req.url)
    platform = platform_for(url)
    try:
        with yt_dlp.YoutubeDL(ydl_options(skip_download=True)) as ydl:
            data = ydl.extract_info(url, download=False)
        if not data:
            raise ValueError("No video information returned.")
        return {
            "title": data.get("title") or "Video",
            "thumbnail": data.get("thumbnail"),
            "duration": int(data.get("duration") or 0),
            "platform": platform.title(),
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not access this video. It may be private, unavailable, region-restricted, or unsupported. Details: {str(exc)[:220]}")

@app.post("/api/download")
def download(req: LinkRequest):
    url = str(req.url)
    platform_for(url)
    temp_dir = Path(tempfile.mkdtemp(prefix="4kvd_"))
    try:
        opts = ydl_options(
            format="best[ext=mp4]/best",
            outtmpl=str(temp_dir / "%(title).100B-%(id)s.%(ext)s"),
            max_filesize=500 * 1024 * 1024,
            merge_output_format="mp4",
        )
        with yt_dlp.YoutubeDL(opts) as ydl:
            data = ydl.extract_info(url, download=True)
            if not data:
                raise ValueError("No media file returned.")
            prepared = Path(ydl.prepare_filename(data))
            candidates = [prepared]
            if prepared.suffix.lower() != ".mp4":
                candidates.insert(0, prepared.with_suffix(".mp4"))
            candidates += list(temp_dir.glob("*"))
            file_path = next((p for p in candidates if p.is_file() and p.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov"}), None)
            if not file_path:
                raise ValueError("The media file could not be prepared.")
        filename = clean_name(data.get("title")) + file_path.suffix.lower()
        return FileResponse(
            file_path, media_type="application/octet-stream", filename=filename,
            background=BackgroundTask(shutil.rmtree, temp_dir, ignore_errors=True)
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=f"Download unavailable for this link. It may be private, restricted, too large (500 MB limit), or unsupported. Details: {str(exc)[:220]}")

app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
