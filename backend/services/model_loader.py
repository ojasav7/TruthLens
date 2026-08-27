"""Model loader -- loads each model independently at startup.

Ponytail: deferred imports so torch/cv2 are only loaded when load_all_models() runs.
"""

import sys
import traceback

_models = {"nlp": None, "image": None, "video": None, "audio": None}


def get_nlp_model(): return _models["nlp"]
def get_image_model(): return _models["image"]
def get_video_model(): return _models["video"]
def get_audio_model(): return _models["audio"]


def load_all_models():
    # Deferred imports — torch/cv2 are heavy and may not be installed in test env
    from models.nlp.model import FakeNewsClassifier
    from models.image.model import ImageDeepfakeDetector
    from models.video.model import VideoDeepfakeDetector
    from models.audio.model import AudioDeepfakeDetector

    for name, cls, key in [
        ("NLP", FakeNewsClassifier, "nlp"),
        ("Image", ImageDeepfakeDetector, "image"),
        ("Video", VideoDeepfakeDetector, "video"),
        ("Audio", AudioDeepfakeDetector, "audio"),
    ]:
        try:
            print(f"[Loading] {name} model...")
            _models[key] = cls()
            print(f"[OK] {name} model loaded.")
        except Exception as e:
            print(f"[Error] {name}: {e}")
            traceback.print_exc(file=sys.stdout)
