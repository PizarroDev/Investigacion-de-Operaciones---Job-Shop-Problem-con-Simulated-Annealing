import argparse
import math
import random
import statistics
import sys
import time

sys.dont_write_bytecode = True

from instancia import leer_instancia
from evaluador import makespan, decodificar, verificar_programa, secuencia_aleatoria
from sa import vecino, simulated_annealing

LIMITE_EXHAUSTIVA = 5_000_000


def tamano_espacio(inst):
    return math.factorial(inst.n * inst.m) // math.factorial(inst.m) ** inst.n


def formato_grande(x):
    return f"{x:,}".replace(",", ".") if x < 10 ** 12 else f"{x:.3e}"


def mostrar_secuencia(secuencia):
    return " ".join(str(j) for j in secuencia)


def leer_soluciones(ruta):
    soluciones = []
    with open(ruta, "r") as f:
        for linea in f:
            linea = linea.split("#")[0].strip()
            if linea:
                soluciones.append([int(x) for x in linea.split()])
    if not soluciones:
        raise ValueError(f"El archivo {ruta} no tiene soluciones")
    return soluciones


def validar(inst, secuencia):
    errores = []
    esperado = inst.n * inst.m
    if len(secuencia) != esperado:
        errores.append(f"largo {len(secuencia)}, se esperaba {esperado} (n*m)")
    fuera = sorted({j for j in secuencia if j < 0 or j >= inst.n})
    if fuera:
        errores.append(f"trabajos que no existen: {fuera} (deben ir de 0 a {inst.n - 1})")
    for j in range(inst.n):
        c = secuencia.count(j)
        if c != inst.m:
            errores.append(f"el trabajo {j} aparece {c} veces, debe aparecer {inst.m} "
                           f"(una por operacion)")
    if not errores:
        if not verificar_programa(inst, decodificar(inst, secuencia)):
            errores.append("el programa tiene solapes o no respeta el orden de un trabajo")
    return (not errores), errores


def evaluar(inst, secuencia):
    ok, errores = validar(inst, secuencia)
    return ok, (makespan(inst, secuencia) if ok else None), errores


def comparar_soluciones(inst, a, b):
    va, ma, _ = evaluar(inst, a)
    vb, mb, _ = evaluar(inst, b)
    if va and not vb:
        return -1
    if vb and not va:
        return 1
    if not va and not vb:
        return 0
    return (ma > mb) - (ma < mb)


def imprimir_programa(inst, secuencia):
    print("    trabajo op maquina inicio  fin")
    for (j, k, maq, ini, fin) in decodificar(inst, secuencia):
        print(f"    {j:7d} {k:2d} {maq:7d} {ini:6d} {fin:4d}")


def imprimir_resumen(nombre, valores):
    print(f"  {nombre}: mejor {min(valores)}, promedio {statistics.mean(valores):.1f}, "
          f"peor {max(valores)}")


def info(inst):
    print(f"Instancia: {inst.nombre}")
    print(f"Trabajos (n): {inst.n} | Maquinas (m): {inst.m} | Operaciones: {inst.n * inst.m}")
    print("\nRuta de cada trabajo (maquina:tiempo):")
    for j in range(inst.n):
        ops = "  ".join(f"M{inst.maquinas[j][k]}:{inst.tiempos[j][k]}" for k in range(inst.m))
        print(f"  J{j:<3} {ops}   (total {sum(inst.tiempos[j])})")

    carga = [0] * inst.m
    for j in range(inst.n):
        for k in range(inst.m):
            carga[inst.maquinas[j][k]] += inst.tiempos[j][k]
    print("\nCarga total por maquina:")
    for i, c in enumerate(carga):
        print(f"  M{i}: {c}")

    todos = [t for fila in inst.tiempos for t in fila]
    print(f"\nTiempos de operacion: min {min(todos)}, max {max(todos)}, "
          f"promedio {statistics.mean(todos):.2f}")
    print(f"Cota inferior del makespan: {inst.cota_inferior()}")
    print(f"Tamano del espacio de soluciones (n*m)!/(m!)^n: {formato_grande(tamano_espacio(inst))}")


