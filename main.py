import argparse
import os
import sys
import time

sys.dont_write_bytecode = True 

from instancia import leer_instancia
from sa import simulated_annealing
from evaluador import decodificar, verificar_programa

def main():
    parser = argparse.ArgumentParser(description="Simulated Annealing para el JSP")
    parser.add_argument("instancia", help="ruta del archivo de instancia")
    parser.add_argument("--semilla", type=int, default=1, help="semilla aleatoria (default 1)")
    parser.add_argument("--presupuesto", type=int, default=100_000,
                        help="numero maximo de evaluaciones (default 100000)")
    parser.add_argument("--gantt", action="store_true",
                        help="guarda el diagrama de Gantt de la mejor solucion")
    args = parser.parse_args()

    inst = leer_instancia(args.instancia)
    print(inst)
    print(f"Cota inferior: {inst.cota_inferior()}")
    print(f"Semilla: {args.semilla} | Presupuesto: {args.presupuesto} evaluaciones")

    inicio = time.perf_counter()
    res = simulated_annealing(inst, presupuesto=args.presupuesto, semilla=args.semilla)
    duracion = time.perf_counter() - inicio

    # Verificacion independiente de la solucion final
    factible = verificar_programa(inst, decodificar(inst, res["mejor_secuencia"]))

    print(f"\nMejor makespan: {res['mejor_makespan']}")
    print(f"Factible: {'si' if factible else 'NO'}")
    print(f"Evaluaciones: {res['evaluaciones']} | Tiempo: {duracion:.2f} s")
    print(f"T0 = {res['T0']:.2f} | alpha = {res['alpha']:.5f}")
    print(f"Secuencia: {res['mejor_secuencia']}")

    if args.gantt:
        from graficos import gantt
        os.makedirs("resultados", exist_ok=True)
        nombre = os.path.splitext(inst.nombre)[0]
        ruta = os.path.join("resultados", f"gantt_{nombre}_s{args.semilla}.png")
        gantt(inst, res["mejor_secuencia"], ruta)
        print(f"Gantt guardado en {ruta}")


if __name__ == "__main__":
    main()