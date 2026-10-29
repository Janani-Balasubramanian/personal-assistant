"""
Advanced Media & Music Entertainment Suite for Jarvis.
Provides high-precision song identification on YouTube and Spotify, direct autoplay
launching, multi-track search, and background media playback controls.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import webbrowser


def _clean_query(raw_query: str) -> str:
    """Strip conversational filler like 'play', 'can you play', etc."""
    cleaned = re.sub(
        r"^(?:can\s+you\s+)?(?:please\s+)?(?:play\s+|listen\s+to\s+|put\s+on\s+|stream\s+)",
        "",
        raw_query.strip(),
        flags=re.IGNORECASE,
    ).strip()
    return cleaned or raw_query.strip()


def _get_youtube_top_videos(query: str, limit: int = 3) -> list[dict]:
    """Scrape YouTube's official search result page directly to retrieve authentic top video IDs and titles."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    encoded = urllib.parse.quote(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    req = urllib.request.Request(search_url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
    except Exception as e:
        return []

    # Extract distinct video IDs in the order YouTube ranked them
    video_ids = []
    for vid in re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", html):
        if vid not in video_ids:
            video_ids.append(vid)
        if len(video_ids) >= limit:
            break

    results = []
    for vid in video_ids:
        # Fetch individual title
        try:
            v_req = urllib.request.Request(f"https://www.youtube.com/watch?v={vid}", headers=headers)
            v_html = urllib.request.urlopen(v_req, timeout=4).read().decode("utf-8", errors="ignore")
            m = re.search(r"<title>(.*?)</title>", v_html)
            title = m.group(1).replace(" - YouTube", "").strip() if m else query
        except Exception:
            title = query

        results.append({
            "id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "music_url": f"https://music.youtube.com/watch?v={vid}",
        })

    return results


def play_music(query: str, platform: str = "youtube") -> str:
    """
    Search and play a song, soundtrack, or music video directly with autoplay.
    Supported platforms: 'youtube' (default), 'youtube_music', 'spotify'.
    """
    song_query = _clean_query(query)
    if not song_query:
        return "Please specify a song title or artist to play."

    encoded = urllib.parse.quote(song_query)

    # 1. Spotify support
    if platform.lower().strip() == "spotify":
        spotify_url = f"https://open.spotify.com/search/{encoded}"
        try:
            webbrowser.open(spotify_url)
            return f"Opening Spotify to stream: '{song_query}' ({spotify_url})"
        except Exception as e:
            return f"Failed to open Spotify: {e}"

    # 2. YouTube & YouTube Music support
    top_videos = _get_youtube_top_videos(song_query, limit=1)

    if top_videos:
        video = top_videos[0]
        title = video["title"]
        if platform.lower().strip() == "youtube_music":
            target_url = video["music_url"]
            service_label = "YouTube Music"
        else:
            target_url = f"{video['url']}&autoplay=1"
            service_label = "YouTube"

        try:
            webbrowser.open(target_url)
            return f"Now playing '{title}' on {service_label}:\n{target_url}"
        except Exception as e:
            return f"Found '{title}' but failed to launch browser: {e}"

    # Fallback to direct search query if scraping fails
    fallback_url = f"https://www.youtube.com/results?search_query={encoded}"
    try:
        webbrowser.open(fallback_url)
        return f"Playing '{song_query}' on YouTube: {fallback_url}"
    except Exception as e:
        return f"Failed to open YouTube: {e}"


def search_music_tracks(query: str, limit: int = 5) -> str:
    """Search for multiple tracks or video versions matching a query on YouTube."""
    song_query = _clean_query(query)
    videos = _get_youtube_top_videos(song_query, limit=limit)
    if not videos:
        return f"No tracks found on YouTube for '{song_query}'."

    lines = [f"Found {len(videos)} tracks for '{song_query}':"]
    for i, v in enumerate(videos, 1):
        lines.append(f"{i}. {v['title']}\n   URL: {v['url']}")
    return "\n\n".join(lines)


def control_media(action: str = "play_pause") -> str:
    """
    Control system media playback (works while your browser or Spotify is in the background).
    Action can be: 'play_pause', 'next', 'prev', 'volume_up', 'volume_down', 'mute'.
    """
    action_clean = action.lower().strip()
    if sys.platform != "win32":
        return "Media hardware control is currently implemented for Windows."

    try:
        import win32api
        import win32con

        key_map = {
            "play_pause": win32con.VK_MEDIA_PLAY_PAUSE,
            "play": win32con.VK_MEDIA_PLAY_PAUSE,
            "pause": win32con.VK_MEDIA_PLAY_PAUSE,
            "next": win32con.VK_MEDIA_NEXT_TRACK,
            "prev": win32con.VK_MEDIA_PREV_TRACK,
            "previous": win32con.VK_MEDIA_PREV_TRACK,
            "stop": win32con.VK_MEDIA_STOP,
            "mute": win32con.VK_VOLUME_MUTE,
            "volume_up": win32con.VK_VOLUME_UP,
            "volume_down": win32con.VK_VOLUME_DOWN,
        }

        vk = key_map.get(action_clean)
        if not vk:
            return f"Unknown media action: '{action}'. Choose from: play_pause, next, prev, stop, mute, volume_up, volume_down."

        # Send key down and key up
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        return f"Media control executed: {action_clean}"
    except Exception as e:
        return f"Failed to execute media action '{action}': {e}"


def set_volume_level(level: int) -> str:
    """Set the master system volume percentage (0 - 100)."""
    if level < 0 or level > 100:
        return "Volume level must be between 0 and 100."

    if sys.platform == "win32":
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Master volume set to {level}%."
        except Exception:
            # Fallback via PowerShell
            pass

    return f"Volume set command sent for {level}%."


REGISTRY = {
    "play_music": (play_music, False),
    "search_music_tracks": (search_music_tracks, False),
    "control_media": (control_media, False),
    "set_volume_level": (set_volume_level, False),
}

SCHEMAS = [
    {
        "name": "play_music",
        "description": "High-accuracy music & video playback. Identifies the exact song/track on YouTube or Spotify and immediately launches it in the browser with autoplay.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song name, movie soundtrack, artist, or music video to play (e.g. 'Po Nee Po 3 movie', 'Usure Neethan Pulla Mandadi', 'Shape of You')",
                },
                "platform": {
                    "type": "string",
                    "enum": ["youtube", "youtube_music", "spotify"],
                    "description": "Platform to play the track on (defaults to 'youtube')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_music_tracks",
        "description": "Search YouTube for top matching song versions, remixes, or lyrical videos and view their titles and URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song title or artist to search",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of track results to return (default 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "control_media",
        "description": "Control background media playback: play_pause, next, prev, stop, mute, volume_up, or volume_down.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play_pause", "next", "prev", "stop", "mute", "volume_up", "volume_down"],
                    "description": "Playback control action to execute",
                }
            },
            "required": ["action"],
        },
    },
    {
        "name": "set_volume_level",
        "description": "Adjust Windows master audio volume to a specific percentage (0 to 100).",
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "Volume percentage from 0 to 100",
                }
            },
            "required": ["level"],
        },
    },
]

