"""
Modelli dati per l'orchestratore.

Contiene le dataclass che rappresentano i risultati delle analisi.
Questi modelli vengono usati dai reporter per generare l'output.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ReachabilityMetrics:
    """Metriche di raggiungibilità delle pagine."""
    
    total_pages: int = 0
    total_files: int = 0
    
    # Profondità
    avg_depth: float = 0.0
    max_depth: int = 0
    min_depth: int = 0
    depth_distribution: Dict[int, int] = field(default_factory=dict)
    # ^ {0: 1, 1: 5, 2: 12, ...} = quante pagine per ogni livello
    
    # Pagine per profondità
    pages_at_depth_1: int = 0
    pages_at_depth_2: int = 0
    pages_at_depth_3_plus: int = 0


@dataclass
class QualityMetrics:
    """Metriche di qualità strutturale del sito."""
    
    total_nodes: int = 0
    pages_ok: int = 0
    pages_broken: int = 0
    pages_not_visited: int = 0
    files_found: int = 0
    
    # Percentuali
    broken_percent: float = 0.0
    
    # Liste URL problematici
    broken_urls: List[str] = field(default_factory=list)
    orphan_urls: List[str] = field(default_factory=list)  # Pagine senza parent


@dataclass 
class SectionAnalysis:
    """Analisi di una singola sezione obbligatoria."""
    
    name: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Dove è stata trovata
    found_in_at: bool = False
    found_in_main: bool = False
    
    # URL dove è stata trovata
    urls_in_at: List[str] = field(default_factory=list)
    urls_in_main: List[str] = field(default_factory=list)
    
    # Profondità minima per raggiungerla
    min_depth_in_at: Optional[int] = None
    min_depth_in_main: Optional[int] = None
    
    @property
    def is_hidden(self) -> bool:
        """True se la sezione è fuori da AT (trasparenza sommersa)."""
        return self.found_in_main and not self.found_in_at
    
    @property
    def is_missing(self) -> bool:
        """True se la sezione non è stata trovata da nessuna parte."""
        return not self.found_in_at and not self.found_in_main


@dataclass
class TransparencyMetrics:
    """Metriche di trasparenza e trasparenza sommersa."""
    
    # Sezioni analizzate
    sections: List[SectionAnalysis] = field(default_factory=list)
    
    # Conteggi
    total_required_sections: int = 0
    sections_in_at: int = 0
    sections_only_in_main: int = 0  # Trasparenza sommersa
    sections_missing: int = 0
    
    # Percentuali
    at_coverage_percent: float = 0.0  # % sezioni obbligatorie coperte da AT
    hidden_transparency_percent: float = 0.0  # % sezioni fuori da AT
    
    # Liste per dettaglio
    hidden_sections: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    
    @property
    def all_sections_in_at(self) -> bool:
        """True se tutte le sezioni obbligatorie sono in AT."""
        return self.sections_in_at == self.total_required_sections


@dataclass
class UsabilityIndex:
    """Indice di usabilità calcolato."""

    score: float = 0.0  # Punteggio finale 0-100

    # Dettaglio componenti
    base_score: float = 100.0
    depth_penalty: float = 0.0
    broken_penalty: float = 0.0
    hidden_penalty: float = 0.0
    bonus: float = 0.0

    # Giudizio testuale
    rating: str = ""  # "Ottimo", "Buono", "Sufficiente", "Insufficiente", "Critico"

    @staticmethod
    def get_rating(score: float) -> str:
        """Restituisce il giudizio testuale in base al punteggio."""
        if score >= 90:
            return "Ottimo"
        elif score >= 75:
            return "Buono"
        elif score >= 60:
            return "Sufficiente"
        elif score >= 40:
            return "Insufficiente"
        else:
            return "Critico"


@dataclass
class PrivacyFindingDetail:
    """Dettaglio di un singolo ritrovamento privacy."""

    pattern_type: str = ""  # "codice_fiscale", "email", ecc.
    count: int = 0
    samples: List[str] = field(default_factory=list)


@dataclass
class PrivacyMetrics:
    """Metriche di privacy per l'analisi del sito."""

    # Conteggi
    total_scanned: int = 0
    pages_scanned: int = 0
    files_scanned: int = 0

    # Rischi
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0

    # URL a rischio (per il report)
    high_risk_urls: List[str] = field(default_factory=list)
    medium_risk_urls: List[str] = field(default_factory=list)

    # Ritrovamenti aggregati per tipo
    findings_by_type: Dict[str, int] = field(default_factory=dict)

    # Errori di scansione
    scan_errors: List[str] = field(default_factory=list)

    @property
    def has_high_risk(self) -> bool:
        """True se ci sono nodi ad alto rischio."""
        return self.high_risk_count > 0

    @property
    def risk_percentage(self) -> float:
        """Percentuale di nodi con rischio (medium + high)."""
        if self.total_scanned == 0:
            return 0.0
        return ((self.high_risk_count + self.medium_risk_count) / self.total_scanned) * 100


