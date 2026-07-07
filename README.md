# Smart Photo Organizer

**Author:** arindcha

A local, privacy-first photo organizer that scans a folder of photos and filters by date taken, person (face recognition), and photo age.

## Features
- Extracts EXIF date/time and GPS coordinates
- Detects and clusters faces
- Estimates apparent age of people (optional, via DeepFace)
- Stores everything in a local SQLite database
- Flask web UI to browse/filter photos

## Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## Usage
python cli.py scan "path\to\photos"
python cli.py label
python app.py
