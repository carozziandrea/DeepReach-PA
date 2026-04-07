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
    # 1 - Disposizioni generali
    "disposizioni_generali": [
        "disposizioni-generali", "disposizioni generali", "disposizioni_generali",
        "piano-triennale", "piano-prevenzione",
        "anticorruzione", "ptpct", "ptpc", "codice-etico", "codice-comportamento",
        "regolamenti"
    ],
    # 2 - Organizzazione
    "organizzazione": [
        "organi", "uffici", "organigramma", "organizzazione",
        "struttura", "articolazione"
    ],
    # 3 - Consulenti e collaboratori
    "consulenti": [
        "consulenti", "collaboratori", "incarichi", "professionisti",
        "consulenti e collaboratori", "consulenti-e-collaboratori", "consulenti_e_collaboratori"
    ],
    # 4 - Personale
    "personale": [
        "personale", "dotazione", "dirigenti", "posizioni-organizzative",
        "contrattazione", "assenze", "tassi-assenza"
    ],
    # 5 - Bandi di concorso
    "bandi_concorso": [
        "bandi-concorso", "bandi di concorso", "bandi_concorso",
        "concorsi", "selezioni", "avvisi-selezione", "graduatorie"
    ],
    # 6 - Performance
    "performance": [
        "performance", "obiettivi", "valutazione", "piano-performance"
    ],
    # 7 - Enti controllati
    "enti_controllati": [
        "enti-controllati", "enti controllati", "enti_controllati",
        "societa-partecipate", "partecipate",
        "enti-pubblici", "fondazioni", "associazioni-partecipate",
        "rappresentazione-grafica"
    ],
    # 8 - Attività e procedimenti
    "attivita_procedimenti": [
        "procedimenti", "attivita", "modulistica", "tempi",
        "tipologie-procedimento", "attivita e procedimenti",
        "attivita-e-procedimenti", "attivita_procedimenti",
        "attività e procedimenti"
    ],
    # 9 - Provvedimenti
    "provvedimenti": [
        "provvedimenti", "delibere", "determine", "ordinanze",
        "decreti", "atti-dirigenziali", "atti-organi-indirizzo"
    ],
    # 10 - Controlli sulle imprese
    "controlli_imprese": [
        "controlli-imprese", "controlli-sulle-imprese",
        "controlli imprese", "controlli_imprese",
        "autorizzazioni", "concessioni"
    ],
    # 11 - Bandi di gara e contratti
    "bandi_gare": [
        "bandi-gara", "bandi di gara", "bandi_gare", "bandi e contratti",
        "gare", "appalti", "contratti",
        "procedure-negoziate", "affidamenti"
    ],
    # 12 - Sovvenzioni, contributi, sussidi, vantaggi economici
    "sovvenzioni": [
        "sovvenzioni", "contributi", "sussidi", "vantaggi-economici",
        "benefici-economici", "sovvenzioni contributi", "sovvenzioni_contributi"
    ],
    # 13 - Bilanci
    "bilanci": [
        "bilancio", "bilanci", "rendiconto", "piano-indicatori",
        "patrimonio", "spese", "entrate"
    ],
    # 14 - Beni immobili e gestione patrimonio
    "beni_immobili": [
        "beni-immobili", "beni immobili", "beni_immobili",
        "patrimonio-immobiliare", "canoni-locazione",
        "canoni-affitto", "beni-demaniali"
    ],
    # 15 - Controlli e rilievi sull'amministrazione
    "controlli_amministrazione": [
        "controlli-rilievi", "controlli amministrazione", "controlli_amministrazione",
        "organi-revisione", "corte-dei-conti",
        "relazioni-revisori", "nuclei-valutazione"
    ],
    # 16 - Servizi erogati
    "servizi_erogati": [
        "servizi-erogati", "servizi erogati", "servizi_erogati",
        "carta-servizi", "costi-contabilizzati",
        "liste-attesa", "tempi-medi-erogazione"
    ],
    # 17 - Pagamenti dell'amministrazione
    "pagamenti": [
        "pagamenti", "pagamenti amministrazione", "pagamenti_amministrazione",
        "indicatore-tempestivita", "iban",
        "pagamento-informatico", "dati-pagamenti"
    ],
    # 18 - Opere pubbliche
    "opere_pubbliche": [
        "opere-pubbliche", "opere pubbliche", "opere_pubbliche",
        "lavori-pubblici", "nuclei-valutazione-verifica", "oopp"
    ],
    # 19 - Pianificazione e governo del territorio
    "pianificazione_territorio": [
        "pianificazione-territorio", "pianificazione territorio", "pianificazione_territorio",
        "governo-territorio", "piano-urbanistico", "prg", "pgt", "strumenti-urbanistici"
    ],
    # 20 - Informazioni ambientali
    "informazioni_ambientali": [
        "informazioni-ambientali", "informazioni ambientali", "informazioni_ambientali",
        "ambiente", "vinca", "via", "valutazione-impatto-ambientale"
    ],
    # 21 - Interventi straordinari e di emergenza
    "interventi_emergenza": [
        "emergenza", "interventi-straordinari", "interventi emergenza", "interventi_emergenza",
        "protezione-civile", "calamita", "commissari"
    ],
    # 22 - Altri contenuti - Accesso civico
    "accesso_civico": [
        "accesso-civico", "accesso civico", "accesso_civico",
        "accesso-generalizzato", "foia",
        "accesso-documenti", "richieste-accesso"
    ],
    # 23 - Altri contenuti - Accessibilità e dati
    "accessibilita_dati": [
        "accessibilita", "accessibilita dati", "accessibilita_dati",
        "catalogo-dati", "catalogo dati", "catalogo_dati",
        "open-data", "dati-aperti", "metadati", "banche-dati"
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
    # Sottratto: penalty_per_depth_level * (profondità_media_sezioni_AT - ideal_depth)
    ideal_depth: float = 2.0
    penalty_per_depth_level: float = 5.0

    # Penalità per link rotti
    # Sottratto: penalty_per_broken_percent * percentuale_link_rotti
    penalty_per_broken_percent: float = 1.0

    # Penalità per trasparenza sommersa
    # Sottratto: penalty_per_hidden_section * numero_sezioni_fuori_AT
    penalty_per_hidden_section: float = 10.0

    # Penalità per sezioni completamente assenti
    # Sottratto: penalty_per_missing_section * numero_sezioni_mancanti
    penalty_per_missing_section: float = 3.0

    # Bonus graduale proporzionale alla copertura AT
    # Aggiunto: (sezioni_in_at / totale_sezioni) * bonus_all_sections_in_at
    bonus_all_sections_in_at: float = 5.0

    # Punteggio minimo (floor)
    min_score: float = 0.0

    # Punteggio massimo (ceiling)
    max_score: float = 100.0

    # Pesi per il punteggio finale ponderato
    weight_conformity: float = 0.6
    weight_usability: float = 0.4


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