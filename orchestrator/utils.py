"""
Utility functions per l'orchestratore.
"""

import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


def extract_domain(url: str) -> str:
    """
    Estrae il dominio da un URL per usarlo come nome cartella.

    Args:
        url: URL completo (es. https://www.comune.milano.it/pagina)

    Returns:
        Dominio pulito (es. "comune.milano.it")
    """
    if not url:
        return "unknown"

    # Normalizza URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]

        # Rimuovi www. se presente
        if domain.startswith('www.'):
            domain = domain[4:]

        # Rimuovi porta se presente
        domain = domain.split(':')[0]

        # Sanitizza per uso come nome cartella
        domain = sanitize_filename(domain)

        return domain if domain else "unknown"
    except Exception:
        return "unknown"


def sanitize_filename(name: str) -> str:
    """
    Rimuove caratteri non validi per nomi file/cartelle.

    Args:
        name: Nome da sanitizzare

    Returns:
        Nome pulito
    """
    # Caratteri non validi per Windows
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)

    # Rimuovi spazi iniziali/finali e punti finali
    sanitized = sanitized.strip(' .')

    return sanitized if sanitized else "unnamed"


def ensure_directory(path: Path) -> Path:
    """
    Crea una directory se non esiste.

    Args:
        path: Path della directory

    Returns:
        Path della directory creata
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_site_output_dir(base_output_dir: Path, url: str) -> Path:
    """
    Ottiene la directory di output specifica per un sito.

    Args:
        base_output_dir: Directory base di output
        url: URL del sito

    Returns:
        Path alla directory del sito (es. output/comune.milano.it/)
    """
    domain = extract_domain(url)
    site_dir = Path(base_output_dir) / domain
    return site_dir


def check_site_completed(site_dir: Path) -> bool:
    """
    Verifica se un sito è già stato analizzato completamente.

    Un sito è considerato completo se esiste:
    - analysis_report.json

    Args:
        site_dir: Directory del sito

    Returns:
        True se l'analisi è completa
    """
    site_dir = Path(site_dir)

    if not site_dir.exists():
        return False

    # Controlla che esista il report JSON
    report_file = site_dir / "analysis_report.json"
    return report_file.exists()


def load_partial_batch_state(output_dir: Path) -> dict:
    """
    Carica lo stato parziale di un batch interrotto.

    Args:
        output_dir: Directory di output base

    Returns:
        Dict con lo stato: {
            "completed_sites": ["url1", "url2", ...],
            "failed_sites": [{"url": "...", "error": "..."}]
        }
    """
    import json

    state_file = Path(output_dir) / "_batch_state.json"

    if not state_file.exists():
        return {"completed_sites": [], "failed_sites": []}

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"completed_sites": [], "failed_sites": []}


def save_partial_batch_state(output_dir: Path, state: dict) -> None:
    """
    Salva lo stato parziale di un batch.

    Args:
        output_dir: Directory di output base
        state: Stato da salvare
    """
    import json

    state_file = Path(output_dir) / "_batch_state.json"

    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] Impossibile salvare stato batch: {e}")
