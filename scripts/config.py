"""
Visualization Config - Configurazione per la visualizzazione del grafo.

Definisce parametri per PyVis: dimensioni, colori, fisica e adattamento
automatico dei parametri in base al numero di nodi nel grafo.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class VisualizationConfig:
    """Configurazione per la visualizzazione del grafo."""

    height: str = "900px"
    width: str = "100%"
    bgcolor: str = "#ffffff"

    # Physics base (verranno adattati in base al numero di nodi)
    gravitational_constant: int = -100
    central_gravity: float = 0.01
    spring_length: int = 100
    spring_constant: float = 0.08
    damping: float = 0.4

    # Nodes
    min_node_size: int = 10
    max_node_size: int = 30
    base_node_size: int = 20
    centrality_multiplier: int = 30

    # Paths
    input_file: str = "./output/site_tree.json"
    output_file: str = "./output/force_directed_graph.html"

    # Soglie per adattamento physics
    SMALL_GRAPH_THRESHOLD: int = 100
    MEDIUM_GRAPH_THRESHOLD: int = 500

    def get_adaptive_physics_params(self, node_count: int) -> Dict[str, Any]:
        """
        Calcola parametri physics adattivi in base al numero di nodi.

        Args:
            node_count: Numero di nodi nel grafo

        Returns:
            Dizionario con i parametri physics adattati
        """
        if node_count <= self.SMALL_GRAPH_THRESHOLD:
            # Grafo piccolo: parametri base
            return {
                "gravitational_constant": -100,
                "central_gravity": 0.01,
                "spring_length": 100,
                "spring_constant": 0.08,
                "damping": 0.4,
                "stabilization_iterations": 1000,
            }
        elif node_count <= self.MEDIUM_GRAPH_THRESHOLD:
            # Grafo medio: aumenta separazione
            return {
                "gravitational_constant": -200,
                "central_gravity": 0.02,
                "spring_length": 150,
                "spring_constant": 0.05,
                "damping": 0.5,
                "stabilization_iterations": 1500,
            }
        else:
            # Grafo grande: massima separazione
            # Scala logaritmicamente per grafi molto grandi
            import math
            scale_factor = math.log10(node_count / 500) + 1
            return {
                "gravitational_constant": int(-300 * scale_factor),
                "central_gravity": 0.03,
                "spring_length": int(200 * scale_factor),
                "spring_constant": 0.03,
                "damping": 0.6,
                "stabilization_iterations": 2000,
            }

    def get_physics_options(self, node_count: int = 0) -> dict:
        """
        Ritorna le opzioni di fisica, adattate al numero di nodi.

        Args:
            node_count: Numero di nodi nel grafo (0 = usa parametri base)
        """
        if node_count > 0:
            params = self.get_adaptive_physics_params(node_count)
            grav_const = params["gravitational_constant"]
            central_grav = params["central_gravity"]
            spring_len = params["spring_length"]
            spring_const = params["spring_constant"]
            damp = params["damping"]
            stab_iter = params["stabilization_iterations"]
        else:
            # Usa parametri base dell'istanza
            grav_const = self.gravitational_constant
            central_grav = self.central_gravity
            spring_len = self.spring_length
            spring_const = self.spring_constant
            damp = self.damping
            stab_iter = 1000

        return {
            "forceAtlas2Based": {
                "gravitationalConstant": grav_const,
                "centralGravity": central_grav,
                "springLength": spring_len,
                "springConstant": spring_const,
                "damping": damp,
                "avoidOverlap": 1,
            },
            "minVelocity": 2.00,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": True,
                "onlyDynamicEdges": False,
                "iterations": stab_iter,
                "updateInterval": 100,
                "fit": True,
            },
        }