@dataclass
class CrawlInfo:
    """Informazioni su un singolo crawl."""
    
    mode: str = ""  # "deep" o "shallow"
    start_url: str = ""
    output_file: str = ""
    
    # Risultati
    success: bool = False
    total_pages: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    Risultato completo dell'analisi.
    
    Questo è l'oggetto principale che viene passato ai reporter.
    Contiene tutti i dati raccolti e calcolati.
    """
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    homepage_url: str = ""
    at_url: Optional[str] = None
    at_found: bool = False
    
    # Info crawl
    crawl_shallow: Optional[CrawlInfo] = None
    crawl_deep: Optional[CrawlInfo] = None
    
    # Metriche (popolate solo se i crawl hanno successo)
    reachability_at: Optional[ReachabilityMetrics] = None
    reachability_main: Optional[ReachabilityMetrics] = None
    quality_at: Optional[QualityMetrics] = None
    quality_main: Optional[QualityMetrics] = None
    transparency: Optional[TransparencyMetrics] = None
    usability_index: Optional[UsabilityIndex] = None
    privacy: Optional[PrivacyMetrics] = None

    # Dati raw per analisi future
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il risultato in dizionario per serializzazione JSON."""
        return {
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "homepage_url": self.homepage_url,
                "at_url": self.at_url,
                "at_found": self.at_found,
            },
            "crawl_info": {
                "shallow": self._crawl_to_dict(self.crawl_shallow),
                "deep": self._crawl_to_dict(self.crawl_deep),
            },
            "reachability": {
                "at": self._dataclass_to_dict(self.reachability_at),
                "main": self._dataclass_to_dict(self.reachability_main),
            },
            "quality": {
                "at": self._dataclass_to_dict(self.quality_at),
                "main": self._dataclass_to_dict(self.quality_main),
            },
            "transparency": self._transparency_to_dict(),
            "usability_index": self._dataclass_to_dict(self.usability_index),
            "privacy": self._privacy_to_dict(),
        }

    def _privacy_to_dict(self) -> Optional[Dict]:
        """Converte le metriche privacy in dizionario."""
        if self.privacy is None:
            return None
        return {
            "total_scanned": self.privacy.total_scanned,
            "pages_scanned": self.privacy.pages_scanned,
            "files_scanned": self.privacy.files_scanned,
            "high_risk_count": self.privacy.high_risk_count,
            "medium_risk_count": self.privacy.medium_risk_count,
            "low_risk_count": self.privacy.low_risk_count,
            "high_risk_urls": self.privacy.high_risk_urls[:20],
            "medium_risk_urls": self.privacy.medium_risk_urls[:20],
            "findings_by_type": self.privacy.findings_by_type,
            "has_high_risk": self.privacy.has_high_risk,
            "risk_percentage": round(self.privacy.risk_percentage, 1),
        }
    
    def _crawl_to_dict(self, crawl: Optional[CrawlInfo]) -> Optional[Dict]:
        if crawl is None:
            return None
        return {
            "mode": crawl.mode,
            "start_url": crawl.start_url,
            "output_file": crawl.output_file,
            "success": crawl.success,
            "total_pages": crawl.total_pages,
            "duration_seconds": crawl.duration_seconds,
            "error_message": crawl.error_message,
        }
    
    def _dataclass_to_dict(self, obj) -> Optional[Dict]:
        if obj is None:
            return None
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, list) and len(value) > 20:
                    # Tronca liste molto lunghe nel report
                    result[field_name] = value[:20]
                    result[f"{field_name}_truncated"] = True
                    result[f"{field_name}_total"] = len(value)
                else:
                    result[field_name] = value
            return result
        return None
    
    def _transparency_to_dict(self) -> Optional[Dict]:
        if self.transparency is None:
            return None
        result = {
            "total_required_sections": self.transparency.total_required_sections,
            "sections_in_at": self.transparency.sections_in_at,
            "sections_only_in_main": self.transparency.sections_only_in_main,
            "sections_missing": self.transparency.sections_missing,
            "at_coverage_percent": self.transparency.at_coverage_percent,
            "hidden_transparency_percent": self.transparency.hidden_transparency_percent,
            "hidden_sections": self.transparency.hidden_sections,
            "missing_sections": self.transparency.missing_sections,
            "all_sections_in_at": self.transparency.all_sections_in_at,
            "sections_detail": []
        }
        for section in self.transparency.sections:
            result["sections_detail"].append({
                "name": section.name,
                "found_in_at": section.found_in_at,
                "found_in_main": section.found_in_main,
                "is_hidden": section.is_hidden,
                "is_missing": section.is_missing,
                "min_depth_in_at": section.min_depth_in_at,
                "min_depth_in_main": section.min_depth_in_main,
                "urls_in_at": section.urls_in_at[:5] if section.urls_in_at else [],
                "urls_in_main": section.urls_in_main[:5] if section.urls_in_main else [],
            })
        return result
