import sys
from pathlib import Path

# Agrega la raíz de la misión al path para que 'src' sea importable
sys.path.insert(0, str(Path(__file__).parent))
