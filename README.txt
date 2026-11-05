Tarea 2 Investigacion de Operaciones - Job Shop Problem con Simulated Annealing

Integrantes:
Joaquin Muñoz 21.494.986-5
Benjamin Pizarro 21.630.813-1
Ignacio Reyes 21.415.646-6


------------------------------------------------------------------------------
1. Descripcion
------------------------------------------------------------------------------

El programa resuelve el Job Shop Problem (JSP): hay n trabajos y m maquinas,
cada trabajo tiene que pasar por todas las maquinas en un orden fijo y cada
operacion tiene una duracion. Una maquina no puede hacer dos operaciones al
mismo tiempo y un trabajo no puede estar en dos maquinas a la vez. El objetivo
es minimizar el makespan, o sea el tiempo en que termina el ultimo trabajo.

Para resolverlo implementamos Simulated Annealing.


------------------------------------------------------------------------------
2. Requisitos
------------------------------------------------------------------------------

- Python 3.10 o mas nuevo
- matplotlib (solo para los graficos). Se instala con:
  pip install matplotlib

No se usan otras librerias externas.


------------------------------------------------------------------------------
3. Estructura de la carpeta
------------------------------------------------------------------------------

tarea2_jsp/
  main.py           corre el SA en una instancia
  experimentos.py   hace las 10 ejecuciones por instancia y genera los graficos
  sa.py             implementacion del simulated annealing
  evaluador.py      calcula el makespan y revisa las restricciones
  instancia.py      lee los archivos de las instancias
  graficos.py       gantt, boxplots y convergencia
  instancias/
    01_facil.txt    6 trabajos x 6 maquinas (es la instancia ft06)
    02_medio.txt    15 trabajos x 10 maquinas
    03_dificil.txt  50 trabajos x 10 maquinas
  resultados/       se crea sola al ejecutar, aca quedan los graficos y el csv

La carpeta instancias tiene que ir en minuscula y al lado de los .py.


------------------------------------------------------------------------------
4. Como ejecutar
------------------------------------------------------------------------------

Hay que abrir la terminal dentro de la carpeta tarea2_jsp.

4.1 Una ejecucion (main.py)

  python main.py instancias/01_facil.txt

Opciones (todas son opcionales):
  --semilla N        semilla aleatoria (por defecto 1)
  --presupuesto N    cantidad maxima de evaluaciones de la funcion objetivo
                     (por defecto 100000)
  --gantt            guarda el diagrama de gantt en resultados/

Ejemplo:
  python main.py instancias/02_medio.txt --semilla 3 --presupuesto 20000 --gantt

Lo que imprime:
  - nombre y tamaño de la instancia, y su cota inferior
  - mejor makespan encontrado
  - si la solucion es factible (se revisa aparte, al final)
  - evaluaciones usadas y tiempo de ejecucion
  - T0 y alpha que uso el SA
  - la secuencia de la mejor solucion

4.2 Experimentos del informe (experimentos.py)

  python experimentos.py --presupuesto 20000


Opciones:
  --presupuesto N    evaluaciones por ejecucion (por defecto 100000)
  --ejecuciones N    cuantas ejecuciones por instancia (por defecto 10)
  --salida CARPETA   donde se guardan los archivos (por defecto resultados)

Por ejemplo, para probar con otro presupuesto sin borrar los resultados
anteriores:
  python experimentos.py --presupuesto 5000 --salida resultados_5000

Muestra en la terminal la tabla con el makespan de cada ejecucion, el mejor,
la media y la desviacion estandar. Ademas deja en la carpeta de salida:
  resultados.csv              instancia, semilla, makespan y tiempo de cada ejecucion
  boxplots.png                grafico de cajas de las 3 instancias
  convergencia_<inst>.png     como baja el mejor makespan segun las evaluaciones
  gantt_<inst>.png            diagrama de gantt de la mejor solucion de cada instancia

4.3 Prueba del evaluador

  python evaluador.py

Lee las 3 instancias, evalua 1000 soluciones aleatorias en cada una, revisa que
sean factibles y muestra cuanto se demora una evaluacion. Sirve para comprobar
que la lectura y la funcion objetivo funcionan bien.


