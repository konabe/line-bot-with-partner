from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


def get_display_name_from_line_profile(user_id: str) -> Optional[str]:
    """Fetch displayName for a LINE user via the Messaging API.

    Returns displayName or None on failure. This function is resilient: if
    `requests` is not installed or `LINE_CHANNEL_ACCESS_TOKEN` is not set,
    it will return None.
    """
    try:
        import requests
    except Exception:
        logger.debug("requests not available; skipping profile fetch")
        return None

    token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    if not token or not user_id:
        logger.debug("LINE_CHANNEL_ACCESS_TOKEN not set or empty; skipping profile fetch")
        return None

    try:
        resp = requests.get(
            f"https://api.line.me/v2/bot/profile/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=2,
        )
        if resp.status_code == 200:
            return resp.json().get('displayName')
        logger.debug(f"profile fetch returned status {resp.status_code} for {user_id}")
    except Exception as e:
        logger.error(f"Failed to fetch profile for {user_id}: {e}")
    return None


__all__ = ["get_display_name_from_line_profile"]
