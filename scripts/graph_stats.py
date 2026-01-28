import networkx as nx
from urllib.parse import urlparse
from node_styler import NodeStyler


class GraphStats:
    @staticmethod
    def print_statistics(G: nx.DiGraph) -> None:
        """Stampa le statistiche del grafo."""
        print("\n[STATS] Statistiche del grafo:")
        print(f"   Nodi totali: {G.number_of_nodes()}")
        print(f"   Archi totali: {G.number_of_edges()}")

        status_counts = GraphStats._count_node_types(G)
        GraphStats._print_node_types(status_counts)
        GraphStats._print_central_node(G)

    @staticmethod
    def _count_node_types(G: nx.DiGraph) -> dict:
        """Conta i nodi per tipo."""
        status_counts = {}
        for node in G.nodes():
            node_type = NodeStyler.get_node_type(G.nodes[node])
            status_counts[node_type] = status_counts.get(node_type, 0) + 1
        return status_counts

    @staticmethod
    def _print_node_types(status_counts: dict) -> None:
        """Stampa il conteggio per tipo."""
        print(f"\n[TYPES] Tipologia nodi:")
        print(f"   Pagina iniziale: {status_counts.get('start', 0)}")
        print(f"   Trasparenza: {status_counts.get('transparency', 0)}")
        print(f"   Funzionanti: {status_counts.get('ok', 0)}")
        print(f"   Rotti: {status_counts.get('broken', 0)}")
        print(f"   File: {status_counts.get('file', 0)}")
        print(f"   Dinamici: {status_counts.get('dynamic', 0)}")
        print(f"   In attesa: {status_counts.get('pending', 0)}")

    @staticmethod
    def _print_central_node(G: nx.DiGraph) -> None:
        """Stampa il nodo più centrale."""
        if G.number_of_nodes() > 0:
            centrality = nx.degree_centrality(G)
            central_node = max(centrality.items(), key=lambda x: x[1])
            print(f"\n[CENTRAL] Nodo piu centrale: {urlparse(central_node[0]).path}")
