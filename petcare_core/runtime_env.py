"""Load a private server environment file without evaluating shell expressions."""
import os
from pathlib import Path
import re
import shlex


def load_private_environment():
    explicit = os.environ.get('PETCARE_ENV_FILE')
    path = Path(explicit or '/etc/petcare.env')
    if not path.exists():
        if explicit:
            raise RuntimeError('No se encontró el archivo privado configurado.')
        return
    for number, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise RuntimeError(f'Línea inválida en el archivo privado: {number}.')
        try:
            parts = shlex.split(value, comments=False, posix=True)
        except ValueError:
            raise RuntimeError(f'Valor inválido en el archivo privado: línea {number}.') from None
        if len(parts) > 1:
            raise RuntimeError(f'Usa comillas para valores con espacios: línea {number}.')
        os.environ.setdefault(key, parts[0] if parts else '')
