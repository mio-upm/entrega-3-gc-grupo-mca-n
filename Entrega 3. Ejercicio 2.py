import pandas as pd
import pulp as lp

costes = pd.read_excel("241204_costes.xlsx", index_col=0)

coste_medio = costes.mean()
print("\nCostes de cada operación")
print(coste_medio)

especialidades = ["Cardiología Pediátrica", "Cirugía Cardíaca Pediátrica","Cirugía Cardiovascular", "Cirugía General y del Aparato Digestivo"]
programacion = pd.read_excel("241204_datos_operaciones_programadas.xlsx", index_col=0)
programacion_filtrada = programacion[
    (programacion["Especialidad quirúrgica"] == "Cardiología Pediátrica") |
    (programacion["Especialidad quirúrgica"] == "Cirugía Cardíaca Pediátrica") |
    (programacion["Especialidad quirúrgica"] == "Cirugía Cardiovascular") |
    (programacion["Especialidad quirúrgica"] ==
     "Cirugía General y del Aparato Digestivo")
]

quirofanos = []
for i, j in costes.iterrows():
    quirofanos.append(i)

programacion_ordenada = programacion_filtrada.sort_values(by=["Hora inicio", "Hora fin"], ascending=[True, True])

print("\nDetalles de la programación quirúrgica:")
print(programacion_ordenada)

operaciones = []
for i, j in programacion_ordenada.iterrows():
    operaciones.append(i)

#Creación de planificaciones factibles
planificaciones = []
for i in operaciones:
    operaciones_pendientes = operaciones[operaciones.index(i):] + operaciones[:operaciones.index(i)].copy()
    while operaciones_pendientes:
        planificacion = []
        operacion_actual = operaciones_pendientes[0]
        planificacion.append(operacion_actual)
        operaciones_pendientes.remove(operacion_actual)
        orden = 0
        while orden < len(operaciones_pendientes):
            operacion_siguiente = operaciones_pendientes[orden]
            compatibilidad = True
            I_op_s = pd.to_datetime(programacion_ordenada.loc[operacion_siguiente, "Hora inicio"])
            F_op_s = pd.to_datetime(programacion_ordenada.loc[operacion_siguiente, "Hora fin"])
            for j in planificacion:
                I_j = pd.to_datetime(programacion_ordenada.loc[j, "Hora inicio"])
                F_j = pd.to_datetime(programacion_ordenada.loc[j, "Hora fin"])
                if (I_op_s >= I_j and I_op_s < F_j) or (F_op_s > I_j and F_op_s <= F_j) or (I_op_s <= I_j and F_op_s >= F_j):
                    compatibilidad = False
                    break
            if compatibilidad == True:
                planificacion.append(operacion_siguiente)
                operaciones_pendientes.remove(operacion_siguiente)
            else:
                orden = orden + 1
        planificaciones.append(planificacion)

K = {}
for i in range(0, len(planificaciones)):
    K[i] = planificaciones[i]
print(f"\nEl número de operaciones factibles a barajar es {len(K)}")
print("\nEstas planificaciones son:")
for i, j in K.items():
    print(f"- Planificación {i+1}: {j}")

#Conjuntos
I = operaciones

J = quirofanos

#Parámetros
coste_planificacion = {}
for k in K:
    lista_costes = []
    op_planificacion = K[k]
    for i in op_planificacion:
        coste_i = coste_medio.loc[i]
        lista_costes.append(coste_i)
    coste_planificacion[k] = sum(lista_costes)

#Inicializar modelo
modelo_2 = lp.LpProblem("Entrega_3_Ejercicio_2", lp.LpMinimize)

#Variables
b = lp.LpVariable.dicts("Operación_en_planificación", [(i, k) for i in I for k in K], lowBound=0, cat=lp.LpBinary)
y = lp.LpVariable.dicts("Uso_quirófano", [k for k in K], lowBound=0, cat=lp.LpBinary)

#Función objetivo
modelo_2 += lp.lpSum(coste_planificacion[k] * y[k] for k in K)

#Restricciones
for i in I:
    modelo_2 += lp.lpSum(y[k] for k in K if i in planificaciones[k]) >= 1

#Resolver modelo
modelo_2.solve()

#Imprimir función objetivo, variables y estado del problema
print(f"\nEl valor de la función objetivo (coste total) es de: {round(lp.value(modelo_2.objective),2)} €")

print(f"\nEl estado del problema es: {lp.LpStatus[modelo_2.status]}")

contador=0
lista_planificaciones_sol = []
for k in K:
    if y[k].varValue == 1:
        lista_planificaciones_sol.append(planificaciones[k])
        contador = contador + 1
print(f"\nEn total se requerirán {contador} quirófanos")

print("\nLa asignación de operaciones a cada quirófano es:")
for i in range(0,contador):
    print(f"- Quirófano {i+1}: {lista_planificaciones_sol[i]}")