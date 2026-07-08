"""
YouTube service -- fetches playlist metadata via the YouTube public Atom/RSS feed.

YouTube exposes a public feed (no API key required) at:
  https://www.youtube.com/feeds/videos.xml?playlist_id=<ID>

This feed returns the 15 most recent videos with title, publish date, video ID,
and channel name, parsed with Python stdlib xml.etree -- no extra dependencies,
and no per-video requests that YouTube can bot-check or rate-limit (which is
what caused published dates to intermittently go missing under a yt-dlp-based
fallback on some hosts).

The fetch is offloaded to a ThreadPoolExecutor so it never blocks the async
FastAPI event loop.
"""
import asyncio
import logging
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yt_fetch")

# YouTube Atom feed namespaces
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt":   "http://www.youtube.com/xml/schemas/2015",
    "media":"http://search.yahoo.com/mrss/",
}

_FEED_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"


def _fmt_date(raw: str) -> str:
    """
    Parse an ISO-8601 timestamp (e.g. '2026-06-28T05:00:10+00:00')
    and return a human-readable string like 'Jun 28, 2026'.
    """
    try:
        # Python 3.11+ handles timezone offset natively; strip offset for 3.9/3.10
        clean = raw[:19]  # "2026-06-28T05:00:10"
        dt = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        # strftime "%d" gives zero-padded day; strip leading zero manually
        day = str(dt.day)
        return dt.strftime(f"%b {day}, %Y")
    except Exception:
        return raw


def _sync_fetch_rss(playlist_id: str, max_results: int) -> list:
    """
    Fetch playlist metadata from the YouTube Atom feed (stdlib only).
    Returns up to max_results videos sorted newest-first.
    """
    url = _FEED_URL.format(playlist_id=playlist_id)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CCCGJBot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_bytes = resp.read()
    except Exception as exc:
        logger.error("RSS fetch failed for playlist %s: %s", playlist_id, exc)
        return []

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.error("RSS XML parse error: %s", exc)
        return []
 
    videos = []
    for entry in root.findall("atom:entry", _NS)[:max_results]:
        video_id = (entry.findtext("yt:videoId", namespaces=_NS) or "").strip()
        title     = (entry.findtext("atom:title", namespaces=_NS) or "Untitled").strip()
        published = (entry.findtext("atom:published", namespaces=_NS) or "").strip()
        channel   = (
            entry.findtext("atom:author/atom:name", namespaces=_NS) or "CCCGJ Media"
        ).strip()

        if not video_id:
            continue

        videos.append({
            "title":         title,
            "video_id":      video_id,
            "url":           f"https://www.youtube.com/watch?v={video_id}",
            "published_at":  _fmt_date(published) if published else "",
            "channel_title": channel,
        })

    logger.info("RSS fetch returned %d videos for playlist %s", len(videos), playlist_id)
    return videos


def _sync_fetch(playlist_id: str, max_results: int) -> list:
    """Primary entry point: fetch from the YouTube Atom feed."""
    return _sync_fetch_rss(playlist_id, max_results)


async def fetch_latest_videos(playlist_id: str, max_results: int = 6) -> list:
    """
    Async wrapper -- runs the blocking fetch in a thread pool so FastAPI
    event loop is never stalled.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_fetch, playlist_id, max_results)

