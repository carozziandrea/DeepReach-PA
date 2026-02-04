"""
Graph Visualizer - Genera visualizzazioni interattive HTML dei grafi.

Questo modulo utilizza PyVis per creare visualizzazioni force-directed
dei grafi del sito web, con funzionalità di:
- Stili nodi personalizzati basati su tipo e rischio privacy
- Legenda interattiva
- Statistiche del grafo
- Controlli per navigazione e zoom
"""

import networkx as nx
from pyvis.network import Network
import json
import re
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
        self._configure_all_options(net, node_count)
        self._add_nodes(net, G)
        self._add_edges(net, G)
        net.save_graph(output_file)

        # Inietta legenda, statistiche e controlli nell'HTML
        stats = self._calculate_stats(G)
        self._inject_custom_html(output_file, stats, node_count)

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

    def _calculate_stats(self, G: nx.DiGraph) -> dict:
        """Calcola le statistiche del grafo."""
        stats = {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "node_types": {},
            "privacy_risks": {"high": 0, "medium": 0, "low": 0, "none": 0},
            "max_depth": 0,
            "avg_depth": 0,
        }

        depths = []
        for node in G.nodes():
            node_data = G.nodes[node]
            node_type = NodeStyler.get_node_type(node_data)
            stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1

            # Privacy risk
            risk = node_data.get("privacy_risk", "none")
            if risk in stats["privacy_risks"]:
                stats["privacy_risks"][risk] += 1

            # Depth
            depth = node_data.get("depth", 0)
            depths.append(depth)

        if depths:
            stats["max_depth"] = max(depths)
            stats["avg_depth"] = sum(depths) / len(depths)

        return stats

    def _inject_custom_html(self, output_file: str, stats: dict, node_count: int) -> None:
        """Inietta legenda, statistiche e controlli nell'HTML generato."""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Genera HTML custom
            legend_html = self._generate_legend_html()
            stats_html = self._generate_stats_html(stats)
            controls_html = self._generate_controls_html(node_count)
            css = self._generate_custom_css()

            # Inietta CSS prima di </head>
            html_content = html_content.replace('</head>', f'{css}</head>')

            # Inietta pannelli prima di </body>
            panels_html = f'''
    <div id="graph-panels">
        {legend_html}
        {stats_html}
        {controls_html}
    </div>
'''
            html_content = html_content.replace('</body>', f'{panels_html}</body>')

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            print(f"[WARN] Impossibile iniettare HTML custom: {e}")

    def _generate_custom_css(self) -> str:
        """Genera CSS per i pannelli custom."""
        return '''
    <style>
        #graph-panels {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 90vh;
            overflow-y: auto;
        }

        .graph-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            padding: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
            min-width: 180px;
            max-width: 220px;
        }

        .graph-panel h3 {
            margin: 0 0 10px 0;
            font-size: 13px;
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 6px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin: 6px 0;
            gap: 8px;
        }

        .legend-symbol {
            width: 16px;
            height: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }

        .legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .legend-star {
            color: #D0021B;
            font-size: 14px;
        }

        .legend-triangle {
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-bottom: 12px solid #D0021B;
        }

        .legend-diamond {
            width: 10px;
            height: 10px;
            background: #9D65C9;
            transform: rotate(45deg);
        }

        .legend-label {
            color: #555;
            flex: 1;
        }

        .legend-count {
            color: #888;
            font-weight: bold;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
            padding: 2px 0;
        }

        .stat-label {
            color: #666;
        }

        .stat-value {
            font-weight: bold;
            color: #333;
        }

        .privacy-section {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #eee;
        }

        .privacy-high { color: #D0021B; }
        .privacy-medium { color: #F5A623; }
        .privacy-low { color: #F5D623; }

        .control-btn {
            width: 100%;
            padding: 6px 10px;
            margin: 4px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #f8f8f8;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
        }

        .control-btn:hover {
            background: #e8e8e8;
            border-color: #ccc;
        }

        .control-btn.active {
            background: #4A90E2;
            color: white;
            border-color: #4A90E2;
        }

        #toggle-panels {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1001;
            padding: 8px 12px;
            background: #4A90E2;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }

        #toggle-panels:hover {
            background: #3A80D2;
        }

        .panels-hidden #graph-panels {
            display: none;
        }
    </style>
'''

    def _generate_legend_html(self) -> str:
        """Genera l'HTML della legenda."""
        return '''
        <div class="graph-panel" id="legend-panel">
            <h3>Legenda</h3>
            <div class="legend-item">
                <div class="legend-symbol legend-star">★</div>
                <span class="legend-label">Pagina iniziale</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-dot" style="background:#17A2B8"></div></div>
                <span class="legend-label">Sezione trasparenza</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-dot" style="background:#4A90E2"></div></div>
                <span class="legend-label">Pagina OK</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-triangle"></div></div>
                <span class="legend-label">Link rotto</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-dot" style="background:#7ED321"></div></div>
                <span class="legend-label">File (PDF, etc.)</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-diamond"></div></div>
                <span class="legend-label">Contenuto dinamico</span>
            </div>
            <div class="legend-item">
                <div class="legend-symbol"><div class="legend-dot" style="background:#F5A623"></div></div>
                <span class="legend-label">In attesa</span>
            </div>
            <div class="privacy-section">
                <strong>Bordi Privacy:</strong>
                <div class="legend-item">
                    <div class="legend-symbol"><div class="legend-dot" style="background:#fff;border:3px solid #FF0000"></div></div>
                    <span class="legend-label privacy-high">Rischio ALTO</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol"><div class="legend-dot" style="background:#fff;border:2px solid #FFA500"></div></div>
                    <span class="legend-label privacy-medium">Rischio MEDIO</span>
                </div>
            </div>
        </div>
'''

    def _generate_stats_html(self, stats: dict) -> str:
        """Genera l'HTML delle statistiche."""
        node_types = stats["node_types"]
        privacy = stats["privacy_risks"]

        return f'''
        <div class="graph-panel" id="stats-panel">
            <h3>Statistiche</h3>
            <div class="stat-row">
                <span class="stat-label">Nodi totali:</span>
                <span class="stat-value">{stats["total_nodes"]}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Archi totali:</span>
                <span class="stat-value">{stats["total_edges"]}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Profondita max:</span>
                <span class="stat-value">{stats["max_depth"]} click</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Profondita media:</span>
                <span class="stat-value">{stats["avg_depth"]:.1f} click</span>
            </div>

            <div class="privacy-section">
                <strong>Tipologia nodi:</strong>
                <div class="stat-row">
                    <span class="stat-label">Trasparenza:</span>
                    <span class="stat-value">{node_types.get("transparency", 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Funzionanti:</span>
                    <span class="stat-value">{node_types.get("ok", 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Link rotti:</span>
                    <span class="stat-value" style="color:#D0021B">{node_types.get("broken", 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">File:</span>
                    <span class="stat-value">{node_types.get("file", 0)}</span>
                </div>
            </div>

            <div class="privacy-section">
                <strong>Rischio Privacy:</strong>
                <div class="stat-row">
                    <span class="stat-label privacy-high">Alto:</span>
                    <span class="stat-value">{privacy["high"]}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label privacy-medium">Medio:</span>
                    <span class="stat-value">{privacy["medium"]}</span>
                </div>
            </div>
        </div>
'''

    def _generate_controls_html(self, node_count: int) -> str:
        """Genera controlli per grafi grandi."""
        # Mostra controlli solo per grafi con molti nodi
        if node_count < 100:
            return ''

        return '''
        <div class="graph-panel" id="controls-panel">
            <h3>Controlli</h3>
            <button class="control-btn" onclick="fitGraph()">Adatta alla vista</button>
            <button class="control-btn" onclick="togglePhysics()">Pausa/Riprendi fisica</button>
            <button class="control-btn" onclick="highlightBroken()">Evidenzia link rotti</button>
            <button class="control-btn" onclick="highlightPrivacy()">Evidenzia rischio privacy</button>
            <button class="control-btn" onclick="resetHighlight()">Reset evidenziazione</button>
        </div>
        <script>
            var physicsEnabled = true;

            function fitGraph() {
                network.fit({animation: true});
            }

            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
                network.setOptions({physics: {enabled: physicsEnabled}});
            }

            function highlightBroken() {
                var nodes = network.body.data.nodes;
                nodes.forEach(function(node) {
                    if (node.shape === 'triangle') {
                        nodes.update({id: node.id, borderWidth: 5, size: node.size * 1.5});
                    }
                });
            }

            function highlightPrivacy() {
                var nodes = network.body.data.nodes;
                nodes.forEach(function(node) {
                    if (node.color && node.color.border && (node.color.border === '#FF0000' || node.color.border === '#FFA500')) {
                        nodes.update({id: node.id, size: node.size * 1.5});
                    }
                });
            }

            function resetHighlight() {
                network.fit({animation: true});
                location.reload();
            }
        </script>
'''
