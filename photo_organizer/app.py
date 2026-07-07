"""Flask web UI for browsing/filtering photos."""
import os
from flask import Flask, render_template, request, send_file, abort

from organizer import db as dbmod

app = Flask(__name__)
dbmod.init_db()


@app.route("/")
def index():
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    person_name = request.args.get("person") or None
    min_years = request.args.get("min_years")
    max_years = request.args.get("max_years")
    min_years = float(min_years) if min_years else None
    max_years = float(max_years) if max_years else None

    with dbmod.get_conn() as conn:
        photos = dbmod.query_photos(
            conn,
            date_from=f"{date_from} 00:00:00".replace("-", ":") if date_from else None,
            date_to=f"{date_to} 23:59:59".replace("-", ":") if date_to else None,
            person_name=person_name,
            min_years_old=min_years,
            max_years_old=max_years,
        )
        persons = conn.execute("SELECT name FROM persons ORDER BY name").fetchall()

    return render_template(
        "index.html",
        photos=photos,
        persons=[p["name"] for p in persons],
        filters=request.args,
    )


@app.route("/photo/<int:photo_id>")
def photo_file(photo_id):
    with dbmod.get_conn() as conn:
        row = conn.execute("SELECT filepath FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if not row or not os.path.exists(row["filepath"]):
        abort(404)
    return send_file(row["filepath"])


if __name__ == "__main__":
    app.run(debug=True)