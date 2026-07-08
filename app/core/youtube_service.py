"""
YouTube service -- fetches playlist metadata via the official YouTube Data API v3.

The public Atom/RSS feed and HTML scraping both proved unreliable on some
cloud/VPS hosts: YouTube's anti-scraping layer returns a 404 for the feed
endpoint, and serves an emptied-out interstitial page for watch pages, from
IPs it flags as non-browser traffic. The Data API is authenticated via an API
key rather than IP reputation, so it isn't subject to that blocking.

Two calls are made per refresh:
  1. playlistItems.list -- get the video IDs currently in the playlist.
  2. videos.list         -- get each video's real snippet (title, channel,
                             and its original upload publishedAt). Note that
                             playlistItems.snippet.publishedAt is the date the
                             item was *added to the playlist*, not the video's
                             upload date, so it can't be used directly.

Results are sorted by true upload date (newest first) before trimming to
max_results, since playlist ordering doesn't guarantee that.

Requires YOUTUBE_API_KEY to be set (see app.core.config.Settings).
"""
import asyncio
import json
import logging
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yt_fetch")

_PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# How many playlist items to pull before sorting by real upload date and
# trimming to max_results -- covers channels that don't keep the playlist in
# strict newest-first order.
_PLAYLIST_SCAN_SIZE = 20


def _fmt_date(raw: str) -> str:
    """
    Parse an ISO-8601 timestamp (e.g. '2026-06-28T05:00:10Z')
    and return a human-readable string like 'Jun 28, 2026'.
    """
    try:
        clean = raw[:19]  # "2026-06-28T05:00:10"
        dt = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        # strftime "%d" gives zero-padded day; strip leading zero manually
        day = str(dt.day)
        return dt.strftime(f"%b {day}, %Y")
    except Exception:
        return raw


def _api_get(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{query}",
        headers={"User-Agent": "Mozilla/5.0 (compatible; CCCGJBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _sync_fetch(playlist_id: str, max_results: int) -> list:
    """
    Fetch playlist metadata via the YouTube Data API v3.
    Returns up to max_results videos, sorted newest-first by upload date.
    """
    settings = get_settings()
    api_key = settings.YOUTUBE_API_KEY
    if not api_key:
        logger.error("YOUTUBE_API_KEY is not configured; cannot fetch videos.")
        return []

    try:
        playlist_data = _api_get(_PLAYLIST_ITEMS_URL, {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": str(_PLAYLIST_SCAN_SIZE),
            "key": api_key,
        })
    except Exception as exc:
        logger.error("playlistItems.list failed for playlist %s: %s", playlist_id, exc)
        return []

    video_ids = []
    for item in playlist_data.get("items", []):
        video_id = (item.get("snippet", {}).get("resourceId", {}) or {}).get("videoId", "")
        if video_id:
            video_ids.append(video_id)

    if not video_ids:
        logger.warning("playlistItems.list returned no videos for playlist %s", playlist_id)
        return []

    try:
        videos_data = _api_get(_VIDEOS_URL, {
            "part": "snippet",
            "id": ",".join(video_ids),
            "key": api_key,
        })
    except Exception as exc:
        logger.error("videos.list failed for playlist %s: %s", playlist_id, exc)
        return []

    videos = []
    for item in videos_data.get("items", []):
        video_id = item.get("id", "")
        snippet = item.get("snippet", {})
        title = snippet.get("title", "Untitled")
        published = snippet.get("publishedAt", "")
        channel = snippet.get("channelTitle") or "CCCGJ Media"

        if not video_id:
            continue

        videos.append({
            "title":         title,
            "video_id":      video_id,
            "url":           f"https://www.youtube.com/watch?v={video_id}",
            "published_at":  _fmt_date(published) if published else "",
            "_published_raw": published,
            "channel_title": channel,
        })

    videos.sort(key=lambda v: v["_published_raw"], reverse=True)
    for v in videos:
        del v["_published_raw"]

    videos = videos[:max_results]
    logger.info("Data API fetch returned %d videos for playlist %s", len(videos), playlist_id)
    return videos


async def fetch_latest_videos(playlist_id: str, max_results: int = 6) -> list:
    """
    Async wrapper -- runs the blocking fetch in a thread pool so FastAPI
    event loop is never stalled.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_fetch, playlist_id, max_results)
