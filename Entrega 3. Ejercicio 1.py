import pandas as pd
import pulp as lp

costes = pd.read_excel("241204_costes.xlsx", index_col=0)

programacion = pd.read_excel("241204_datos_operaciones_programadas.xlsx", index_col=0)
programacion = programacion[programacion["Especialidad quirúrgica"] == "Cardiología Pediátrica"]

quirofanos = []
for i,j in costes.iterrows():
    quirofanos.append(i)
operaciones = []
for i,j in programacion.iterrows():
    operaciones.append(i)

op_incompatibles = {}
for i in operaciones:
    I_i = pd.to_datetime(programacion.loc[i,"Hora inicio"])
    F_i = pd.to_datetime(programacion.loc[i,"Hora fin"])
    L = []
    for j in operaciones:
        if i==j:
            continue
        else:
            I_j = pd.to_datetime(programacion.loc[j, "Hora inicio"])
            F_j = pd.to_datetime(programacion.loc[j, "Hora fin"])
            if (I_i >= I_j and I_i < F_j) or (F_i > I_j and F_i <= F_j) or (I_i <= I_j and F_i >= F_j):
                L.append(j)
    op_incompatibles[i] = L

#Conjuntos
I = operaciones

J = quirofanos

L = op_incompatibles

#Parámetros
C = costes

#Inicializar modelo
modelo_1 = lp.LpProblem("Entrega_3_Ejercicio_1", lp.LpMinimize)

#Variables
x = lp.LpVariable.dicts("x", [(i,j) for i in I for j in J], lowBound=0, cat=lp.LpBinary)

#Función objetivo
modelo_1 += lp.lpSum([x[(i,j)] * C.loc[j,i] for i in I for j in J])

#Definir restricciones
for i in I:
    modelo_1 += lp.lpSum([x[(i,j)] for j in J]) >= 1

for i in I:
    for j in J:
        modelo_1 += lp.lpSum([x[(h,j)] for h in L[i]]) + x[(i,j)] <= 1

#Resolver modelo
modelo_1.solve()

#Imprimir función objetivo, variables y estado del problema
print("\nEl valor de la función objetivo (coste total) es de: ", lp.value(modelo_1.objective) ,"€")

print("\nEl estado del problema es: ", lp.LpStatus[modelo_1.status])

print("\nAsignación operaciones - quirófanos:")
for i in I:
    for j in J:
        if x[(i,j)].varValue == 1:
            print(f"- La operación {i} ({programacion.loc[i,"Equipo de Cirugía"]}) se asigna al {j}")

print("\nNúmero de operaciones por quirófano:")
for j in J:
    n = 0
    for i in I:
        if x[(i,j)].varValue == 1:
            n = n+1
    if n == 0:
        pass
    elif n == 1:
        print(f"- El {j} ubicará {n} operación")
    else:
        print(f"- El {j} ubicará un total de {n} operaciones")