------------------------------------------------------------------------------
5. Formato de las instancias
------------------------------------------------------------------------------

Primera linea: cantidad de trabajos y cantidad de maquinas.
Despues una fila por trabajo con m pares (maquina, tiempo), en el orden en que
se hacen las operaciones. Las maquinas parten desde 0.

Ejemplo, primera fila de 01_facil.txt:
  2 1 0 3 1 6 3 7 5 3 4 6
El trabajo 0 va primero a la maquina 2 por 1 unidad de tiempo, despues a la
maquina 0 por 3, despues a la maquina 1 por 6, etc.

Nota: el documento del curso dice que los pares son (tiempo, maquina), pero en
los archivos vienen como (maquina, tiempo). Lo comprobamos porque si se leen al
reves aparecen maquinas que no existen. Al leer, el programa revisa que cada
trabajo pase una vez por cada maquina y si no avisa con un error.


------------------------------------------------------------------------------
6. Como funciona
------------------------------------------------------------------------------

6.1 Representacion de la solucion

Una solucion es una lista de largo n*m donde cada trabajo aparece m veces
(permutacion con repeticion). La k-esima vez que aparece el trabajo j
corresponde a su operacion k. Ejemplo con 3 trabajos y 2 maquinas:
  [1, 0, 1, 2, 0, 2]

La lista indica el orden en que se programan las operaciones; la maquina de
cada operacion ya viene dada por la instancia.

Cualquier lista de este tipo es factible, porque cada aparicion toma la
siguiente operacion pendiente del trabajo y asi siempre se respeta su orden.
Por eso no hace falta penalizar ni reparar soluciones.

6.2 Evaluacion (funcion objetivo)

Se recorre la lista y cada operacion empieza cuando estan libres su trabajo y
su maquina. Termina en inicio + duracion. El
makespan es el mayor tiempo de termino.

Ejemplo con 2 trabajos y 2 maquinas:
  trabajo 0: maquina 0 por 3, luego maquina 1 por 2
  trabajo 1: maquina 1 por 4, luego maquina 0 por 1
Solucion [0, 1, 1, 0]:
  J0 op0 en M0: empieza max(0,0)=0, termina 3
  J1 op0 en M1: empieza max(0,0)=0, termina 4
  J1 op1 en M0: empieza max(4,3)=4, termina 5
  J0 op1 en M1: empieza max(3,4)=4, termina 6
  makespan = 6

6.3 Cota inferior

Se calcula como el maximo entre la carga total de la maquina mas ocupada y la
duracion total del trabajo mas largo. Ninguna solucion puede tener un makespan
menor. Si el SA llega a la cota, esa solucion es optima.

6.4 Simulated Annealing

1. Se parte de una solucion aleatoria.
2. Se calcula la temperatura inicial T0 con 100 vecinos de esa solucion:
   T0 = -(empeoramiento promedio) / ln(0.8)
   Asi al principio se acepta mas o menos el 80% de los vecinos peores. Se
   calcula de esta forma porque las instancias tienen escalas distintas.
3. Se calcula alpha para que la temperatura llegue a T0*0.001 justo cuando se
   acaba el presupuesto.
4. Mientras queden evaluaciones:
   - se genera un vecino con swap o insert (50% cada uno)
       swap: intercambia dos posiciones con trabajos distintos
       insert: saca un elemento y lo pone en otra posicion
   - si el vecino es mejor o igual se acepta
   - si es peor se acepta con probabilidad exp(-delta/T)
   - se guarda la mejor solucion vista
   - cada L iteraciones la temperatura baja: T = alpha*T
5. Se devuelve la mejor solucion encontrada.

Al principio, con T alta, se aceptan bastantes soluciones peores y el algoritmo
explora. Al final T es casi 0 y solo acepta mejoras.

6.5 Parametros

  presupuesto            100000 evaluaciones por defecto (se cambia con --presupuesto)
  T0                     automatica, 80% de aceptacion inicial
  T final                T0 * 0.001
  L                      n*m iteraciones por temperatura
  probabilidad de swap   0.5 (el resto es insert)
  semillas               1 a 10 en los experimentos

Las 100 evaluaciones que se usan para calcular T0 tambien cuentan dentro del
presupuesto.
