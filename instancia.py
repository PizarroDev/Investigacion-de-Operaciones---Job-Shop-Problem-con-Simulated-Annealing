import os
import sys
sys.dont_write_bytecode = True


class Instancia:

    def __init__(self, nombre, n, m, maquinas, tiempos):
        self.nombre = nombre
        self.n = n
        self.m = m
        self.maquinas = maquinas
        self.tiempos = tiempos

    def cota_inferior(self):
        carga = [0] * self.m
        for j in range(self.n):
            for k in range(self.m):
                carga[self.maquinas[j][k]] += self.tiempos[j][k]
        largo_trabajo = max(sum(t) for t in self.tiempos)
        return max(max(carga), largo_trabajo)

    def __str__(self):
        return f"{self.nombre}: {self.n} trabajos x {self.m} maquinas"


def leer_instancia(ruta):
    with open(ruta, "r") as f:
        numeros = [int(x) for x in f.read().split()]

    n, m = numeros[0], numeros[1]
    datos = numeros[2:]
    if len(datos) != n * m * 2:
        raise ValueError(f"Se esperaban {n * m * 2} numeros y hay {len(datos)}")

    maquinas, tiempos = [], []
    for j in range(n):
        fila = datos[j * 2 * m:(j + 1) * 2 * m]
        maq_j = fila[0::2]
        tie_j = fila[1::2]
        if sorted(maq_j) != list(range(m)):
            raise ValueError(f"Trabajo {j}: maquinas invalidas {maq_j}")
        maquinas.append(maq_j)
        tiempos.append(tie_j)

    return Instancia(os.path.basename(ruta), n, m, maquinas, tiempos)