import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from evaluador import decodificar


def gantt(inst, secuencia, ruta_salida, titulo=None):
    programa = decodificar(inst, secuencia)
    makespan = max(op[4] for op in programa)
    colores = plt.get_cmap("tab20" if inst.n <= 20 else "hsv")

    alto = max(3, 0.5 * inst.m + 1)
    fig, ax = plt.subplots(figsize=(12, alto))
    for (j, k, maq, ini, fin) in programa:
        color = colores(j / max(1, inst.n - 1)) if inst.n > 20 else colores(j % 20)
        ax.barh(maq, fin - ini, left=ini, color=color, edgecolor="black", linewidth=0.4)
        if inst.n <= 15:
            ax.text((ini + fin) / 2, maq, f"J{j}", ha="center", va="center", fontsize=7)

    ax.set_yticks(range(inst.m))
    ax.set_yticklabels([f"M{i}" for i in range(inst.m)])
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo")
    ax.axvline(makespan, color="red", linestyle="--", linewidth=1)
    ax.set_title(titulo or f"{inst.nombre} - makespan {makespan}")
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)


def boxplots(resultados, ruta_salida):
    nombres = list(resultados.keys())
    fig, ejes = plt.subplots(1, len(nombres), figsize=(4 * len(nombres), 4))
    if len(nombres) == 1:
        ejes = [ejes]
    for ax, nombre in zip(ejes, nombres):
        ax.boxplot(resultados[nombre])
        ax.set_title(nombre)
        ax.set_xticks([])
        ax.set_ylabel("Makespan")
    fig.suptitle("Makespan en las ejecuciones del SA")
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)


def convergencia(historiales, ruta_salida, titulo):
    fig, ax = plt.subplots(figsize=(8, 4))
    for h in historiales:
        xs, ys = zip(*h)
        ax.step(xs, ys, where="post", alpha=0.6, linewidth=1)
    ax.set_xlabel("Evaluaciones")
    ax.set_ylabel("Mejor makespan")
    ax.set_title(titulo)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)