"""Optional apparent-age estimation using DeepFace."""
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False


def estimate_age(filepath, face_location=None):
    if not DEEPFACE_AVAILABLE:
        return None
    try:
        analysis = DeepFace.analyze(
            img_path=filepath,
            actions=["age"],
            enforce_detection=False,
            silent=True,
        )
        if isinstance(analysis, list):
            analysis = analysis[0]
        return int(analysis.get("age"))
    except Exception:
        return None