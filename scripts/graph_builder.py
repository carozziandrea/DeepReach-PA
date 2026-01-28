import networkx as nx
import json
from typing import Tuple, Optional

# Sezioni obbligatorie per la trasparenza PA (stesso formato di orchestrator/config.py)
TRANSPARENCY_SECTIONS = {
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


class GraphBuilder:
    @staticmethod
    def load_data(json_file: str) -> dict:
        """Carica i dati dal file JSON."""
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def find_root_node(tree: dict) -> str:
        """Trova il nodo root (depth=0)."""
        for url, info in tree.items():
            if info.get("depth", 999) == 0:
                return url
        raise ValueError("Nessun nodo root trovato (depth=0)")

    @staticmethod
    def check_transparency(url: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se l'URL appartiene a una sezione di trasparenza obbligatoria.

        Args:
            url: L'URL da controllare

        Returns:
            Tupla (is_transparency, section_name) dove section_name è il nome
            della sezione trovata o None se non è una sezione trasparenza
        """
        url_lower = url.lower()

        for section_name, keywords in TRANSPARENCY_SECTIONS.items():
            for keyword in keywords:
                if keyword.lower() in url_lower:
                    # Formatta nome sezione per display
                    display_name = section_name.replace("_", " ").title()
                    return True, display_name

        return False, None

    @staticmethod
    def build_graph(tree: dict, start_url: str) -> nx.DiGraph:
        """Costruisce il grafo dai dati."""
        G = nx.DiGraph()

        for url, info in tree.items():
            # Verifica se è una sezione trasparenza obbligatoria
            is_transparency, transparency_section = GraphBuilder.check_transparency(url)

            G.add_node(
                url,
                depth=info.get("depth", 0),
                display_name=info.get("display_name", "unknown"),
                title=info.get("title", ""),
                is_start=url == start_url,
                status=info.get("status", "pending"),
                status_code=info.get("status_code", "N/A"),
                error=info.get("error", ""),
                file_type=info.get("file_type", None),
                is_dynamic=info.get("is_dynamic", False),
                dynamic_label=info.get("dynamic_label", "N/A"),
                # Campi privacy (se presenti dall'analisi privacy)
                privacy_risk=info.get("privacy_risk", "none"),
                privacy_findings=info.get("privacy_findings", []),
                privacy_total_findings=info.get("privacy_total_findings", 0),
                # Campi trasparenza (classificazione automatica)
                is_transparency=is_transparency,
                transparency_section=transparency_section,
            )

        for url, info in tree.items():
            if "parents" in info and info["parents"]:
                first_parent = info["parents"][0]
                if first_parent in tree:
                    G.add_edge(first_parent, url)

        return G

    @staticmethod
    def create_shortest_path_tree(G: nx.DiGraph, start_url: str) -> nx.DiGraph:
        """Converte in Shortest Path Tree."""
        spt_edges = list(nx.bfs_edges(G, start_url))
        G_spt = nx.DiGraph()

        for node in G.nodes():
            G_spt.add_node(node, **G.nodes[node])

        for edge in spt_edges:
            G_spt.add_edge(edge[0], edge[1])

        distances = nx.single_source_shortest_path_length(G_spt, start_url)
        for node in G_spt.nodes():
            G_spt.nodes[node]["distance"] = distances.get(node, 0)

        return G_spt
