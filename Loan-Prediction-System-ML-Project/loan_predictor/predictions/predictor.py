import joblib
from django.conf import settings
from pathlib import Path

MODEL = None
MODEL_PATH = Path(settings.BASE_DIR) / 'ml' / 'models' / 'pipeline.joblib'

def get_model():
    global MODEL
    if MODEL is None:
        MODEL = joblib.load(MODEL_PATH)
    return MODEL
