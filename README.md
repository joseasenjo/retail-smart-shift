# Smart Shift Planner | Retail Analytics 
Analisis Eficiencia en Recursos Humanos
Optimación y eficiencia. 


Herramienta avanzada de optimización de personal para Store Managers del sector retail.
Permite analizar el tráfico de clientes, calcular la plantilla óptima, asignar zonas de trabajo (zoning), cuantificar el impacto financiero de los desajustes y simular escenarios "what-if".
Integra benchmarks de gestión de personal y proporciona recomendaciones automáticas basadas en datos.

Desarrollado en Python con Streamlit, Pandas, Plotly y NumPy.

Características principales
Dos modos de análisis: diario (un día) o semanal (vista de 7 días con selector de jornada).
Cálculo dinámico de personal óptimo por hora a partir del tráfico y la capacidad de atención.
Mapa de estrés operativo (déficit/exceso de personal) y fuga de ventas (€) por hora.
Parámetros financieros completos: ticket medio, tasa de conversión, coste laboral, margen bruto, presupuesto de horas.
Análisis financiero detallado: coste de oportunidad (margen perdido), ROI de la optimización, punto de equilibrio de tráfico, alerta presupuestaria.
Zoning inteligente: distribución recomendada del personal entre caja, probadores y planta según la plantilla óptima.
Optimizador de descansos: detección de franjas con exceso de personal para organizar pausas.
Benchmarks de gestión de personal: indicadores automáticos (ventas por empleado/hora, coste laboral sobre ventas, productividad, cobertura) y campos para datos externos (absentismo, rotación, tiempo de atención, horas extra).
Simulador de 8 escenarios "What-If":
Variación del tráfico (%)
Penalización de la conversión por saturación
Contratación de refuerzo externo
Reducción de personal en horas valle
Ajuste del estándar de servicio (clientes/empleado)
Cierre temporal de probadores
Apertura de segunda caja en horas pico
Comparador de dos estrategias
Recomendaciones automáticas narrativas basadas en los resultados.
Expanders educativos con teoría, metodología y visualización de conceptos clave.
Modo demo con datos sintéticos para exploración inmediata.
Carga de archivos CSV personalizados.
Instalación y ejecución
Requisitos
Python 3.8 o superior
pip
Dependencias
Las librerías necesarias se listan en requirements.txt:

streamlit
pandas
plotly
numpy
Instalar con:

bash
pip install -r requirements.txt
Ejecutar la aplicación
bash
streamlit run app.py
La aplicación se abrirá en el navegador por defecto en http://localhost:8501.



Al respecto de cuestiones teóricas y de desarrollo, diremos:

Modos de análisis
Diario: analiza un único día. El CSV debe contener las columnas Hora, Trafico_Clientes, Personal_Actual.

Semanal: analiza una semana completa (7 días). El CSV debe incluir la columna adicional Dia (valores esperados: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo).

Se puede alternar entre modos mediante un radio button al inicio de la aplicación.

Carga de datos
Archivo CSV: se puede subir el archivo con la estructura correspondiente.

Modo Demo: genera automáticamente datos sintéticos realistas (patrones de tráfico diferenciados para laborables y fines de semana).

Configuración de parámetros
Todos los parámetros se ajustan en la barra lateral.

Parámetros operativos
Clientes asumibles por empleado/hora (10–40): define la capacidad de atención estándar.

Parámetros financieros básicos
Ticket medio estimado (€): gasto medio por cliente que compra.

Tasa de conversión esperada (%): porcentaje de clientes que realizan una compra.

Configuración financiera avanzada (expander)
Coste laboral medio por hora (€): incluye salario bruto y cotizaciones.

Margen bruto (%): margen comercial sobre ventas.

Presupuesto máximo de horas: límite de horas diario o semanal.

Métricas y KPIs
Cálculos base
Para cada franja horaria:

Personal Óptimo
Personal_Optimo = ceil(Trafico_Clientes / Clientes_por_empleado)

Déficit/Exceso de Personal
Deficit_Personal = Personal_Optimo - Personal_Actual

Nivel de estrés operativo

Deficit > 0 → Alto (Riesgo)

Deficit < 0 → Bajo (Exceso)

Deficit == 0 → Óptimo

Capacidad de atención actual
Capacidad_Actual = Personal_Actual * Clientes_por_empleado

Clientes excedentes (no atendidos)
Clientes_Excedentes = max(0, Trafico_Clientes - Capacidad_Actual)

Fuga de ventas (€)
Fuga_Ventas_Euros = Clientes_Excedentes * Tasa_Conversion * Ticket_Medio

Margen bruto perdido
Margen_Perdido = Fuga_Ventas_Euros * Margen_Bruto

Métricas agregadas
Horas de riesgo: número de franjas con déficit de personal.

Horas ineficientes: número de franjas con exceso de personal.

Fuga de ventas total: suma de las fugas horarias.

Tráfico total: suma de clientes en el periodo.

Análisis financiero detallado
Dentro del expander correspondiente se muestran:

Margen bruto perdido (impacto en la cuenta de resultados).

ROI de la optimización:
ROI = (Margen_Recuperable - Coste_Extra) / Coste_Extra * 100
donde Coste_Extra es el coste de cubrir el déficit con personal adicional.

Punto de equilibrio de tráfico: clientes necesarios para que un empleado sea rentable.
Clientes_Equilibrio = Coste_Laboral_Hora / (Ticket_Medio * Tasa_Conversion)

Alerta presupuestaria: compara las horas óptimas con el presupuesto máximo.

Benchmarks de gestión de personal
Se comparan los valores calculados con referencias del sector retail. La sección se divide en dos partes:

