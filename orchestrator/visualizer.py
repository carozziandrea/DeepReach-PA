"""
Visualizer - Genera la visualizzazione interattiva del grafo.

Questo modulo integra la generazione del grafo force-directed nel workflow
dell'orchestrator, utilizzando i moduli di scripts/.
"""

import sys
from pathlib import Path
from typing import Optional

# Aggiungi scripts/ al path per importare i moduli
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import dei moduli da scripts/ prima di qualsiasi altro import
from graph_builder import GraphBuilder
from graph_stats import GraphStats
from graph_visualizer import GraphVisualizer

# Import esplicito di VisualizationConfig da scripts/config.py
import importlib.util
spec = importlib.util.spec_from_file_location("scripts_config", scripts_dir / "config.py")
scripts_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scripts_config)
VisualizationConfig = scripts_config.VisualizationConfig


class Visualizer:
    """Genera visualizzazioni del grafo del sito."""

    def __init__(self, output_dir: Path = None):
        """
        Inizializza il visualizzatore.

        Args:
            output_dir: Directory di output (default: output/)
        """
        self.output_dir = output_dir or Path(__file__).parent.parent / "output"
        self.config = VisualizationConfig()
        # Aggiorna i path nel config per usare la directory corretta
        self.config.input_file = str(self.output_dir / "site_tree.json")
        self.config.output_file = str(self.output_dir / "force_directed_graph.html")

    def generate_graph(
        self,
        input_file: str = None,
        output_file: str = None,
        show_stats: bool = True
    ) -> Optional[str]:
        """
        Genera il grafo interattivo da un file site_tree.json.

        Args:
            input_file: Path al file JSON di input (default: site_tree.json)
            output_file: Path al file HTML di output (default: force_directed_graph.html)
            show_stats: Se True, stampa le statistiche del grafo

        Returns:
            Path al file HTML generato, o None se errore
        """
        input_path = input_file or self.config.input_file
        output_path = output_file or self.config.output_file

        print("\n" + "=" * 60)
        print("[GRAPH] GENERAZIONE GRAFO INTERATTIVO")
        print("=" * 60)
        print(f"   Input:  {input_path}")
        print(f"   Output: {output_path}")

        try:
            # Carica e costruisci il grafo
            data = GraphBuilder.load_data(input_path)
            tree = data.get("tree", data)
            start_url = GraphBuilder.find_root_node(tree)
            G = GraphBuilder.build_graph(tree, start_url)
            G_spt = GraphBuilder.create_shortest_path_tree(G, start_url)

            # Statistiche
            if show_stats:
                GraphStats.print_statistics(G_spt)

            # Genera visualizzazione
            visualizer = GraphVisualizer(self.config)
            visualizer.visualize(G_spt, output_path)

            print(f"\n[OK] Grafo generato: {output_path}")
            return output_path

        except FileNotFoundError as e:
            print(f"\n[X] File non trovato: {e}")
            return None
        except Exception as e:
            print(f"\n[X] Errore generazione grafo: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_for_crawl(
        self,
        crawl_name: str = "site_tree",
        output_name: str = None
    ) -> Optional[str]:
        """
        Genera il grafo per uno specifico crawl.

        Args:
            crawl_name: Nome del file crawl (senza .json)
            output_name: Nome del file output (senza .html), default = crawl_name

        Returns:
            Path al file HTML generato, o None se errore
        """
        input_file = str(self.output_dir / f"{crawl_name}.json")
        output_file = str(self.output_dir / f"{output_name or crawl_name}_graph.html")

        return self.generate_graph(input_file, output_file)


def generate_visualization(
    input_file: str,
    output_file: str = None,
    output_dir: Path = None
) -> Optional[str]:
    """
    Funzione di convenienza per generare una visualizzazione.

    Args:
        input_file: Path al file JSON di input
        output_file: Path al file HTML di output (opzionale)
        output_dir: Directory di output (opzionale)

    Returns:
        Path al file HTML generato, o None se errore
    """
    visualizer = Visualizer(output_dir)
    return visualizer.generate_graph(input_file, output_file)
