import re
from datetime import datetime
from pathlib import Path

import pytz
import tzlocal
from PIL import Image
from win32com.propsys import propsys, pscon

from utils import modify_file_creation_time

VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"]
WHATSAPP_NAMING_PATTERN = r"(IMG|VID)-\d{8}-WA\d{4}"


def get_media_date(path: Path, skip_patterns: bool = False):
    if path.is_dir():
        raise ValueError("The path must be a file, not a directory.")

    if not skip_patterns:
        if re.fullmatch(path.stem, WHATSAPP_NAMING_PATTERN) is not None:
            return get_whatsapp_date(path)

    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return get_video_date(path)
    return get_picture_date(path)


def get_earliest_date(path: Path):
    if path.is_dir():
        raise ValueError("The path must be a file, not a directory.")
    date_created = datetime.fromtimestamp(path.stat().st_ctime)
    date_modified = datetime.fromtimestamp(path.stat().st_mtime)
    return (
        date_created
        if date_created.timestamp() < date_modified.timestamp()
        else date_modified
    )


def get_picture_date(path: Path):
    if path.is_dir():
        raise ValueError("The path must be a file, not a directory.")
    try:
        exif = Image.open(path)._getexif()
        if not exif:
            date_taken = None
        date_taken = datetime.strptime(exif[36867], "%Y:%m:%d %H:%M:%S")
    except Exception:
        date_taken = None
    if date_taken:
        return date_taken
    else:
        return get_earliest_date(path)


def get_video_date(path: Path):
    if path.is_dir():
        raise ValueError("The path must be a file, not a directory.")
    try:
        properties = propsys.SHGetPropertyStoreFromParsingName(str(path))
        media_date = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
        if not isinstance(media_date, datetime):
            media_date = datetime.fromtimestamp(int(media_date))
            media_date = media_date.replace(tzinfo=pytz.timezone("UTC"))
        return media_date.astimezone(tzlocal.get_localzone())
    except Exception:
        return get_picture_date(path)


def get_whatsapp_date(path: Path):
    if path.is_dir():
        raise ValueError("The path must be a file, not a directory.")
    try:
        time = datetime.strptime(path.name.split("-")[1], "%Y%m%d")
        modify_file_creation_time(path, time)
        return time
    except Exception:
        return get_media_date(path, True)