def busqueda_exhaustiva(inst):
    n, m = inst.n, inst.m
    largo = n * m
    restantes = [m] * n
    sig_op = [0] * n
    fin_trabajo = [0] * n
    fin_maquina = [0] * m
    secuencia = []
    mejor = {"valor": None, "secuencia": None, "en": 0}
    revisadas = 0

    def dfs(cmax):
        nonlocal revisadas
        if len(secuencia) == largo:
            revisadas += 1
            if mejor["valor"] is None or cmax < mejor["valor"]:
                mejor.update(valor=cmax, secuencia=secuencia[:], en=revisadas)
            return
        for j in range(n):
            if restantes[j] == 0:
                continue
            k = sig_op[j]
            maq = inst.maquinas[j][k]
            ant_t, ant_m = fin_trabajo[j], fin_maquina[maq]
            fin = max(ant_t, ant_m) + inst.tiempos[j][k]
            fin_trabajo[j] = fin_maquina[maq] = fin
            sig_op[j] += 1
            restantes[j] -= 1
            secuencia.append(j)

            dfs(cmax if cmax > fin else fin)

            secuencia.pop()
            restantes[j] += 1
            sig_op[j] -= 1
            fin_trabajo[j], fin_maquina[maq] = ant_t, ant_m

    dfs(0)
    return mejor["secuencia"], mejor["valor"], revisadas, mejor["en"]


def puede_exhaustiva(inst):
    total = tamano_espacio(inst)
    if total > LIMITE_EXHAUSTIVA:
        print(f"La instancia tiene {formato_grande(total)} soluciones posibles; "
              f"recorrerlas todas no es factible (limite {formato_grande(LIMITE_EXHAUSTIVA)}).")
        print("Use una instancia pequena, por ejemplo instancias/00_pequena.txt")
        return False
    return True


def greedy_mwkr(inst):
    sig_op = [0] * inst.n
    pendiente = [sum(t) for t in inst.tiempos]
    secuencia = []
    for _ in range(inst.n * inst.m):
        j = max((j for j in range(inst.n) if sig_op[j] < inst.m), key=lambda j: pendiente[j])
        pendiente[j] -= inst.tiempos[j][sig_op[j]]
        sig_op[j] += 1
        secuencia.append(j)
    return secuencia


def mov_swap(s, i, j):
    t = s[:]
    t[i], t[j] = t[j], t[i]
    return t


def mov_insert(s, i, j):
    t = s[:]
    t.insert(j, t.pop(i))
    return t


def movimientos(largo, rng):
    movs = [("swap", i, j) for i in range(largo) for j in range(i + 1, largo)]
    movs += [("insert", i, j) for i in range(largo) for j in range(largo) if i != j]
    rng.shuffle(movs)
    return movs


def busqueda_local(inst, inicial, rng, max_evals=200_000):
    actual = inicial[:]
    valor = makespan(inst, actual)
    evals, mejoras = 1, 0
    while evals < max_evals:
        mejoro = False
        for tipo, i, j in movimientos(len(actual), rng):
            if tipo == "swap" and actual[i] == actual[j]:
                continue
            cand = mov_swap(actual, i, j) if tipo == "swap" else mov_insert(actual, i, j)
            v = makespan(inst, cand)
            evals += 1
            if v < valor:
                actual, valor = cand, v
                mejoras += 1
                mejoro = True
                break
            if evals >= max_evals:
                break
        if not mejoro:
            break
    optimo_local = evals < max_evals
    return actual, valor, evals, mejoras, optimo_local


def cmd_info(args):
    info(leer_instancia(args.instancia))


def cmd_verificar(args):
    inst = leer_instancia(args.instancia)
    print(inst)
    for idx, s in enumerate(leer_soluciones(args.soluciones), 1):
        ok, valor, errores = evaluar(inst, s)
        print(f"\nSolucion {idx}: {mostrar_secuencia(s)}")
        if ok:
            print(f"  VALIDA | makespan = {valor}")
            if args.detalle:
                imprimir_programa(inst, s)
        else:
            print("  INVALIDA:")
            for e in errores:
                print(f"    - {e}")


def cmd_comparar(args):
    inst = leer_instancia(args.instancia)
    sols = leer_soluciones(args.soluciones)
    if len(sols) < 2:
        raise SystemExit("El archivo debe tener al menos dos soluciones (una por linea)")
    a, b = sols[0], sols[1]
    print(inst)
    for nombre, s in (("A", a), ("B", b)):
        ok, valor, errores = evaluar(inst, s)
        estado = f"valida, makespan {valor}" if ok else "INVALIDA (" + "; ".join(errores) + ")"
        print(f"\nSolucion {nombre}: {mostrar_secuencia(s)}\n  {estado}")
    r = comparar_soluciones(inst, a, b)
    va, vb = validar(inst, a)[0], validar(inst, b)[0]
    print()
    if r == 0 and not va and not vb:
        print("Resultado: ninguna es mejor, ambas son invalidas")
    elif r == 0:
        print("Resultado: son igual de buenas (mismo makespan)")
    else:
        mejor, peor = ("A", "B") if r < 0 else ("B", "A")
        motivo = "la otra es invalida" if va != vb else "tiene menor makespan"
        print(f"Resultado: la solucion {mejor} es mejor que la {peor} ({motivo})")


