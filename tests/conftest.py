"""Host-side tests: app/ is put on the path, so the modules import as they do on the Pi."""
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / 'app'
sys.path.insert(0, str(APP))
