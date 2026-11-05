import math
import random

from evaluador import makespan, secuencia_aleatoria


def vecino(secuencia, rng, p_swap=0.5):
    s = secuencia[:]
    largo = len(s)

    if rng.random() < p_swap:
        while True:
            i, j = rng.randrange(largo), rng.randrange(largo)
            if s[i] != s[j]:
                break
        s[i], s[j] = s[j], s[i]
    else:
        i, j = rng.randrange(largo), rng.randrange(largo)
        while i == j:
            j = rng.randrange(largo)
        s.insert(j, s.pop(i))

    return s


def temperatura_inicial(inst, secuencia, rng, muestras=100, aceptacion=0.8, p_swap=0.5):
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
    rng = random.Random(semilla)
    if L is None:
        L = inst.n * inst.m

    actual = secuencia_aleatoria(inst, rng)
    valor_actual = makespan(inst, actual)
    evals = 1

    T0, usadas = temperatura_inicial(inst, actual, rng, aceptacion=aceptacion_inicial, p_swap=p_swap)
    evals += usadas
    T = T0
    T_final = T0 * razon_tf

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

            if delta <= 0 or rng.random() < math.exp(-delta / T):
                actual, valor_actual = candidato, valor_cand
                if valor_actual < valor_mejor:
                    mejor, valor_mejor = actual[:], valor_actual

            if evals % registrar_cada == 0:
                historial.append((evals, valor_mejor))

        T *= alpha

    historial.append((evals, valor_mejor))
    return {
        "mejor_secuencia": mejor,
        "mejor_makespan": valor_mejor,
        "evaluaciones": evals,
        "T0": T0,
        "alpha": alpha,
        "historial": historial,
    }