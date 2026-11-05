import argparse
import csv
import os
import statistics
import sys
import time

sys.dont_write_bytecode = True

from instancia import leer_instancia
from sa import simulated_annealing
from graficos import gantt, boxplots, convergencia

INSTANCIAS = ["01_facil.txt", "02_medio.txt", "03_dificil.txt"]


def main():
    parser = argparse.ArgumentParser(description="Experimentos del SA para el JSP")
    parser.add_argument("--presupuesto", type=int, default=100_000)
    parser.add_argument("--ejecuciones", type=int, default=10)
    parser.add_argument("--salida", default="resultados")
    args = parser.parse_args()

    carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instancias")
    os.makedirs(args.salida, exist_ok=True)

    makespans = {}
    filas_csv = []

    for archivo in INSTANCIAS:
        inst = leer_instancia(os.path.join(carpeta, archivo))
        nombre = os.path.splitext(archivo)[0]
        print(f"\n{inst} | cota inferior {inst.cota_inferior()}")

        valores, historiales = [], []
        mejor_global = None
        for semilla in range(1, args.ejecuciones + 1):
            t0 = time.perf_counter()
            res = simulated_annealing(inst, presupuesto=args.presupuesto, semilla=semilla)
            dur = time.perf_counter() - t0

            valores.append(res["mejor_makespan"])
            historiales.append(res["historial"])
            filas_csv.append([nombre, semilla, res["mejor_makespan"], round(dur, 3)])
            if mejor_global is None or res["mejor_makespan"] < mejor_global["mejor_makespan"]:
                mejor_global = res
            print(f"  ejecucion {semilla:2d}: makespan {res['mejor_makespan']}  ({dur:.1f} s)")

        makespans[nombre] = valores
        convergencia(historiales, os.path.join(args.salida, f"convergencia_{nombre}.png"),
                     f"Convergencia SA - {nombre}")
        gantt(inst, mejor_global["mejor_secuencia"],
              os.path.join(args.salida, f"gantt_{nombre}.png"))

    with open(os.path.join(args.salida, "resultados.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["instancia", "semilla", "makespan", "tiempo_s"])
        w.writerows(filas_csv)

    boxplots(makespans, os.path.join(args.salida, "boxplots.png"))

    nombres = list(makespans.keys())
    print(f"\nResumen ({args.ejecuciones} ejecuciones, presupuesto {args.presupuesto})")
    print("ejecucion " + "".join(f"{n:>14}" for n in nombres))
    for i in range(args.ejecuciones):
        print(f"{i + 1:>9} " + "".join(f"{makespans[n][i]:>14}" for n in nombres))
    print(f"{'mejor':>9} " + "".join(f"{min(makespans[n]):>14}" for n in nombres))
    print(f"{'media':>9} " + "".join(f"{statistics.mean(makespans[n]):>14.2f}" for n in nombres))
    print(f"{'desv.est.':>9} " + "".join(f"{statistics.stdev(makespans[n]):>14.2f}" for n in nombres))
    print(f"\nArchivos guardados en la carpeta '{args.salida}'")


if __name__ == "__main__":
    main()