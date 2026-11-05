import os
import random
import time
import sys


sys.dont_write_bytecode = True 
from instancia import leer_instancia


def makespan(inst, secuencia):
    maquinas, tiempos = inst.maquinas, inst.tiempos
    sig_op = [0] * inst.n        
    fin_trabajo = [0] * inst.n  
    fin_maquina = [0] * inst.m   

    for j in secuencia:
        k = sig_op[j]
        maq = maquinas[j][k]
        inicio = fin_trabajo[j] if fin_trabajo[j] > fin_maquina[maq] else fin_maquina[maq]
        fin = inicio + tiempos[j][k]
        fin_trabajo[j] = fin
        fin_maquina[maq] = fin
        sig_op[j] = k + 1

    return max(fin_trabajo)


def decodificar(inst, secuencia):
    sig_op = [0] * inst.n
    fin_trabajo = [0] * inst.n
    fin_maquina = [0] * inst.m
    programa = []

    for j in secuencia:
        k = sig_op[j]
        maq = inst.maquinas[j][k]
        inicio = max(fin_trabajo[j], fin_maquina[maq])
        fin = inicio + inst.tiempos[j][k]
        fin_trabajo[j] = fin
        fin_maquina[maq] = fin
        sig_op[j] = k + 1
        programa.append((j, k, maq, inicio, fin))

    return programa


def es_secuencia_valida(inst, secuencia):
    if len(secuencia) != inst.n * inst.m:
        return False
    conteo = [0] * inst.n
    for j in secuencia:
        conteo[j] += 1
    return all(c == inst.m for c in conteo)


def verificar_programa(inst, programa):
    por_trabajo = {}
    for (j, k, maq, ini, fin) in programa:
        por_trabajo.setdefault(j, []).append((k, ini, fin))
    for ops in por_trabajo.values():
        ops.sort()
        for a, b in zip(ops, ops[1:]):
            if b[1] < a[2]:
                return False
    por_maquina = {}
    for (j, k, maq, ini, fin) in programa:
        por_maquina.setdefault(maq, []).append((ini, fin))
    for intervalos in por_maquina.values():
        intervalos.sort()
        for a, b in zip(intervalos, intervalos[1:]):
            if b[0] < a[1]:
                return False
    return True


def secuencia_aleatoria(inst, rng):
    """Genera una solucion aleatoria (permutacion con repeticion)."""
    secuencia = [j for j in range(inst.n) for _ in range(inst.m)]
    rng.shuffle(secuencia)
    return secuencia

if __name__ == "__main__":
    carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instancias")
    archivos = ["01_facil.txt", "02_medio.txt", "03_dificil.txt"]
    rng = random.Random(1)

    for archivo in archivos:
        inst = leer_instancia(os.path.join(carpeta, archivo))
        print(inst)
        print(f"  Cota inferior: {inst.cota_inferior()}")

        # Evaluar 1000 soluciones aleatorias y verificar factibilidad
        valores = []
        t0 = time.perf_counter()
        for _ in range(1000):
            s = secuencia_aleatoria(inst, rng)
            valores.append(makespan(inst, s))
        t1 = time.perf_counter()

        s = secuencia_aleatoria(inst, rng)
        assert es_secuencia_valida(inst, s)
        prog = decodificar(inst, s)
        assert verificar_programa(inst, prog), "Programa infactible"
        assert max(op[4] for op in prog) == makespan(inst, s)

        print(f"  1000 soluciones aleatorias: mejor {min(valores)}, "
              f"promedio {sum(valores) / len(valores):.1f}, peor {max(valores)}")
        print(f"  Tiempo por evaluacion: {(t1 - t0) / 1000 * 1e6:.1f} microsegundos")
        print("  Verificacion de factibilidad: OK\n")