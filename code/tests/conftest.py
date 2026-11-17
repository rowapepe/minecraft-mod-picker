import sys
from pathlib import Path

# пакеты из code/ (search) импортируются по имени
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
