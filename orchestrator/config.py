"""
Configurazione dell'orchestratore.

Questo file contiene tutte le configurazioni modificabili:
- Sezioni obbligatorie per la trasparenza PA
- Keyword per identificare link AT
- Parametri di crawling
- Pesi per il calcolo dell'indice di usabilità
"""

from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path


# =============================================================================
# SEZIONI OBBLIGATORIE PER LA TRASPARENZA PA
# =============================================================================
# Struttura: "nome_sezione": [lista di keyword che identificano la sezione]
# Per aggiungere una nuova sezione, basta aggiungere una riga al dizionario.

REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "organizzazione": [
        "organi", "uffici", "organigramma", "organizzazione",
        "struttura", "articolazione"
    ],
    "bilanci": [
        "bilancio", "bilanci", "rendiconto", "piano-indicatori",
        "patrimonio", "spese", "entrate"
    ],
    "personale": [
        "personale", "dotazione", "dirigenti", "posizioni-organizzative",
        "contrattazione", "assenze", "tassi-assenza"
    ],
    "bandi_gare": [
        "bandi", "gare", "concorsi", "avvisi", "appalti",
        "contratti", "procedure"
    ],
    "delibere_atti": [
        "delibere", "determine", "atti", "provvedimenti",
        "ordinanze", "decreti"
    ],
    "albo_pretorio": [
        "albo", "pretorio", "albo-pretorio", "pubblicazioni"
    ],
    "consulenti": [
        "consulenti", "collaboratori", "incarichi", "professionisti"
    ],
    "sovvenzioni": [
        "sovvenzioni", "contributi", "sussidi", "vantaggi-economici"
    ],
    "performance": [
        "performance", "obiettivi", "valutazione", "piano-performance"
    ],
    "attivita_procedimenti": [
        "procedimenti", "attivita", "servizi", "modulistica", "tempi"
    ],
}


# =============================================================================
# KEYWORD PER IDENTIFICARE LINK AMMINISTRAZIONE TRASPARENTE
# =============================================================================

AT_KEYWORDS: List[str] = [
    "amministrazione trasparente",
    "amministrazione-trasparente",
    "amministrazione.trasparente",
    "amministrazione_trasparente",
    "amm_trasp",
    "amm-trasp",
    "trasparenza",
    "trasparente",
]


# =============================================================================
# PARAMETRI DI CRAWLING
# =============================================================================

@dataclass
class CrawlConfig:
    """Configurazione per i crawler."""

    # Profondità
    deep_max_depth: int = 4  # Ridotto da 5 per velocizzare
    shallow_max_depth: int = 1  # Ridotto da 2 - basta per vedere le sezioni principali

    # Modalità thorough (analisi approfondita per tesi)
    thorough_deep_depth: int = 5
    thorough_shallow_depth: int = 2
    thorough_concurrent: int = 2
    thorough_delay: float = 1.0

    # Timeout (secondi)
    page_load_timeout: int = 30  # Timeout per singola pagina
    js_render_wait: int = 5
    site_timeout: int = 7200  # Timeout totale per sito (2 ore)
    request_timeout: int = 60  # Timeout per singola richiesta HTTP

    # Output - directory unificata per tutti i dati (crawl + visualizzazione)
    # Usa output/ nella root del progetto
    output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")
    deep_output_name: str = "site_tree"
    shallow_output_name: str = "site_tree_main"

    # Path al crawler (relativo o assoluto)
    crawler_script: str = "sitemap_spider.py"
    spider_name: str = "sitemap_spider"


# =============================================================================
# CONFIGURAZIONE PRIVACY / DATI SENSIBILI
# =============================================================================

@dataclass
class PrivacyConfig:
    """
    Configurazione per la scansione privacy.

    I pattern regex sono definiti in content_scanner.py.
    Qui si configurano i comportamenti.
    """

    # Abilita/disabilita scansione
    enabled: bool = True
    scan_html_content: bool = True
    scan_pdf_files: bool = True

    # Limiti
    max_content_chars: int = 100000  # Max caratteri HTML da scansionare
    max_file_size_mb: int = 50  # Max dimensione PDF da scaricare
    max_pdfs_per_site: int = 0  # Max PDF da scansionare per sito (0 = nessun limite)

    # Download
    download_delay_seconds: float = 0.5  # Pausa tra download
    download_timeout_seconds: int = 30

    # Report
    include_samples_in_report: bool = True
    max_samples_per_pattern: int = 5


# =============================================================================
# PESI PER INDICE DI USABILITÀ
# =============================================================================

@dataclass
class UsabilityWeights:
    """
    Pesi per il calcolo dell'indice di usabilità (0-100).
    
    Formula base:
        score = 100 - penalità_profondità - penalità_link_rotti - penalità_trasparenza_sommersa + bonus
    
    Modifica questi valori per calibrare l'indice.
    """
    
    # Punteggio base
    base_score: float = 100.0
    
    # Penalità per profondità media elevata
    # Sottratto: penalty_per_depth_level * (profondità_media - ideal_depth)
    ideal_depth: float = 2.0
    penalty_per_depth_level: float = 5.0
    
    # Penalità per link rotti
    # Sottratto: penalty_per_broken_percent * percentuale_link_rotti
    penalty_per_broken_percent: float = 1.0
    
    # Penalità per trasparenza sommersa
    # Sottratto: penalty_per_hidden_section * numero_sezioni_fuori_AT
    penalty_per_hidden_section: float = 10.0
    
    # Bonus se tutte le sezioni obbligatorie sono in AT
    bonus_all_sections_in_at: float = 10.0
    
    # Punteggio minimo (floor)
    min_score: float = 0.0
    
    # Punteggio massimo (ceiling)
    max_score: float = 100.0


# =============================================================================
# CONFIGURAZIONE COMPLETA
# =============================================================================

@dataclass
class OrchestratorConfig:
    """Configurazione completa dell'orchestratore."""

    crawl: CrawlConfig = field(default_factory=CrawlConfig)
    usability_weights: UsabilityWeights = field(default_factory=UsabilityWeights)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    required_sections: Dict[str, List[str]] = field(default_factory=lambda: REQUIRED_SECTIONS.copy())
    at_keywords: List[str] = field(default_factory=lambda: AT_KEYWORDS.copy())
    
    # Report
    report_output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")
    report_filename: str = "analysis_report"
    
    def add_required_section(self, name: str, keywords: List[str]) -> None:
        """Aggiunge una nuova sezione obbligatoria."""
        self.required_sections[name] = keywords
    
    def remove_required_section(self, name: str) -> None:
        """Rimuove una sezione obbligatoria."""
        if name in self.required_sections:
            del self.required_sections[name]
    
    def add_at_keyword(self, keyword: str) -> None:
        """Aggiunge una keyword per identificare AT."""
        if keyword not in self.at_keywords:
            self.at_keywords.append(keyword)


# Configurazione di default (singleton-like)
default_config = OrchestratorConfig()