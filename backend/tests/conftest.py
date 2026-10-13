import os
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "segredo-de-teste-com-tamanho-adequado-para-hs256")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
