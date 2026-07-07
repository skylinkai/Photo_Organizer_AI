"""Command line interface for the photo organizer."""
import argparse

from organizer import db as dbmod
from organizer.scanner import scan_folder


def cmd_scan(args):
    scan_folder(args.folder, estimate_ages=args.estimate_ages)


def cmd_label(args):
    dbmod.init_db()
    with dbmod.get_conn() as conn:
        unlabeled = dbmod.get_unlabeled_faces(conn)
        if not unlabeled:
            print("No unlabeled faces found. Run `scan` first.")
            return
        print(f"{len(unlabeled)} unlabeled face(s) found.\n")

        for face in unlabeled:
            photo = conn.execute(
                "SELECT filepath FROM photos WHERE id = ?", (face["photo_id"],)
            ).fetchone()
            print(f"Face at {face['location']} in: {photo['filepath']}")
            name = input("  Enter name (or blank to skip, 'q' to quit labeling): ").strip()
            if name.lower() == "q":
                break
            if not name:
                continue
            person_id = dbmod.get_or_create_person(conn, name)
            dbmod.label_face(conn, face["id"], person_id)
            print(f"  Labeled as '{name}'.\n")


def main():
    parser = argparse.ArgumentParser(description="Smart Photo Organizer CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a folder and index photos")
    scan_p.add_argument("folder", help="Path to folder containing photos")
    scan_p.add_argument(
        "--estimate-ages", action="store_true",
        help="Also estimate apparent age of detected faces (slower, needs deepface)"
    )
    scan_p.set_defaults(func=cmd_scan)

    label_p = sub.add_parser("label", help="Interactively label detected faces")
    label_p.set_defaults(func=cmd_label)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()