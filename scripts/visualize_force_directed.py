from graph_builder import GraphBuilder
from graph_stats import GraphStats
from graph_visualizer import GraphVisualizer
from config import VisualizationConfig


def main():
    """Funzione principale dello script."""
    try:
        config = VisualizationConfig()

        # Carica e costruisci il grafo
        data = GraphBuilder.load_data(config.input_file)
        start_url = GraphBuilder.find_root_node(data["tree"])
        G = GraphBuilder.build_graph(data["tree"], start_url)
        G_spt = GraphBuilder.create_shortest_path_tree(G, start_url)

        # Statistiche
        GraphStats.print_statistics(G_spt)

        # Visualizza
        visualizer = GraphVisualizer(config)
        visualizer.visualize(G_spt, config.output_file)

    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
