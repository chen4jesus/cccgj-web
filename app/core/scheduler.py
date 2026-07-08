"""
APScheduler cron job -- refreshes YouTube playlist cache every 24 hours.
Exposes get_cached_videos() for use in route handlers.
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger    # type: ignore
from app.core.youtube_service import fetch_latest_videos

logger = logging.getLogger(__name__)

# In-memory cache
_cache: dict = {
    "videos": [],
    "last_updated": None,
}

scheduler = AsyncIOScheduler()

PLAYLIST_ID = "PLQHQ_Dw8UrH84Kfq_o2Bkvg5KoZffRkPn"
MAX_VIDEOS = 6


async def refresh_youtube_cache():
    """Fetch latest videos from YouTube and update the in-memory cache."""
    logger.info("Refreshing YouTube playlist cache...")
    try:
        videos = await fetch_latest_videos(PLAYLIST_ID, MAX_VIDEOS)
        if videos:
            _cache["videos"] = videos
            from datetime import datetime, timezone
            _cache["last_updated"] = datetime.now(timezone.utc).isoformat()
            logger.info("YouTube cache updated: %d videos", len(videos))
        else:
            logger.warning("YouTube cache refresh returned no videos; keeping previous cache.")
    except Exception as exc:
        logger.error("YouTube cache refresh failed: %s", exc)


def get_cached_videos() -> list:
    """Return the currently cached list of video dicts."""
    return _cache["videos"]


def start_scheduler():
    """
    Register the cron job and start the scheduler.
    Call this from the FastAPI startup event.
    """
    scheduler.add_job(
        refresh_youtube_cache,
        trigger=IntervalTrigger(hours=1),
        id="youtube_refresh",
        name="Refresh YouTube Playlist Cache",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("APScheduler started -- YouTube refresh every hour.")
    # Fire immediately on startup (non-blocking)
    asyncio.ensure_future(refresh_youtube_cache())
