"""Orchestrates scanning a folder into the database."""
import os
from tqdm import tqdm

from . import db as dbmod
from . import exif_utils
from . import face_utils
from . import age_utils

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"}


def find_images(folder):
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                yield os.path.join(root, name)


def scan_folder(folder, db_path=dbmod.DB_PATH, estimate_ages=False):
    dbmod.init_db(db_path)
    filepaths = list(find_images(folder))
    print(f"Found {len(filepaths)} image(s) in {folder}")

    with dbmod.get_conn(db_path) as conn:
        known_faces = []
        rows = conn.execute(
            "SELECT person_id, encoding FROM faces WHERE person_id IS NOT NULL"
        ).fetchall()
        for r in rows:
            known_faces.append((r["person_id"], face_utils.blob_to_encoding(r["encoding"])))

        for filepath in tqdm(filepaths, desc="Scanning"):
            meta = exif_utils.extract_metadata(filepath)
            mtime = exif_utils.get_file_mtime(filepath)

            photo_id = dbmod.upsert_photo(
                conn,
                filepath=filepath,
                date_taken=meta["date_taken"],
                file_mtime=mtime,
                gps_lat=meta["gps_lat"],
                gps_lon=meta["gps_lon"],
                width=meta["width"],
                height=meta["height"],
            )

            faces = face_utils.detect_faces(filepath)
            for encoding, location in faces:
                person_id = face_utils.match_or_new_cluster(encoding, known_faces)
                age = age_utils.estimate_age(filepath) if estimate_ages else None
                blob = face_utils.encoding_to_blob(encoding)
                dbmod.insert_face(
                    conn,
                    photo_id=photo_id,
                    encoding_blob=blob,
                    location_str=str(location),
                    estimated_age=age,
                    person_id=person_id,
                )
                if person_id is not None:
                    known_faces.append((person_id, encoding))

    print("Scan complete.")