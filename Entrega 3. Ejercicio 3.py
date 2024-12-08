import pandas as pd
import pulp as lp

costes = pd.read_excel("241204_costes.xlsx", index_col=0)

coste_medio = costes.mean()
print("\nCostes de cada operación")
print(coste_medio)

programacion = pd.read_excel("241204_datos_operaciones_programadas.xlsx", index_col=0)

quirofanos = []
for i, j in costes.iterrows():
    quirofanos.append(i)

programacion_ordenada = programacion.sort_values(by=["Hora inicio", "Hora fin"], ascending=[True, True])

operaciones = []
for i, j in programacion_ordenada.iterrows():
    operaciones.append(i)

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

planificaciones = [tuple(p) for p in planificaciones]
planificaciones = set(planificaciones)
planificaciones = [list(p) for p in planificaciones]

K = {}
for i in range(0, len(planificaciones)):
    K[i] = planificaciones[i]
print(f"\nEl número de operaciones factibles a barajar es {len(K)}")
print("\nEstas planificaciones son:")
for i, j in K.items():
    print(f"- Planificación {i+1}: {j}")

def modelo_maestro(K):
    #Conjuntos
    I = operaciones
        
    #Inicializar modelo
    modelo_3 = lp.LpProblem("Entrega_3_Ejercicio_3", lp.LpMinimize)
    
    #Variables
    y = lp.LpVariable.dicts("Uso_quirófano", [k for k in K], lowBound=0, cat=lp.LpBinary)
    
    #Función objetivo
    modelo_3 += lp.lpSum(y[k] for k in K)
    
    #Restricciones
    for i in I:
        modelo_3 += lp.lpSum(y[k] for k in K if i in planificaciones[k]) >= 1

    #Resolver modelo
    modelo_3.solve()
    
    return modelo_3, y

#Generar nuevas variables para el modelo maestro
def generar_columnas(maestro, operaciones, planificaciones, programacion_ordenada):
    duales = {}
    for i in maestro.constraints.values():
        if hasattr(i, "pi"):
            duales[i.name] = i.pi
    nuevas_planificaciones = []
    for i in range(len(operaciones)):
        for j in range(i + 1, len(operaciones)):
            planificacion_candidata = [operaciones[i], operaciones[j]]
            compatible = True
            for m in range(len(planificacion_candidata)):
                for n in range(m + 1, len(planificacion_candidata)):
                    op1_inicio = programacion_ordenada.loc[planificacion_candidata[m], "Hora inicio"]
                    op1_fin = programacion_ordenada.loc[planificacion_candidata[m], "Hora fin"]
                    op2_inicio = programacion_ordenada.loc[planificacion_candidata[n], "Hora inicio"]
                    op2_fin = programacion_ordenada.loc[planificacion_candidata[n], "Hora fin"]
                    if (op1_inicio >= op2_inicio and op1_inicio < op2_fin) or (op1_fin > op2_inicio and op1_fin <= op2_fin) or (op1_inicio <= op2_inicio and op1_fin >= op2_fin):
                        compatible = False
                        break
                if not compatible:
                    break
            if compatible:
                coste_reducido = 1 - sum(duales.get(op, 0) for op in planificacion_candidata)
                if coste_reducido < 0:
                    nuevas_planificaciones.append(planificacion_candidata)
    return nuevas_planificaciones

#Inicializar modelo maestro
maestro, y = modelo_maestro(K)

#Generación inicial de columnas
nuevas_planificaciones = generar_columnas(maestro, operaciones, planificaciones, programacion_ordenada)
for planificacion_nueva in nuevas_planificaciones:
    nuevo_id = len(K)
    K[nuevo_id] = planificacion_nueva

#Iteración de columnas hasta resolver modelo
while nuevas_planificaciones:
    maestro, y = modelo_maestro(K)
    nuevas_planificaciones = generar_columnas(maestro, operaciones, planificaciones, programacion_ordenada)

#Imprimir función objetivo, variables y estado del problema
asignaciones_quirofanos = {}
contador = 1
for i,j in y.items():
    if j.varValue == 1:
        operaciones_asignadas = K[i]
        asignaciones_quirofanos[contador] = operaciones_asignadas
        contador = contador + 1

print(f"\nEn total se requerirán {round(lp.value(maestro.objective),0)} quirófanos")

print(f"\nEl estado del problema es: {lp.LpStatus[maestro.status]}")

print("\nLa asignación de operaciones a cada quirófano es:")
for i,j in asignaciones_quirofanos.items():
    print(f"Quirófano {i}: {j}")