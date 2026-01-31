"""
Batch Runner - Esegue l'analisi su una lista di siti PA.

Questo modulo gestisce l'esecuzione batch dell'analisi su più siti,
aggregando i risultati e generando statistiche comparative.

Funzionalità:
- Output separato per ogni sito in sottocartelle
- Persistenza dello stato per riprendere batch interrotti
- Resume automatico di siti già analizzati
"""

from datetime import datetime
from pathlib import Path
from typing import List, TYPE_CHECKING

from models import AnalysisResult, BatchResult, SiteRanking, UsabilityIndex
from utils import (
    extract_domain,
    ensure_directory,
    get_site_output_dir,
    check_site_completed,
    load_partial_batch_state,
    save_partial_batch_state,
)

if TYPE_CHECKING:
    from main import Orchestrator


class BatchRunner:
    """
    Esegue l'analisi su una lista di siti PA.

    Processa ogni sito sequenzialmente, gestisce gli errori,
    e aggrega i risultati in un BatchResult.
    """

    def __init__(self, orchestrator: "Orchestrator"):
        """
        Inizializza il batch runner.

        Args:
            orchestrator: Istanza dell'orchestratore per eseguire le analisi
        """
        self.orchestrator = orchestrator
        self.output_dir = orchestrator.config.report_output_dir

    def load_sites(self, file_path: Path) -> List[str]:
        """
        Carica la lista di siti da un file.

        Il file deve contenere un URL per riga.
        Le righe vuote e i commenti (che iniziano con #) vengono ignorati.

        Args:
            file_path: Path al file con la lista di siti

        Returns:
            Lista di URL da analizzare

        Raises:
            FileNotFoundError: Se il file non esiste
        """
        sites = []

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Salta righe vuote e commenti
                if not line or line.startswith('#'):
                    continue

                # Normalizza URL
                if not line.startswith('http://') and not line.startswith('https://'):
                    line = 'https://' + line

                sites.append(line)

        return sites

    def run_batch(
        self,
        sites: List[str],
        continue_on_error: bool = True,
        skip_crawl: bool = False,
        shallow_only: bool = False,
        thorough: bool = False,
        resume: bool = False,
    ) -> BatchResult:
        """
        Esegue l'analisi su tutti i siti della lista.

        Args:
            sites: Lista di URL da analizzare
            continue_on_error: Se True, continua anche se un sito fallisce
            skip_crawl: Se True, salta i crawl e usa JSON esistenti
            shallow_only: Se True, esegue solo crawl shallow
            thorough: Se True, usa analisi approfondita (più lento)
            resume: Se True, salta siti già analizzati con successo

        Returns:
            BatchResult con tutti i risultati e le statistiche
        """
        results: List[AnalysisResult] = []
        failed_sites: List[dict] = []
        skipped_sites: List[str] = []

        total = len(sites)

        # Carica stato precedente se resume è attivo
        batch_state = {"completed_sites": [], "failed_sites": []}
        if resume:
            batch_state = load_partial_batch_state(self.output_dir)
            if batch_state["completed_sites"]:
                print(f"[RESUME] Trovati {len(batch_state['completed_sites'])} siti già completati")

        print("\n" + "=" * 70)
        print("DeepReach-PA - Analisi Batch")
        print("=" * 70)
        print(f"Siti da analizzare: {total}")
        mode_str = "approfondita (thorough)" if thorough else "veloce (default)"
        print(f"Modalita: {mode_str}")
        if resume:
            print(f"Resume: attivo")
        print(f"Output: {self.output_dir}")
        print("=" * 70)

        for i, site_url in enumerate(sites, 1):
            domain = extract_domain(site_url)
            site_output_dir = get_site_output_dir(self.output_dir, site_url)

            print(f"\n[{i}/{total}] Analisi: {site_url}")
            print(f"   Output: {site_output_dir}")
            print("-" * 50)

            # Controlla se il sito è già stato completato (resume)
            if resume:
                # Controlla se il dominio è nella lista dei completati
                if site_url in batch_state["completed_sites"]:
                    print(f"[SKIP] Già completato (da stato batch)")
                    skipped_sites.append(site_url)
                    # Carica il risultato esistente se possibile
                    existing_result = self._load_existing_result(site_output_dir, site_url)
                    if existing_result:
                        results.append(existing_result)
                    continue

                # Controlla se esiste già l'output completo
                if check_site_completed(site_output_dir):
                    print(f"[SKIP] Già analizzato (output esistente)")
                    skipped_sites.append(site_url)
                    batch_state["completed_sites"].append(site_url)
                    # Carica il risultato esistente
                    existing_result = self._load_existing_result(site_output_dir, site_url)
                    if existing_result:
                        results.append(existing_result)
                    continue

            try:
                # Crea directory per il sito
                ensure_directory(site_output_dir)

                # Esegui analisi con output nella directory del sito
                result = self.orchestrator.run(
                    homepage_url=site_url,
                    skip_crawl=skip_crawl,
                    shallow_only=shallow_only,
                    thorough=thorough,
                    site_output_dir=site_output_dir,
                )
                results.append(result)

                # Aggiorna stato batch
                batch_state["completed_sites"].append(site_url)
                save_partial_batch_state(self.output_dir, batch_state)

                # Mostra risultato sintetico
                if result.usability_index:
                    score = result.usability_index.score
                    rating = result.usability_index.rating
                    print(f"[OK] Usability: {score:.1f}/100 ({rating})")
                else:
                    print("[OK] Analisi completata (senza indice usabilità)")

            except KeyboardInterrupt:
                print("\n[WARN] Interrotto dall'utente")
                # Salva stato prima di uscire
                save_partial_batch_state(self.output_dir, batch_state)
                failed_sites.append({
                    "url": site_url,
                    "error": "Interrotto dall'utente"
                })
                break

            except Exception as e:
                error_msg = str(e).splitlines()[0] if str(e) else "Errore sconosciuto"
                print(f"[ERRORE] {error_msg}")

                failed_sites.append({
                    "url": site_url,
                    "error": error_msg
                })

                # Aggiorna stato batch con il fallimento
                batch_state["failed_sites"].append({"url": site_url, "error": error_msg})
                save_partial_batch_state(self.output_dir, batch_state)

                if not continue_on_error:
                    raise

        # Riepilogo skip
        if skipped_sites:
            print(f"\n[INFO] Siti saltati (già completati): {len(skipped_sites)}")

        # Crea risultato batch con statistiche
        return self._create_batch_result(results, failed_sites, total)

    def _load_existing_result(self, site_dir: Path, site_url: str) -> AnalysisResult:
        """
        Carica un AnalysisResult esistente da una directory.

        Args:
            site_dir: Directory del sito
            site_url: URL del sito

        Returns:
            AnalysisResult caricato o None se non trovato
        """
        import json

        report_file = Path(site_dir) / "analysis_report.json"

        if not report_file.exists():
            return None

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Ricostruisci un AnalysisResult minimale per le statistiche batch
            result = AnalysisResult(
                homepage_url=site_url,
                at_url=data.get("metadata", {}).get("at_url"),
                at_found=data.get("metadata", {}).get("at_found", False),
            )

            # Ricostruisci UsabilityIndex se presente
            ui_data = data.get("usability_index")
            if ui_data:
                result.usability_index = UsabilityIndex(
                    score=ui_data.get("score", 0.0),
                    rating=ui_data.get("rating", "N/A"),
                    base_score=ui_data.get("base_score", 100.0),
                    depth_penalty=ui_data.get("depth_penalty", 0.0),
                    broken_penalty=ui_data.get("broken_penalty", 0.0),
                    hidden_penalty=ui_data.get("hidden_penalty", 0.0),
                    bonus=ui_data.get("bonus", 0.0),
                )

            # Ricostruisci TransparencyMetrics se presente
            from models import TransparencyMetrics
            tr_data = data.get("transparency")
            if tr_data:
                result.transparency = TransparencyMetrics(
                    total_required_sections=tr_data.get("total_required_sections", 0),
                    sections_in_at=tr_data.get("sections_in_at", 0),
                    sections_only_in_main=tr_data.get("sections_only_in_main", 0),
                    sections_missing=tr_data.get("sections_missing", 0),
                    at_coverage_percent=tr_data.get("at_coverage_percent", 0.0),
                )

            return result

        except Exception as e:
            print(f"[WARN] Impossibile caricare risultato esistente: {e}")
            return None

    def _create_batch_result(
        self,
        results: List[AnalysisResult],
        failed_sites: List[dict],
        total_sites: int
    ) -> BatchResult:
        """
        Crea il BatchResult con ranking e statistiche aggregate.

        Args:
            results: Lista di AnalysisResult per i siti analizzati con successo
            failed_sites: Lista di dict con URL e errore per i siti falliti
            total_sites: Numero totale di siti nella lista originale

        Returns:
            BatchResult completo
        """
        # Calcola ranking
        ranking = self._calculate_ranking(results)

        # Calcola statistiche aggregate
        scores = [r.usability_index.score for r in results if r.usability_index]
        coverages = [
            r.transparency.at_coverage_percent
            for r in results
            if r.transparency
        ]
        hidden_count = sum(
            1 for r in results
            if r.transparency and r.transparency.sections_only_in_main > 0
        )

        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0

        return BatchResult(
            timestamp=datetime.now(),
            total_sites=total_sites,
            successful=len(results),
            failed=len(failed_sites),
            results=results,
            failed_sites=failed_sites,
            ranking=ranking,
            avg_usability_score=avg_score,
            avg_at_coverage=avg_coverage,
            sites_with_hidden_transparency=hidden_count,
        )

    def _calculate_ranking(self, results: List[AnalysisResult]) -> List[SiteRanking]:
        """
        Calcola il ranking dei siti per usability score.

        Args:
            results: Lista di AnalysisResult

        Returns:
            Lista di SiteRanking ordinata per score decrescente
        """
        rankings = []

        for result in results:
            if result.usability_index:
                score = result.usability_index.score
                rating = result.usability_index.rating
            else:
                score = 0.0
                rating = "N/A"

            if result.transparency:
                coverage = result.transparency.at_coverage_percent
                hidden = result.transparency.sections_only_in_main > 0
                hidden_count = result.transparency.sections_only_in_main
            else:
                coverage = 0.0
                hidden = False
                hidden_count = 0

            rankings.append(SiteRanking(
                url=result.homepage_url,
                usability_score=score,
                rating=rating,
                at_coverage_percent=coverage,
                has_hidden_transparency=hidden,
                hidden_sections_count=hidden_count,
            ))

        # Ordina per score decrescente
        rankings.sort(key=lambda x: x.usability_score, reverse=True)

        return rankings
