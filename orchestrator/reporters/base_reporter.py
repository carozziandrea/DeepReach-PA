"""
Base Reporter - Classe astratta per i reporter.

Tutti i reporter devono ereditare da questa classe e implementare il metodo report().
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from models import AnalysisResult


class BaseReporter(ABC):
    """
    Classe astratta per i reporter.
    
    Per creare un nuovo formato di output:
    1. Crea una nuova classe che eredita da BaseReporter
    2. Implementa il metodo report()
    3. (Opzionale) Override di get_file_extension() se salvi su file
    """
    
    def __init__(self, output_dir: Path = None):
        """
        Inizializza il reporter.
        
        Args:
            output_dir: Directory dove salvare l'output (se applicabile)
        """
        self.output_dir = output_dir or Path("./output")
    
    @abstractmethod
    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> None:
        """
        Genera il report.
        
        Args:
            result: Risultato dell'analisi
            filename: Nome del file di output (senza estensione)
        """
        pass
    
    def get_file_extension(self) -> str:
        """
        Restituisce l'estensione del file per questo reporter.
        Override nelle sottoclassi se necessario.
        """
        return ""
    
    def get_output_path(self, filename: str) -> Path:
        """
        Costruisce il path completo per il file di output.
        
        Args:
            filename: Nome del file (senza estensione)
        
        Returns:
            Path completo
        """
        ext = self.get_file_extension()
        if ext:
            return self.output_dir / f"{filename}.{ext}"
        return self.output_dir / filename
