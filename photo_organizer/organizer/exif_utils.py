"""EXIF extraction utilities: date taken, GPS coordinates, dimensions.

Author: arindcha
"""
import os
from datetime import datetime
from PIL import Image, ExifTags

DATE_TAG = "DateTimeOriginal"
GPS_TAG = "GPSInfo"


def _get_exif_dict(img):
    try:
        exif_raw = img._getexif()
    except AttributeError:
        exif_raw = None
    if not exif_raw:
        return {}
    return {ExifTags.TAGS.get(k, k): v for k, v in exif_raw.items()}


def _convert_gps(gps_info):
    def to_deg(value):
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    try:
        lat = to_deg(gps_info[2])
        if gps_info[1] == "S":
            lat = -lat
        lon = to_deg(gps_info[4])
        if gps_info[3] == "W":
            lon = -lon
        return lat, lon
    except (KeyError, IndexError, TypeError):
        return None, None


def extract_metadata(filepath):
    result = {
        "date_taken": None,
        "gps_lat": None,
        "gps_lon": None,
        "width": None,
        "height": None,
    }
    try:
        with Image.open(filepath) as img:
            result["width"], result["height"] = img.size
            exif = _get_exif_dict(img)

            date_taken = exif.get(DATE_TAG) or exif.get("DateTime")
            if date_taken:
                result["date_taken"] = date_taken

            gps_info = exif.get(GPS_TAG)
            if gps_info:
                lat, lon = _convert_gps(gps_info)
                result["gps_lat"], result["gps_lon"] = lat, lon
    except Exception:
        pass

    if not result["date_taken"]:
        mtime = os.path.getmtime(filepath)
        result["date_taken"] = datetime.fromtimestamp(mtime).strftime("%Y:%m:%d %H:%M:%S")

    return result


def get_file_mtime(filepath):
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime("%Y:%m:%d %H:%M:%S")