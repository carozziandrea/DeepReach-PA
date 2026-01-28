"""
JSON Reporter - Salva il report in formato JSON.

Produce un file JSON strutturato con tutti i dati dell'analisi.
"""

import json
from pathlib import Path
from typing import Optional

from models import AnalysisResult
from reporters.base_reporter import BaseReporter


class JsonReporter(BaseReporter):
    """Reporter per output JSON."""
    
    def __init__(self, output_dir: Path = None, indent: int = 2):
        """
        Inizializza il reporter JSON.
        
        Args:
            output_dir: Directory di output
            indent: Indentazione JSON (default: 2)
        """
        super().__init__(output_dir)
        self.indent = indent
    
    def get_file_extension(self) -> str:
        return "json"
    
    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> None:
        """
        Salva il report in formato JSON.
        
        Args:
            result: Risultato dell'analisi
            filename: Nome del file (default: 'analysis_report')
        """
        filename = filename or "analysis_report"
        output_path = self.get_output_path(filename)
        
        # Assicura che la directory esista
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Converti in dizionario
        data = result.to_dict()
        
        # Salva
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=False)
        
        print(f"[SAVED] Report JSON salvato: {output_path}")
