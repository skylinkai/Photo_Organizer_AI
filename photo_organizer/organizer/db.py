"""SQLite database layer for the photo organizer."""
import sqlite3
from contextlib import contextmanager

DB_PATH = "photos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE NOT NULL,
    date_taken TEXT,
    file_mtime TEXT,
    gps_lat REAL,
    gps_lon REAL,
    width INTEGER,
    height INTEGER
);

CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_id INTEGER NOT NULL,
    encoding BLOB NOT NULL,
    location TEXT,
    person_id INTEGER,
    estimated_age INTEGER,
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id)
);

CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
"""


@contextmanager
def get_conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH):
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


def upsert_photo(conn, filepath, date_taken, file_mtime, gps_lat, gps_lon, width, height):
    cur = conn.execute("SELECT id FROM photos WHERE filepath = ?", (filepath,))
    row = cur.fetchone()
    if row:
        conn.execute(
            """UPDATE photos SET date_taken=?, file_mtime=?, gps_lat=?, gps_lon=?,
               width=?, height=? WHERE id=?""",
            (date_taken, file_mtime, gps_lat, gps_lon, width, height, row["id"]),
        )
        return row["id"]
    cur = conn.execute(
        """INSERT INTO photos (filepath, date_taken, file_mtime, gps_lat, gps_lon, width, height)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (filepath, date_taken, file_mtime, gps_lat, gps_lon, width, height),
    )
    return cur.lastrowid


def insert_face(conn, photo_id, encoding_blob, location_str, estimated_age=None, person_id=None):
    cur = conn.execute(
        """INSERT INTO faces (photo_id, encoding, location, estimated_age, person_id)
           VALUES (?, ?, ?, ?, ?)""",
        (photo_id, encoding_blob, location_str, estimated_age, person_id),
    )
    return cur.lastrowid


def get_or_create_person(conn, name):
    cur = conn.execute("SELECT id FROM persons WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO persons (name) VALUES (?)", (name,))
    return cur.lastrowid


def get_unlabeled_faces(conn):
    return conn.execute(
        "SELECT * FROM faces WHERE person_id IS NULL"
    ).fetchall()


def label_face(conn, face_id, person_id):
    conn.execute("UPDATE faces SET person_id = ? WHERE id = ?", (person_id, face_id))


def query_photos(conn, date_from=None, date_to=None, person_name=None, min_years_old=None, max_years_old=None):
    sql = "SELECT DISTINCT p.* FROM photos p"
    joins = []
    wheres = []
    params = []

    if person_name:
        joins.append("JOIN faces f ON f.photo_id = p.id JOIN persons pe ON pe.id = f.person_id")
        wheres.append("pe.name = ?")
        params.append(person_name)

    if date_from:
        wheres.append("p.date_taken >= ?")
        params.append(date_from)
    if date_to:
        wheres.append("p.date_taken <= ?")
        params.append(date_to)

    if joins:
        sql += " " + " ".join(joins)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY p.date_taken DESC"

    rows = conn.execute(sql, params).fetchall()

    if min_years_old is not None or max_years_old is not None:
        from datetime import datetime
        filtered = []
        now = datetime.now()
        for r in rows:
            if not r["date_taken"]:
                continue
            try:
                dt = datetime.strptime(r["date_taken"], "%Y:%m:%d %H:%M:%S")
            except ValueError:
                continue
            years_old = (now - dt).days / 365.25
            if min_years_old is not None and years_old < min_years_old:
                continue
            if max_years_old is not None and years_old > max_years_old:
                continue
            filtered.append(r)
        return filtered

    return rows