Indicadores automáticos
Indicador	Fórmula	Referencia
Ventas por empleado (€/h)	Ventas_Estimadas / Horas_Trabajadas	Moda rápida: 80-150 €/h; Deporte: 100-180 €/h
Coste laboral / Ventas (%)	(Coste_Laboral_Total / Ventas_Estimadas) * 100	Ideal 12-18%, máx. 22%
Clientes atendidos por hora	Clientes_Atendidos / Horas_Trabajadas	Comparar con media histórica de la tienda
Cobertura de horas sin déficit (%)	(1 - Horas_Riesgo / Total_Horas) * 100	Objetivo > 95%
Indicadores manuales
Campos para introducir datos externos y comparar con estándares:

Tasa de absentismo (%) – objetivo < 3%

Índice de rotación anual (%) – referencia 30-50%, valores superiores indican problemas de retención

Tiempo medio de atención por cliente (min) – moda: 3-7 min

Horas extra sobre planificadas (%) – ideal < 5%

Cada indicador muestra un semáforo (verde, amarillo, rojo) según su posición frente al objetivo.

Simulador de escenarios "What-If"
El expander permite seleccionar uno de los siguientes escenarios y modificar los parámetros relevantes para ver el impacto inmediato en la fuga de ventas y otros indicadores.

1. Variación del tráfico (%)
Modifica el tráfico de todas las horas en un porcentaje (de -50% a +50%). Recalcula personal óptimo, clientes excedentes y fuga de ventas.

2. Penalización de la conversión por saturación
Aplica una reducción de la tasa de conversión por cada empleado faltante (slider de 0% a 50%). Modela el deterioro del servicio cuando el personal está sobrecargado.
Conv_Ajustada = Tasa_Conversion * (1 - Penalizacion * max(0, Deficit_Personal))

3. Contratación de refuerzo externo
Permite simular la incorporación de personal extra (con un coste laboral propio) para cubrir total o parcialmente el déficit. Calcula el coste adicional, el margen recuperado y el resultado neto.

4. Reducción de personal en horas valle
Elimina un porcentaje del exceso de personal en las horas donde sobra plantilla. Muestra el ahorro en costes laborales y el posible incremento de clientes excedentes.

5. Ajuste del estándar de servicio (clientes/empleado)
Cambia el ratio de clientes que puede atender un empleado por hora. Permite probar políticas de más calidad (ratio menor) o mayor productividad (ratio mayor).

6. Cierre temporal de probadores
Selecciona horas en las que los probadores permanecen cerrados y aplica una reducción adicional de la tasa de conversión en esas franjas.

7. Apertura de segunda caja en horas pico
Incrementa la capacidad de atención (clientes/empleado) en las horas seleccionadas, simulando la apertura de una caja adicional.

8. Comparador de dos estrategias
Permite configurar dos conjuntos de parámetros (variación de tráfico, ratio clientes/empleado, refuerzo) y compara sus resultados (fuga de ventas y coste laboral) con la situación actual.

Planificación de descansos (Break Planner)
Detecta franjas horarias con exceso de personal (Deficit_Personal < 0) y las ordena por mayor excedente. Recomienda las tres mejores franjas para organizar los descansos del equipo, asegurando que no se descuide la atención al cliente.

Zoning inteligente
La función asignar_zonas(personal) distribuye automáticamente la plantilla óptima entre las áreas clave:

0 empleados: Tienda Cerrada

1: Multitarea (Caja y Planta)

2: 1 Caja, 1 Planta/Visual

3: 1 Caja, 1 Probadores, 1 Planta

4+: 2 Caja, 1 Probadores, resto en Planta

Esta lógica es fácilmente personalizable según las necesidades de cada tienda.

Visualizaciones
Gráfico de barras con el déficit/exceso de personal coloreado según nivel de estrés (rojo, verde, azul).

Gráfico de líneas con la fuga de ventas por hora (spline suavizado).

Gráfico de barras agrupadas (modo semanal) mostrando el tráfico por hora y día.

Gráfico de saturación (expander educativo) que ilustra la capacidad de atención vs. tráfico entrante.

Recomendaciones automáticas
En el expander correspondiente, se genera un texto narrativo que identifica las horas críticas y sugiere el número de personas extra necesarias para eliminar la fuga de ventas. Si no hay déficit, se informa que la plantilla está equilibrada y se puede evaluar la reducción de costes.

Conceptos teóricos (expander educativo)
La herramienta incluye un expander con explicaciones sobre:

Planificación basada en datos frente a intuición.

Cálculo de capacidad de atención.

Interpretación del déficit/exceso de personal.

Efecto de la saturación en la conversión.

Coste de oportunidad y margen bruto.

Metodología Lean y PDCA aplicada a la gestión de turnos.

Estructura del código
El script principal (app.py) sigue una estructura secuencial y modular:

Configuración de página (st.set_page_config).

Carga de datos: archivo o generación demo.

Cálculos base: creación de columnas calculadas en el DataFrame.

Sidebar: parámetros operativos y financieros.

Visualización principal: métricas, gráficos, tablas.

Secciones en expanders: análisis financiero, benchmarks, escenarios, teoría, etc.

Lógica de simulación: para cada escenario se aplican transformaciones al DataFrame.

Footer: enlaces a LinkedIn y Portfolio.

El uso de st.expander permite ocultar secciones complejas sin sobrecargar la interfaz.

Personalización
Datos demo: se pueden modificar los arrays trafico_lab, trafico_finde, etc., para adaptar los patrones sintéticos a otro formato de tienda.

Zoning: modificar la función asignar_zonas().

Estilos: los colores y textos son fácilmente ajustables.

Benchmarks: las referencias numéricas están en el código y pueden actualizarse según el sector.
