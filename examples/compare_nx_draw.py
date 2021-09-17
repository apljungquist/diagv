import matplotlib.pyplot as plt
import networkx as nx

from diagv import generators


def without_prefix(text: str, prefix: str, missing_ok: bool = False) -> str:
    if not text.startswith(prefix):
        if missing_ok:
            return text
        raise ValueError(f"{text} does not have prefix {prefix}")
    return text[len(prefix) :]


def compare(graphs):
    funcs = [
        nx.draw_circular,
        nx.draw_kamada_kawai,
        nx.draw_planar,
        nx.draw_spectral,
        nx.draw_spring,
        # nx.draw_shell,
        # nx.draw,
        # nx.draw_networkx,
    ]
    fig, axs = plt.subplots(len(graphs), len(funcs))
    for i, (name, graph) in enumerate(graphs.items()):
        for j, draw in enumerate(funcs):
            ax = axs[i, j]
            if not i:
                ax.set_title(without_prefix(draw.__name__, "draw_", True))
            draw(graph, ax=ax)
    plt.show()


if __name__ == "__main__":
    compare(
        {
            "dibull()": generators.dibull(),
            "diline(4)": generators.diline(4),
            "distar(4)": generators.distar(4),
            "distar(-4)": generators.distar(-4),
            "ditutte_fragment()": generators.ditutte_fragment(),
            "ditutte()": generators.ditutte(),
            # "tutte_graph()":nx.generators.tutte_graph(),
            # "gn_graph(5)":nx.generators.gn_graph(5),
            # "gnr_graph(5, 0.5)":nx.generators.gnr_graph(5, 0.5),
            # "gnc_graph(5)":nx.generators.gnc_graph(5),
            # "random_k_out_graph(5, 3, 0.5)":nx.generators.random_k_out_graph(5, 3, 0.5),
            # "scale_free_graph(5)":nx.generators.scale_free_graph(5),
        }
    )