def cmd_exhaustiva(args):
    inst = leer_instancia(args.instancia)
    print(inst)
    print(f"Soluciones posibles: {formato_grande(tamano_espacio(inst))}")
    if not puede_exhaustiva(inst):
        return
    t0 = time.perf_counter()
    sec, valor, revisadas, en = busqueda_exhaustiva(inst)
    dur = time.perf_counter() - t0
    print(f"\nMejor solucion: {mostrar_secuencia(sec)}")
    print(f"Makespan optimo: {valor} (cota inferior {inst.cota_inferior()})")
    print(f"Tiempo: {dur:.3f} s")
    print(f"Soluciones revisadas en total: {formato_grande(revisadas)}")
    print(f"Soluciones revisadas hasta encontrar la mejor: {formato_grande(en)}")


def cmd_iniciales(args):
    inst = leer_instancia(args.instancia)
    rng = random.Random(args.semilla)
    print(inst)
    print(f"\nSoluciones aleatorias (semilla {args.semilla}):")
    valores = []
    for i in range(1, args.cantidad + 1):
        s = secuencia_aleatoria(inst, rng)
        ok, v, _ = evaluar(inst, s)
        valores.append(v)
        print(f"  {i:2d}) makespan {v:5d} | {'valida' if ok else 'INVALIDA'} | {mostrar_secuencia(s)}")
    g = greedy_mwkr(inst)
    ok, vg, _ = evaluar(inst, g)
    print(f"\nHeuristica greedy MWKR:")
    print(f"      makespan {vg:5d} | {'valida' if ok else 'INVALIDA'} | {mostrar_secuencia(g)}")
    print("\nComparacion:")
    imprimir_resumen("aleatorias", valores)
    print(f"  greedy MWKR: {vg} | cota inferior: {inst.cota_inferior()}")


def cmd_vecino(args):
    inst = leer_instancia(args.instancia)
    rng = random.Random(args.semilla)
    print(inst)
    if args.solucion:
        s = leer_soluciones(args.solucion)[0]
        ok, _, errores = validar(inst, s)
        if not ok:
            raise SystemExit("La solucion del archivo es invalida: " + "; ".join(errores))
        origen = f"archivo {args.solucion}"
    else:
        s = secuencia_aleatoria(inst, rng)
        origen = f"aleatoria, semilla {args.semilla}"
    largo = len(s)
    v0 = makespan(inst, s)
    print(f"\nSolucion inicial ({origen}):\n  {mostrar_secuencia(s)}\n  makespan {v0}")

    while True:
        i, j = rng.randrange(largo), rng.randrange(largo)
        if s[i] != s[j]:
            break
    sw = mov_swap(s, i, j)
    i2, j2 = rng.sample(range(largo), 2)
    ins = mov_insert(s, i2, j2)
    aleatorio = vecino(s, rng)

    for titulo, t in ((f"Vecino SWAP (posiciones {i} y {j})", sw),
                      (f"Vecino INSERT (de la posicion {i2} a la {j2})", ins),
                      ("Vecino del operador del SA (swap o insert al azar)", aleatorio)):
        ok, v, _ = evaluar(inst, t)
        cambio = "mejora" if v < v0 else ("empeora" if v > v0 else "igual")
        print(f"\n{titulo}:\n  {mostrar_secuencia(t)}")
        print(f"  {'valida' if ok else 'INVALIDA'} | makespan {v} ({cambio}, delta {v - v0:+d})")


def cmd_local(args):
    inst = leer_instancia(args.instancia)
    print(inst)
    print(f"Busqueda local primera mejora (swap + insert), {args.ejecuciones} soluciones "
          f"iniciales aleatorias\n")
    valores = []
    for semilla in range(1, args.ejecuciones + 1):
        rng = random.Random(semilla)
        ini = secuencia_aleatoria(inst, rng)
        v_ini = makespan(inst, ini)
        t0 = time.perf_counter()
        s, v, evals, mejoras, opt = busqueda_local(inst, ini, rng, args.max_evals)
        dur = time.perf_counter() - t0
        valores.append(v)
        print(f"  semilla {semilla:2d}: inicial {v_ini:5d} -> final {v:5d} | {mejoras:3d} mejoras, "
              f"{evals:6d} evaluaciones, {dur:.2f} s{'' if opt else ' (presupuesto agotado)'}")
    print()
    imprimir_resumen("busqueda local", valores)
    print(f"  cota inferior: {inst.cota_inferior()}")


def cmd_sa(args):
    inst = leer_instancia(args.instancia)
    print(inst)
    t0 = time.perf_counter()
    res = simulated_annealing(inst, presupuesto=args.presupuesto, semilla=args.semilla)
    dur = time.perf_counter() - t0
    ok, v, _ = evaluar(inst, res["mejor_secuencia"])
    print(f"Semilla {args.semilla} | presupuesto {args.presupuesto} evaluaciones")
    print(f"\nMejor solucion: {mostrar_secuencia(res['mejor_secuencia'])}")
    print(f"Makespan: {v} | {'valida' if ok else 'INVALIDA'} | cota inferior {inst.cota_inferior()}")
    print(f"Tiempo: {dur:.2f} s | T0 = {res['T0']:.2f} | alpha = {res['alpha']:.5f}")


