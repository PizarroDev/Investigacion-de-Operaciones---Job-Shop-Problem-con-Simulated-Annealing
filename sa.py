import math
import random

from evaluador import makespan, secuencia_aleatoria


def vecino(secuencia, rng, p_swap=0.5):
    """Genera un vecino aplicando swap (prob. p_swap) o insert."""
    s = secuencia[:]          # copia, para no modificar la solucion actual
    largo = len(s)

    if rng.random() < p_swap:
        # SWAP: intercambiar dos posiciones con trabajos distintos
        # (intercambiar el mismo trabajo no cambia la solucion)
        while True:
            i, j = rng.randrange(largo), rng.randrange(largo)
            if s[i] != s[j]:
                break
        s[i], s[j] = s[j], s[i]
    else:
        # INSERT: sacar el elemento de la posicion i e insertarlo en j
        i, j = rng.randrange(largo), rng.randrange(largo)
        while i == j:
            j = rng.randrange(largo)
        s.insert(j, s.pop(i))

    return s


def temperatura_inicial(inst, secuencia, rng, muestras=100, aceptacion=0.8, p_swap=0.5):
    """
    Estima T0 a partir de movimientos aleatorios desde 'secuencia':
    T0 = -delta_promedio / ln(aceptacion), usando solo los deltas positivos.
    Asi, al comienzo se acepta aprox. el 80% de los empeoramientos.
    Retorna (T0, evaluaciones usadas).
    """
    valor = makespan(inst, secuencia)
    deltas = []
    for _ in range(muestras):
        delta = makespan(inst, vecino(secuencia, rng, p_swap)) - valor
        if delta > 0:
            deltas.append(delta)
    if not deltas:
        return 1.0, muestras
    promedio = sum(deltas) / len(deltas)
    return -promedio / math.log(aceptacion), muestras


def simulated_annealing(inst, presupuesto=100_000, semilla=1, L=None,
                        razon_tf=0.001, aceptacion_inicial=0.8, p_swap=0.5,
                        registrar_cada=1000):
    """
    Ejecuta el SA y retorna un diccionario con:
      mejor_secuencia, mejor_makespan, evaluaciones, historial
    'historial' es una lista de (evaluaciones, mejor_makespan) para
    graficar la convergencia.
    """
    rng = random.Random(semilla)
    if L is None:
        L = inst.n * inst.m        # iteraciones por nivel de temperatura

    # Solucion inicial
    actual = secuencia_aleatoria(inst, rng)
    valor_actual = makespan(inst, actual)
    evals = 1

    # Temperatura inicial (sus evaluaciones cuentan en el presupuesto)
    T0, usadas = temperatura_inicial(inst, actual, rng, aceptacion=aceptacion_inicial, p_swap=p_swap)
    evals += usadas
    T = T0
    T_final = T0 * razon_tf

    # alpha para que T llegue a T_final al agotar el presupuesto
    niveles = max(1, (presupuesto - evals) // L)
    alpha = (T_final / T0) ** (1.0 / niveles)

    mejor, valor_mejor = actual[:], valor_actual
    historial = [(evals, valor_mejor)]

    while evals < presupuesto:
        for _ in range(L):
            if evals >= presupuesto:
                break
            candidato = vecino(actual, rng, p_swap)
            valor_cand = makespan(inst, candidato)
            evals += 1
            delta = valor_cand - valor_actual

            # Criterio de Metropolis
            if delta <= 0 or rng.random() < math.exp(-delta / T):
                actual, valor_actual = candidato, valor_cand
                if valor_actual < valor_mejor:
                    mejor, valor_mejor = actual[:], valor_actual

            if evals % registrar_cada == 0:
                historial.append((evals, valor_mejor))

        T *= alpha   # enfriamiento geometrico

    historial.append((evals, valor_mejor))
    return {
        "mejor_secuencia": mejor,
        "mejor_makespan": valor_mejor,
        "evaluaciones": evals,
        "T0": T0,
        "alpha": alpha,
        "historial": historial,
    }