"""
Graph Builder - Costruisce grafi NetworkX dai dati JSON del crawl.

Questo modulo fornisce la classe GraphBuilder che:
- Carica i dati JSON prodotti dal crawler
- Costruisce grafi NetworkX con metadati sui nodi
- Classifica i nodi come sezioni di trasparenza
- Crea lo Shortest Path Tree per la visualizzazione

Nota: TRANSPARENCY_SECTIONS è duplicato da orchestrator/config.py
per permettere l'uso standalone degli script di visualizzazione.
"""

import networkx as nx
import json
from typing import Tuple, Optional

# Sezioni obbligatorie per la trasparenza PA (stesso formato di orchestrator/config.py)
TRANSPARENCY_SECTIONS = {
    # 1 - Disposizioni generali
    "disposizioni_generali": [
        "disposizioni-generali", "piano-triennale", "piano-prevenzione",
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
        "consulenti", "collaboratori", "incarichi", "professionisti"
    ],
    # 4 - Personale
    "personale": [
        "personale", "dotazione", "dirigenti", "posizioni-organizzative",
        "contrattazione", "assenze", "tassi-assenza"
    ],
    # 5 - Bandi di concorso
    "bandi_concorso": [
        "bandi-concorso", "concorsi", "selezioni", "avvisi-selezione",
        "graduatorie"
    ],
    # 6 - Performance
    "performance": [
        "performance", "obiettivi", "valutazione", "piano-performance"
    ],
    # 7 - Enti controllati
    "enti_controllati": [
        "enti-controllati", "societa-partecipate", "partecipate",
        "enti-pubblici", "fondazioni", "associazioni-partecipate",
        "rappresentazione-grafica"
    ],
    # 8 - Attività e procedimenti
    "attivita_procedimenti": [
        "procedimenti", "attivita", "modulistica", "tempi",
        "tipologie-procedimento"
    ],
    # 9 - Provvedimenti
    "provvedimenti": [
        "provvedimenti", "delibere", "determine", "ordinanze",
        "decreti", "atti-dirigenziali", "atti-organi-indirizzo"
    ],
    # 10 - Controlli sulle imprese
    "controlli_imprese": [
        "controlli-imprese", "controlli-sulle-imprese",
        "autorizzazioni", "concessioni"
    ],
    # 11 - Bandi di gara e contratti
    "bandi_gare": [
        "bandi-gara", "gare", "appalti", "contratti",
        "procedure-negoziate", "affidamenti"
    ],
    # 12 - Sovvenzioni, contributi, sussidi, vantaggi economici
    "sovvenzioni": [
        "sovvenzioni", "contributi", "sussidi", "vantaggi-economici",
        "benefici-economici"
    ],
    # 13 - Bilanci
    "bilanci": [
        "bilancio", "bilanci", "rendiconto", "piano-indicatori",
        "patrimonio", "spese", "entrate"
    ],
    # 14 - Beni immobili e gestione patrimonio
    "beni_immobili": [
        "beni-immobili", "patrimonio-immobiliare", "canoni-locazione",
        "canoni-affitto", "beni-demaniali"
    ],
    # 15 - Controlli e rilievi sull'amministrazione
    "controlli_amministrazione": [
        "controlli-rilievi", "organi-revisione", "corte-dei-conti",
        "relazioni-revisori", "nuclei-valutazione"
    ],
    # 16 - Servizi erogati
    "servizi_erogati": [
        "servizi-erogati", "carta-servizi", "costi-contabilizzati",
        "liste-attesa", "tempi-medi-erogazione"
    ],
    # 17 - Pagamenti dell'amministrazione
    "pagamenti": [
        "pagamenti", "indicatore-tempestivita", "iban",
        "pagamento-informatico", "dati-pagamenti"
    ],
    # 18 - Opere pubbliche
    "opere_pubbliche": [
        "opere-pubbliche", "lavori-pubblici", "nuclei-valutazione-verifica",
        "oopp"
    ],
    # 19 - Pianificazione e governo del territorio
    "pianificazione_territorio": [
        "pianificazione-territorio", "governo-territorio",
        "piano-urbanistico", "prg", "pgt", "strumenti-urbanistici"
    ],
    # 20 - Informazioni ambientali
    "informazioni_ambientali": [
        "informazioni-ambientali", "ambiente", "vinca", "via",
        "valutazione-impatto-ambientale"
    ],
    # 21 - Interventi straordinari e di emergenza
    "interventi_emergenza": [
        "emergenza", "interventi-straordinari", "protezione-civile",
        "calamita", "commissari"
    ],
    # 22 - Altri contenuti - Accesso civico
    "accesso_civico": [
        "accesso-civico", "accesso-generalizzato", "foia",
        "accesso-documenti", "richieste-accesso"
    ],
    # 23 - Altri contenuti - Accessibilità e dati
    "accessibilita_dati": [
        "accessibilita", "catalogo-dati", "open-data", "dati-aperti",
        "metadati", "banche-dati"
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