def cmd_comparar_metodos(args):
    inst = leer_instancia(args.instancia)
    print(inst)
    print(f"Cota inferior: {inst.cota_inferior()}\n")

    if tamano_espacio(inst) <= LIMITE_EXHAUSTIVA:
        t0 = time.perf_counter()
        _, v, revisadas, _ = busqueda_exhaustiva(inst)
        print(f"Busqueda exhaustiva: optimo {v} ({formato_grande(revisadas)} soluciones, "
              f"{time.perf_counter() - t0:.2f} s)")
    else:
        print("Busqueda exhaustiva: no aplicable, espacio de "
              f"{formato_grande(tamano_espacio(inst))} soluciones")

    loc, sa_v, t_loc, t_sa = [], [], 0.0, 0.0
    for semilla in range(1, args.ejecuciones + 1):
        rng = random.Random(semilla)
        t0 = time.perf_counter()
        loc.append(busqueda_local(inst, secuencia_aleatoria(inst, rng), rng, args.presupuesto)[1])
        t_loc += time.perf_counter() - t0
        t0 = time.perf_counter()
        sa_v.append(simulated_annealing(inst, presupuesto=args.presupuesto,
                                        semilla=semilla)["mejor_makespan"])
        t_sa += time.perf_counter() - t0

    print(f"\n{args.ejecuciones} ejecuciones (semillas 1 a {args.ejecuciones}), "
          f"presupuesto maximo {args.presupuesto} evaluaciones:")
    print(f"  {'metodo':<16}{'mejor':>7}{'media':>9}{'peor':>7}{'t. medio':>10}")
    for nombre, vals, t in (("busqueda local", loc, t_loc), ("SA", sa_v, t_sa)):
        print(f"  {nombre:<16}{min(vals):>7}{statistics.mean(vals):>9.1f}{max(vals):>7}"
              f"{t / args.ejecuciones:>9.2f}s")
    print(f"\n  busqueda local: {loc}")
    print(f"  SA:             {sa_v}")


def main():
    p = argparse.ArgumentParser(description="Talleres 1 a 8 - JSP",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__)
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("info", help="T1: informacion de la instancia")
    s.add_argument("instancia")
    s.set_defaults(f=cmd_info)

    s = sub.add_parser("verificar", help="T2-T3: valida soluciones y calcula el makespan")
    s.add_argument("instancia")
    s.add_argument("soluciones", help="archivo con una solucion por linea")
    s.add_argument("--detalle", action="store_true", help="muestra el programa de cada operacion")
    s.set_defaults(f=cmd_verificar)

    s = sub.add_parser("comparar", help="T3: compara las dos primeras soluciones del archivo")
    s.add_argument("instancia")
    s.add_argument("soluciones")
    s.set_defaults(f=cmd_comparar)

    s = sub.add_parser("exhaustiva", help="T4: busqueda exhaustiva")
    s.add_argument("instancia")
    s.set_defaults(f=cmd_exhaustiva)

    s = sub.add_parser("iniciales", help="T5: soluciones iniciales")
    s.add_argument("instancia")
    s.add_argument("--cantidad", type=int, default=5)
    s.add_argument("--semilla", type=int, default=1)
    s.set_defaults(f=cmd_iniciales)

    s = sub.add_parser("vecino", help="T6: genera y evalua vecinos")
    s.add_argument("instancia")
    s.add_argument("--solucion", help="archivo con la solucion de partida (si no, aleatoria)")
    s.add_argument("--semilla", type=int, default=1)
    s.set_defaults(f=cmd_vecino)

    s = sub.add_parser("local", help="T7: busqueda local primera mejora")
    s.add_argument("instancia")
    s.add_argument("--ejecuciones", type=int, default=10)
    s.add_argument("--max-evals", type=int, default=200_000)
    s.set_defaults(f=cmd_local)

    s = sub.add_parser("sa", help="T8: simulated annealing")
    s.add_argument("instancia")
    s.add_argument("--semilla", type=int, default=1)
    s.add_argument("--presupuesto", type=int, default=100_000)
    s.set_defaults(f=cmd_sa)

    s = sub.add_parser("comparar_metodos", help="T7-T8: exhaustiva vs local vs SA")
    s.add_argument("instancia")
    s.add_argument("--ejecuciones", type=int, default=10)
    s.add_argument("--presupuesto", type=int, default=100_000)
    s.set_defaults(f=cmd_comparar_metodos)

    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
