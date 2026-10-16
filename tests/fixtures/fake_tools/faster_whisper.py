"""FICTIONAL fallback adapter; asserts configuration but generates no evidence."""
from types import SimpleNamespace
class WhisperModel:
    def __init__(self, name, device, compute_type):
        assert name == 'base' and device == 'cpu' and compute_type == 'int8'
    def transcribe(self, path, beam_size):
        return iter([SimpleNamespace(start=0.0, end=2.0, text='FICTIONAL fallback transcript')]), SimpleNamespace(language='en')
