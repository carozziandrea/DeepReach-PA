import networkx as nx
from pyvis.network import Network
import json
from node_styler import NodeStyler


class GraphVisualizer:
    """Gestisce la visualizzazione del grafo con PyVis."""

    def __init__(self, config):
        """Inizializza il visualizzatore con la configurazione."""
        self.config = config

    def visualize(self, G: nx.DiGraph, output_file: str) -> None:
        """Crea e salva la visualizzazione del grafo."""
        node_count = G.number_of_nodes()
        print(f"[GRAPH] Visualizzazione grafo con {node_count} nodi")

        net = self._create_network()
        self._configure_all_options(net, node_count)  # ← Passa numero nodi per physics adattivi
        self._add_nodes(net, G)
        self._add_edges(net, G)
        net.save_graph(output_file)
        print(f"\n[OK] Grafo salvato in: {output_file}")

    def _create_network(self) -> Network:
        """Crea la rete PyVis con la configurazione."""
        return Network(
            height=self.config.height,
            width=self.config.width,
            bgcolor=self.config.bgcolor,
            font_color="black",
            directed=True,
            notebook=False,  # ← Aggiunto per coerenza
        )

    def _configure_all_options(self, net: Network, node_count: int = 0) -> None:
        """Configura tutte le opzioni del grafo (physics, layout, edges, ecc.)."""
        options = {
            "physics": self.config.get_physics_options(node_count),
            "layout": {
                "randomSeed": 42,
                "improvedLayout": True
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                },
                "arrows": {
                    "to": {
                        "enabled": True,
                        "scaleFactor": 0.5
                    }
                }
            },
            "nodes": {
                "shape": "dot",
                "scaling": {
                    "min": 10,
                    "max": 30,
                    "label": {
                        "enabled": True,
                        "min": 8,
                        "max": 20,
                        "drawThreshold": 12,
                        "maxVisible": 30
                    }
                }
            },
            "font": {
                "color": "black",
                "size": 12,
                "strokeWidth": 2,
                "strokeColor": "#ffffff"
            },
            "interaction": {
                "navigationButtons": True,
                "keyboard": True,
                "hover": True,
                "zoomView": True,
                "hideEdgesOnZoom": True
            }
        }

        net.set_options(json.dumps(options))

    def _add_nodes(self, net: Network, G: nx.DiGraph) -> None:
        """Aggiunge i nodi alla rete."""
        centrality = nx.degree_centrality(G)

        for node in G.nodes():
            node_data = G.nodes[node]
            node_type = NodeStyler.get_node_type(node_data)
            style = NodeStyler.get_style(node_type)
            degree = G.degree(node)

            # Calcola dimensione (include bonus per start)
            size = self._calculate_node_size(centrality.get(node, 0), node_type)

            # Formatta label e tooltip
            label = self._format_label(node_data)
            tooltip = NodeStyler.format_tooltip(node, node_data, node_type, degree)

            # Ottieni stile privacy (bordo colorato per nodi a rischio)
            privacy_style = NodeStyler.get_privacy_style(node_data)

            # Usa border_width e border_color da privacy se presenti
            border_width = privacy_style.get("border_width", style["border_width"])
            border_color = privacy_style.get("border_color")

            # Costruisci colore nodo: se privacy ha bordo, usa color dict con border
            if border_color:
                node_color = {
                    "background": style["color"],
                    "border": border_color,
                    "highlight": {
                        "background": style["color"],
                        "border": border_color
                    }
                }
            else:
                node_color = style["color"]

            net.add_node(
                node,
                label=label,
                title=tooltip,
                size=size,
                color=node_color,
                shape=style["shape"],
                borderWidth=border_width,
                borderWidthSelected=max(5, border_width + 1),
                hidden=False,
                physics=True,
                labelHighlightBold=True
            )

    def _add_edges(self, net: Network, G: nx.DiGraph) -> None:
        """Aggiunge gli archi alla rete."""
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])

    def _calculate_node_size(self, centrality: float, node_type: str) -> int:
        """Calcola la dimensione del nodo in base alla centralità."""
        base_size = self.config.base_node_size + (
                centrality * self.config.centrality_multiplier
        )

        # Aggiungi bonus per nodo start
        size = base_size + (20 if node_type == "start" else 0)

        return max(
            self.config.min_node_size,
            min(size, self.config.max_node_size + 20)  # +20 per permettere il bonus start
        )

    def _format_label(self, node_data: dict) -> str:
        """Formatta l'etichetta del nodo."""
        node_type = NodeStyler.get_node_type(node_data)
        style = NodeStyler.get_style(node_type)
        emoji = style["emoji"]

        # Usa display_name
        base_label = node_data.get("display_name", "unknown")
        return f"{emoji} {base_label}"
