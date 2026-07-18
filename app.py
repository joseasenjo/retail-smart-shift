import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ------------------ CONFIGURACIÓN GENERAL ------------------
st.set_page_config(page_title="Smart Shift Planner | Retail Analytics", layout="wide")

st.title("Smart Shift Planner | Retail Analytics")
st.markdown("Herramienta de optimización de plantilla, asignación de zonas (Zoning) y análisis de impacto financiero para Store Managers.")

# ------------------ GUÍA DIDÁCTICA INICIAL ------------------
with st.expander("Fundamentos y guía de interpretación"):
    st.markdown("""
    ### ¿Por qué automatizar la planificación de personal?
    La asignación manual de turnos provoca desequilibrios que se traducen en **pérdida de ventas** (falta de personal en horas punta) y **costes innecesarios** (exceso en horas valle). Un modelo basado en tráfico real y tasa de servicio permite alcanzar un equilibrio rentable, maximizando la atención al cliente y controlando el gasto de personal.

    ### KPIs principales
    - **Clientes asumibles por empleado/hora:** número de clientes que un empleado puede atender eficazmente en una hora. Varía según el formato de tienda.
    - **Déficit / Exceso de personal:** diferencia entre el personal óptimo calculado a partir del tráfico y el personal realmente programado.
    - **Fuga de ventas (€):** clientes que no pueden ser atendidos por falta de personal, multiplicados por la tasa de conversión y el ticket medio.
    - **Coste de oportunidad (margen bruto):** fuga de ventas ajustada por el margen bruto, mostrando el impacto real en la cuenta de resultados.
    - **ROI de la optimización:** retorno obtenido al ajustar la plantilla exactamente a lo necesario.
    - **Punto de equilibrio de tráfico:** tráfico mínimo necesario para que un empleado sea rentable en una hora.
    """)

# ------------------ SELECCIÓN DEL MODO ------------------
modo = st.radio("Modo de análisis:", ["Diario", "Semanal"], horizontal=True)

# ------------------ CARGA DE DATOS ------------------
col_upload, col_demo = st.columns([2, 1])

with col_upload:
    if modo == "Diario":
        uploaded_file = st.file_uploader("Subir CSV diario (Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])
    else:
        uploaded_file = st.file_uploader("Subir CSV semanal (Dia, Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])

with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    demo_mode = st.checkbox("Cargar datos de demostración (Modo Demo)")

# ------------------ CARGA DE DATOS ------------------
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if modo == "Diario":
        df["Dia"] = "Hoy"
elif demo_mode:
    if modo == "Diario":
        datos = {
            "Hora": ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],
            "Trafico_Clientes": [15, 45, 95, 40, 15, 25, 80, 130, 160, 110, 50, 20],
            "Personal_Actual": [2, 2, 3, 3, 2, 2, 3, 4, 4, 4, 3, 2]
        }
        df = pd.DataFrame(datos)
        df["Dia"] = "Hoy"
    else:
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        horas_jornada = ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"]
        trafico_lab = [15,45,95,40,15,25,80,130,160,110,50,20]
        trafico_finde = [30,75,140,90,40,55,120,180,210,175,90,35]
        personal_lab = [2,2,3,3,2,2,3,4,4,4,3,2]
        personal_finde = [3,3,4,4,3,3,4,5,5,5,4,3]
        registros = []
        for dia in dias_semana:
            es_finde = dia in ["Viernes", "Sábado", "Domingo"]
            t = trafico_finde if es_finde else trafico_lab
            p = personal_finde if es_finde else personal_lab
            for i, h in enumerate(horas_jornada):
                registros.append({"Dia": dia, "Hora": h, "Trafico_Clientes": t[i], "Personal_Actual": p[i]})
        df = pd.DataFrame(registros)

# ------------------ SI HAY DATOS ------------------
if df is not None:
    # ---------- SIDEBAR: PARÁMETROS ----------
    st.sidebar.header("Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", 10, 40, 20)
    
    st.sidebar.header("Parámetros Financieros Básicos")
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (EUR)", 5.0, 500.0, 25.0, 1.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", 5, 50, 15) / 100.0
    
    with st.sidebar.expander("Configuración Financiera Avanzada"):
        coste_laboral_hora = st.number_input("Coste laboral medio por hora (EUR)", 5.0, 50.0, 12.0, 1.0,
                                             help="Incluye salario bruto y cotizaciones. Dato proporcionado por RRHH.")
        margen_bruto_pct = st.slider("Margen bruto (%)", 30, 90, 60) / 100.0
        if modo == "Diario":
            horas_presupuesto = st.number_input("Presupuesto máximo de horas/día", 0, 500, 200, 10)
        else:
            horas_presupuesto = st.number_input("Presupuesto máximo de horas/semana", 0, 3000, 1000, 10)

    # ---------- CÁLCULOS BASE ----------
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo)',
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso)', 'Óptimo'))
    df['Capacidad_Actual'] = df['Personal_Actual'] * clientes_por_empleado
    df['Clientes_Excedentes'] = np.maximum(0, df['Trafico_Clientes'] - df['Capacidad_Actual'])
    df['Fuga_Ventas_Euros'] = df['Clientes_Excedentes'] * tasa_conversion * ticket_medio
    df['Margen_Perdido'] = df['Fuga_Ventas_Euros'] * margen_bruto_pct

    def asignar_zonas(personal):
        if personal <= 0: return "Tienda Cerrada"
        if personal == 1: return "1 Multitarea (Caja y Planta)"
        if personal == 2: return "1 Caja | 1 Planta/Visual"
        if personal == 3: return "1 Caja | 1 Probadores | 1 Planta"
        return f"2 Caja | 1 Probadores | {int(personal)-3} Planta"
    df['Zoning_Recomendado'] = df['Personal_Optimo'].apply(asignar_zonas)

    # ---------- SELECCIÓN DE DÍA EN MODO SEMANAL ----------
    if modo == "Semanal":
        st.markdown("---")
        st.markdown("### Control Semanal")
        total_horas_opt = df['Personal_Optimo'].sum()
        st.info(f"El volumen de tráfico requiere un total de {int(total_horas_opt)} horas de trabajo efectivas distribuidas en la semana.")
        dia_sel = st.selectbox("Seleccionar día para auditar en detalle:", df['Dia'].unique())
        df_vista = df[df['Dia'] == dia_sel].copy()
    else:
        dia_sel = "Hoy"
        df_vista = df.copy()
        total_horas_opt = df['Personal_Optimo'].sum()

    # ---------- MÉTRICAS PRINCIPALES ----------
    fuga_total = df_vista['Fuga_Ventas_Euros'].sum()
    margen_perdido_total = df_vista['Margen_Perdido'].sum()

    st.markdown(f"### Resumen Operativo y Financiero ({dia_sel})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Horas de Riesgo", f"{len(df_vista[df_vista['Deficit_Personal'] > 0])} hrs")
    col2.metric("Horas Ineficientes", f"{len(df_vista[df_vista['Deficit_Personal'] < 0])} hrs")
    col3.metric("Fuga de Ventas Estimada", f"EUR {fuga_total:,.2f}", delta="- Pérdida", delta_color="inverse")
    col4.metric("Tráfico Total", f"{df_vista['Trafico_Clientes'].sum()} pax")

    # ---------- GRÁFICOS PRINCIPALES ----------
    colg1, colg2 = st.columns(2)
    with colg1:
        fig1 = px.bar(df_vista, x='Hora', y='Deficit_Personal', color='Nivel_Estres',
                      color_discrete_map={'Alto (Riesgo)':'#e74c3c','Óptimo':'#2ecc71','Bajo (Exceso)':'#3498db'},
                      title=f"Mapa de Estrés Operativo ({dia_sel})")
        st.plotly_chart(fig1, use_container_width=True)
    with colg2:
        fig2 = px.line(df_vista, x='Hora', y='Fuga_Ventas_Euros', markers=True,
                       title=f"Fuga de Ventas por Hora (EUR) - {dia_sel}",
                       color_discrete_sequence=['#e67e22'])
        fig2.update_traces(line_shape='spline')
        st.plotly_chart(fig2, use_container_width=True)

    # ---------- EXPANDER: COSTE DE OPORTUNIDAD, ROI, PUNTO DE EQUILIBRIO, ALERTA ----------
    with st.expander("Análisis financiero detallado"):
        st.markdown(f"**Margen bruto perdido en {dia_sel}:** EUR {margen_perdido_total:,.2f}")
        st.caption("Impacto real en el beneficio después de descontar el coste de la mercancía vendida.")

        deficit_positivo = df_vista[df_vista['Deficit_Personal'] > 0]
        if not deficit_positivo.empty:
            coste_extra = (deficit_positivo['Deficit_Personal'] * coste_laboral_hora).sum()
            ventas_recuperables = deficit_positivo['Fuga_Ventas_Euros'].sum()
            margen_recuperable = ventas_recuperables * margen_bruto_pct
            roi = (margen_recuperable - coste_extra) / coste_extra * 100 if coste_extra > 0 else 0
        else:
            coste_extra = 0
            ventas_recuperables = 0
            margen_recuperable = 0
            roi = 0

        st.markdown(f"**Coste de cubrir el déficit con personal extra:** EUR {coste_extra:,.2f}")
        st.markdown(f"**Margen bruto recuperable al eliminar la fuga:** EUR {margen_recuperable:,.2f}")
        st.markdown(f"**ROI estimado:** {roi:.1f}%")
        if roi > 0:
            st.success("Ajustar la plantilla genera un retorno positivo. Cada euro invertido en personal extra retorna margen adicional.")
        else:
            st.warning("El coste de la plantilla extra supera el margen recuperable. Revisar parámetros financieros o tasa de conversión.")

        clientes_equilibrio = coste_laboral_hora / (ticket_medio * tasa_conversion)
        st.markdown(f"**Punto de equilibrio de tráfico:** se necesitan al menos {clientes_equilibrio:.1f} clientes por hora para que un empleado sea rentable.")

        horas_reales = df_vista['Personal_Actual'].sum()
        horas_optimas = df_vista['Personal_Optimo'].sum()
        st.markdown("---")
        st.markdown(f"**Horas programadas actuales:** {horas_reales:.0f} h")
        st.markdown(f"**Horas óptimas necesarias:** {horas_optimas:.0f} h")
        st.markdown(f"**Presupuesto de horas:** {horas_presupuesto} h")
        if horas_optimas > horas_presupuesto:
            st.error("La propuesta óptima supera el presupuesto. Negociar con RRHH o ajustar la tasa de servicio.")
        else:
            st.success("La propuesta óptima se ajusta al presupuesto disponible.")

    # ---------- TABLA DE PLANIFICACIÓN ----------
    st.markdown(f"### Planificación y Zoning ({dia_sel})")
    tabla = df_vista[['Hora','Trafico_Clientes','Personal_Actual','Personal_Optimo','Zoning_Recomendado','Fuga_Ventas_Euros']].copy()
    tabla.columns = ['Hora','Tráfico Clientes','Personal Actual','Personal Óptimo','Distribución (Zoning)','Fuga de Ventas (EUR)']
    tabla['Fuga de Ventas (EUR)'] = tabla['Fuga de Ventas (EUR)'].apply(lambda x: f"EUR {x:,.2f}")
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    # ---------- BREAK PLANNER ----------
    st.markdown(f"### Optimizador de Descansos ({dia_sel})")
    valles = df_vista[df_vista['Deficit_Personal'] < 0][['Hora','Deficit_Personal','Personal_Actual']].copy()
    if not valles.empty:
        valles['Deficit_Personal'] = valles['Deficit_Personal'].abs()
        valles.columns = ['Franja Horaria','Exceso de Personal','Personal en Tienda']
        st.success("Franjas seguras para organizar descansos:")
        st.table(valles.sort_values('Exceso de Personal', ascending=False).head(3))
    else:
        st.warning("No se detectan franjas con exceso de personal. Los descansos requerirán refuerzos o cierre parcial de zonas.")

    # ---------- BENCHMARKS DE GESTIÓN DE PERSONAL ----------
    with st.expander("Benchmarks de gestión de personal"):
        st.markdown("### Indicadores de eficiencia operativa")
        st.markdown("Se comparan los valores calculados con los estándares de referencia del sector retail.")

        # Datos necesarios para los cálculos
        # Ventas estimadas reales (clientes atendidos * conversión * ticket)
        clientes_atendidos = (df_vista['Trafico_Clientes'] - df_vista['Clientes_Excedentes']).sum()
        ventas_estimadas = clientes_atendidos * tasa_conversion * ticket_medio
        horas_trabajadas = df_vista['Personal_Actual'].sum()
        coste_laboral_total = horas_trabajadas * coste_laboral_hora

        # 1. Ventas por empleado (EUR/hora)
        ventas_por_empleado = ventas_estimadas / horas_trabajadas if horas_trabajadas > 0 else 0
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ventas por empleado (EUR/h)", f"{ventas_por_empleado:,.2f}")
        with col2:
            st.caption("Referencia: moda rápida 80-150 EUR/h, deporte 100-180 EUR/h")

        # 2. Coste laboral sobre ventas (%)
        coste_laboral_pct = (coste_laboral_total / ventas_estimadas * 100) if ventas_estimadas > 0 else 0
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Coste laboral / Ventas", f"{coste_laboral_pct:.1f}%")
        with col2:
            st.caption("Ideal 12-18%, máximo recomendable 22%")
            if coste_laboral_pct > 22:
                st.error("Supera el límite recomendable. Revisar productividad o ajustar plantilla.")
            elif 12 <= coste_laboral_pct <= 22:
                st.success("Dentro del rango aceptable.")
            else:
                st.warning("Por debajo del objetivo, podría indicar falta de personal para atender la demanda.")

        # 3. Ratio de productividad (clientes atendidos/hora)
        ratio_productividad = clientes_atendidos / horas_trabajadas if horas_trabajadas > 0 else 0
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Clientes atendidos por hora", f"{ratio_productividad:.1f}")
        with col2:
            st.caption("Comparar con la media histórica de la tienda.")

        # 4. Cobertura de horas con déficit
        total_horas = len(df_vista)
        horas_riesgo = len(df_vista[df_vista['Deficit_Personal'] > 0])
        cobertura = (1 - horas_riesgo / total_horas) * 100 if total_horas > 0 else 0
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cobertura de horas sin déficit", f"{cobertura:.0f}%")
        with col2:
            st.caption("Objetivo > 95%")
            if cobertura >= 95:
                st.success("Cobertura excelente.")
            else:
                st.warning("Existen horas desatendidas. Reforzar las franjas detectadas en el mapa de estrés.")

        # Indicadores que requieren datos externos
        st.markdown("---")
        st.markdown("### Indicadores adicionales (introducir datos manualmente para comparar)")
        
        # 5. Tasa de absentismo
        absentismo = st.number_input("Tasa de absentismo del periodo (%)", 0.0, 100.0, 2.0, 0.1, key="absentismo")
        if absentismo < 3:
            st.success(f"Absentismo {absentismo}%: dentro del objetivo (<3%).")
        else:
            st.error(f"Absentismo {absentismo}%: supera el objetivo. Investigar causas y planificar cobertura.")

        # 6. Índice de rotación
        rotacion = st.number_input("Índice de rotación anual estimado (%)", 0.0, 200.0, 35.0, 1.0, key="rotacion")
        st.caption("Referencia sector retail: 30-50%. Valores superiores indican necesidad de mejorar retención.")
        if rotacion > 50:
            st.error("Rotación elevada. Impacta en costes de reclutamiento y formación.")
        
        # 7. Tiempo medio de atención por cliente (min)
        tiempo_atencion = st.number_input("Tiempo medio de atención por cliente (minutos)", 0.0, 30.0, 5.0, 0.5, key="tiempo")
        st.caption("Referencia moda: 3-7 minutos según nivel de servicio.")
        if 3 <= tiempo_atencion <= 7:
            st.success("Dentro del rango típico.")
        elif tiempo_atencion > 7:
            st.warning("Tiempo de atención elevado. Puede indicar procesos ineficientes o falta de formación.")
        
        # 8. Horas extra sobre horas planificadas
        horas_extra_pct = st.number_input("Horas extra realizadas (% sobre horas planificadas)", 0.0, 100.0, 4.0, 0.5, key="extra")
        st.caption("Ideal < 5%.")
        if horas_extra_pct <= 5:
            st.success("Horas extra controladas.")
        else:
            st.warning("Exceso de horas extra. Revisar planificación y picos de demanda.")

    # ---------- RECOMENDACIONES AUTOMÁTICAS ----------
    with st.expander("Recomendaciones automáticas para el Store Manager"):
        deficit_horas = df_vista[df_vista['Deficit_Personal'] > 0]
        if not deficit_horas.empty:
            horas_criticas = ', '.join(deficit_horas['Hora'].values)
            st.markdown(f"Horas críticas detectadas: {horas_criticas}")
            st.markdown(f"Se recomienda reforzar con {int(deficit_horas['Deficit_Personal'].max())} persona(s) extra en las franjas de mayor déficit para evitar una fuga de ventas estimada de EUR {fuga_total:,.2f}.")
        else:
            st.markdown("La plantilla está equilibrada o existe exceso de personal. Revisar si se pueden recolocar horas en otros días o reducir costes.")

    # ---------- EXPLICACIÓN VISUAL DEL CONCEPTO CLIENTES/EMPLEADO ----------
    with st.expander("Visualización: capacidad de atención (clientes por empleado/hora)"):
        ejemplo_trafico = np.arange(0, 200, 10)
        capacidad = clientes_por_empleado
        fig_conc = px.bar(x=ejemplo_trafico, y=[min(c, capacidad) for c in ejemplo_trafico],
                          labels={'x':'Clientes que entran en una hora','y':'Clientes atendidos'})
        fig_conc.add_hline(y=capacidad, line_dash="dash", line_color="red",
                           annotation_text=f"Capacidad máx. 1 empleado = {capacidad} clientes")
        fig_conc.update_layout(title="Atención al cliente vs tráfico entrante")
        st.plotly_chart(fig_conc, use_container_width=True)
        st.markdown("Cuando el tráfico supera la línea roja, los clientes adicionales no son atendidos, generando fuga de ventas.")

    # ---------- SIMULADOR DE ESCENARIOS (TODOS) ----------
    with st.expander("Simulador de escenarios (What-If)"):
        st.markdown("Seleccione un escenario y configure sus parámetros para ver el impacto en los KPIs.")

        escenario = st.selectbox("Escenario a simular:", [
            "Variación del tráfico (%)",
            "Penalización de la conversión por saturación",
            "Contratación de refuerzo externo",
            "Reducción de personal en horas valle",
            "Ajuste del estándar de servicio (clientes/empleado)",
            "Cierre temporal de probadores",
            "Apertura de segunda caja en horas pico",
            "Comparador de dos estrategias"
        ])

        df_sim = df_vista.copy()
        base_fuga = df_vista['Fuga_Ventas_Euros'].sum()
        base_costelab = df_vista['Personal_Actual'].sum() * coste_laboral_hora
        base_margen = df_vista['Margen_Perdido'].sum()

        if escenario == "Variación del tráfico (%)":
            var_trafico = st.slider("Variación del tráfico (%)", -50, 50, 20)
            df_sim['Trafico_Clientes'] = df_sim['Trafico_Clientes'] * (1 + var_trafico/100)
            df_sim['Personal_Optimo'] = np.ceil(df_sim['Trafico_Clientes'] / clientes_por_empleado)
            df_sim['Capacidad_Actual'] = df_sim['Personal_Actual'] * clientes_por_empleado
            df_sim['Clientes_Excedentes'] = np.maximum(0, df_sim['Trafico_Clientes'] - df_sim['Capacidad_Actual'])
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Penalización de la conversión por saturación":
            penalizacion = st.slider("Reducción de conversión por cada empleado faltante (%)", 0, 50, 10) / 100.0
            df_sim['Conv_Ajustada'] = tasa_conversion * (1 - penalizacion * np.maximum(0, df_sim['Deficit_Personal']))
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * df_sim['Conv_Ajustada'] * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Contratación de refuerzo externo":
            coste_refuerzo = st.number_input("Coste laboral/hora del refuerzo (EUR)", 5.0, 50.0, 15.0, 1.0)
            cubrir_deficit = st.checkbox("Cubrir completamente el déficit de personal", value=True)
            if cubrir_deficit:
                df_sim['Personal_Reforzado'] = df_sim['Personal_Actual'] + np.maximum(0, df_sim['Deficit_Personal'])
            else:
                extra = st.number_input("Empleados extra a añadir en todo el día", 0, 20, 2)
                df_sim['Personal_Reforzado'] = df_sim['Personal_Actual'] + extra/len(df_sim)
            df_sim['Capacidad_Actual'] = df_sim['Personal_Reforzado'] * clientes_por_empleado
            df_sim['Clientes_Excedentes'] = np.maximum(0, df_sim['Trafico_Clientes'] - df_sim['Capacidad_Actual'])
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            coste_total = (df_sim['Personal_Reforzado'] - df_vista['Personal_Actual']).sum() * coste_refuerzo
            beneficio_adicional = base_margen - df_sim['Margen_Perdido'].sum()
            resultado = beneficio_adicional - coste_total
            st.markdown(f"**Coste del refuerzo:** EUR {coste_total:,.2f}")
            st.markdown(f"**Margen bruto adicional recuperado:** EUR {beneficio_adicional:,.2f}")
            st.markdown(f"**Resultado neto:** EUR {resultado:,.2f}")

        elif escenario == "Reducción de personal en horas valle":
            factor_reduccion = st.slider("Porcentaje del exceso de personal a eliminar", 0, 100, 50) / 100.0
            exceso = np.maximum(0, -df_sim['Deficit_Personal'])
            df_sim['Personal_Actual'] = df_sim['Personal_Actual'] - exceso * factor_reduccion
            df_sim['Personal_Actual'] = df_sim['Personal_Actual'].clip(lower=0)
            df_sim['Capacidad_Actual'] = df_sim['Personal_Actual'] * clientes_por_empleado
            df_sim['Clientes_Excedentes'] = np.maximum(0, df_sim['Trafico_Clientes'] - df_sim['Capacidad_Actual'])
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            ahorro = (df_vista['Personal_Actual'].sum() - df_sim['Personal_Actual'].sum()) * coste_laboral_hora
            st.markdown(f"Ahorro en costes laborales: EUR {ahorro:,.2f}")
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Ajuste del estándar de servicio (clientes/empleado)":
            nuevo_ratio = st.slider("Nuevo ratio de clientes por empleado/hora", 10, 40, clientes_por_empleado)
            df_sim['Personal_Optimo'] = np.ceil(df_sim['Trafico_Clientes'] / nuevo_ratio)
            df_sim['Deficit_Personal'] = df_sim['Personal_Optimo'] - df_sim['Personal_Actual']
            df_sim['Capacidad_Actual'] = df_sim['Personal_Actual'] * nuevo_ratio
            df_sim['Clientes_Excedentes'] = np.maximum(0, df_sim['Trafico_Clientes'] - df_sim['Capacidad_Actual'])
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Cierre temporal de probadores":
            impacto_conv = st.slider("Reducción de la tasa de conversión por cierre (%)", 0, 50, 15) / 100.0
            horas_aplicar = st.multiselect("Horas en las que se cierran probadores", df_sim['Hora'].unique(), default=df_sim['Hora'].unique())
            mask = df_sim['Hora'].isin(horas_aplicar)
            df_sim['Tasa_Conv'] = tasa_conversion
            df_sim.loc[mask, 'Tasa_Conv'] = tasa_conversion * (1 - impacto_conv)
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * df_sim['Tasa_Conv'] * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Apertura de segunda caja en horas pico":
            incremento_capacidad = st.slider("Incremento de clientes asumibles por empleado (%)", 0, 50, 20) / 100.0
            horas_caja = st.multiselect("Horas con segunda caja operativa", df_sim['Hora'].unique())
            capacidad_mejorada = clientes_por_empleado * (1 + incremento_capacidad)
            mask = df_sim['Hora'].isin(horas_caja)
            df_sim['Capacidad_Actual'] = df_sim['Personal_Actual'] * clientes_por_empleado
            df_sim.loc[mask, 'Capacidad_Actual'] = df_sim.loc[mask, 'Personal_Actual'] * capacidad_mejorada
            df_sim['Clientes_Excedentes'] = np.maximum(0, df_sim['Trafico_Clientes'] - df_sim['Capacidad_Actual'])
            df_sim['Fuga_Ventas_Euros'] = df_sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
            df_sim['Margen_Perdido'] = df_sim['Fuga_Ventas_Euros'] * margen_bruto_pct
            st.metric("Nueva fuga de ventas", f"EUR {df_sim['Fuga_Ventas_Euros'].sum():,.2f}")

        elif escenario == "Comparador de dos estrategias":
            st.markdown("Configure dos escenarios y compare sus resultados frente a la situación actual.")
            colA, colB = st.columns(2)
            with colA:
                st.subheader("Estrategia A")
                var_trafico_a = st.slider("Var. tráfico A (%)", -50, 50, 0, key="ta")
                ratio_a = st.slider("Clientes/empleado A", 10, 40, clientes_por_empleado, key="ra")
                refuerzo_a = st.checkbox("Cubrir déficit con refuerzo", key="refa")
                coste_ref_a = st.number_input("Coste refuerzo/h A", 5.0, 50.0, 15.0, 1.0, key="costa") if refuerzo_a else 0
            with colB:
                st.subheader("Estrategia B")
                var_trafico_b = st.slider("Var. tráfico B (%)", -50, 50, 0, key="tb")
                ratio_b = st.slider("Clientes/empleado B", 10, 40, clientes_por_empleado, key="rb")
                refuerzo_b = st.checkbox("Cubrir déficit con refuerzo", key="refb")
                coste_ref_b = st.number_input("Coste refuerzo/h B", 5.0, 50.0, 15.0, 1.0, key="costb") if refuerzo_b else 0

            def simular_estrategia(var_traf, ratio, refuerzo, coste_ref):
                sim = df_vista.copy()
                sim['Trafico_Clientes'] *= (1 + var_traf/100)
                sim['Personal_Optimo'] = np.ceil(sim['Trafico_Clientes'] / ratio)
                if refuerzo:
                    deficit = np.maximum(0, sim['Personal_Optimo'] - sim['Personal_Actual'])
                    sim['Personal_Actual'] += deficit
                sim['Capacidad_Actual'] = sim['Personal_Actual'] * ratio
                sim['Clientes_Excedentes'] = np.maximum(0, sim['Trafico_Clientes'] - sim['Capacidad_Actual'])
                sim['Fuga_Ventas_Euros'] = sim['Clientes_Excedentes'] * tasa_conversion * ticket_medio
                sim['Margen_Perdido'] = sim['Fuga_Ventas_Euros'] * margen_bruto_pct
                fuga = sim['Fuga_Ventas_Euros'].sum()
                coste_lab = sim['Personal_Actual'].sum() * (coste_ref if refuerzo else coste_laboral_hora)
                return fuga, coste_lab

            fugaA, costeA = simular_estrategia(var_trafico_a, ratio_a, refuerzo_a, coste_ref_a)
            fugaB, costeB = simular_estrategia(var_trafico_b, ratio_b, refuerzo_b, coste_ref_b)

            st.markdown("### Comparación de resultados")
            comp_df = pd.DataFrame({
                'Indicador': ['Fuga ventas (EUR)', 'Coste laboral total (EUR)'],
                'Situación actual': [base_fuga, base_costelab],
                'Estrategia A': [fugaA, costeA],
                'Estrategia B': [fugaB, costeB]
            })
            st.table(comp_df)

    # ---------- GRÁFICO SEMANAL EN MODO SEMANAL ----------
    if modo == "Semanal":
        st.markdown("### Tendencia Comparativa del Tráfico Semanal")
        fig_sem = px.bar(df, x="Hora", y="Trafico_Clientes", color="Dia", barmode="group",
                         title="Patrones horarios - 7 días")
        st.plotly_chart(fig_sem, use_container_width=True)

    # ---------- CONCEPTOS TEÓRICOS ADICIONALES ----------
    with st.expander("Conceptos teóricos y metodología"):
        st.markdown("""
        **La importancia de la planificación basada en datos**  
        La gestión tradicional de turnos suele apoyarse en intuiciones o plantillas fijas. El uso de datos de tráfico permite una asignación dinámica que maximiza la atención al cliente y minimiza los costes innecesarios.

        **Cálculo de la capacidad de atención**  
        La capacidad se define como el número de clientes que un empleado puede atender eficazmente por hora. Este parámetro depende del formato comercial, los procesos operativos y el nivel de servicio deseado.

        **Interpretación del déficit y exceso de personal**  
        - Déficit: riesgo de pérdida de ventas por falta de atención.  
        - Exceso: coste laboral improductivo que lastra la rentabilidad de la tienda.

        **Efecto de la saturación en la conversión**  
        Cuando el personal está sobrecargado, la calidad del servicio disminuye y la tasa de conversión puede caer, amplificando la fuga de ventas.

        **El coste de oportunidad en retail**  
        Cada cliente que abandona sin comprar representa una venta perdida, pero también un margen bruto que deja de ingresarse. La herramienta traduce este concepto en cifras concretas para facilitar la toma de decisiones.

        **Metodología Lean y Six Sigma aplicada a la gestión de turnos**  
        El Smart Shift Planner se inspira en la eliminación de desperdicios (horas sobrantes) y la maximización del valor (atención en horas clave). La medición continua y la simulación permiten ciclos de mejora PDCA (Plan-Do-Check-Act).
        """)

else:
    st.info("Suba un archivo CSV o active el Modo Demo para comenzar.")
    if modo == "Diario":
        st.markdown("Estructura esperada del CSV diario: `Hora, Trafico_Clientes, Personal_Actual`")
    else:
        st.markdown("Estructura esperada del CSV semanal: `Dia, Hora, Trafico_Clientes, Personal_Actual`")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555; padding: 20px;'>
        <p style='font-size: 16px; margin-bottom: 8px;'>Desarrollado por <b>Jose Luis Asenjo</b></p>
        <p style='font-size: 14px;'>
            <a href='https://www.linkedin.com/in/joseluisasenjo' target='_blank' style='text-decoration: none; color: #0077b5; font-weight: bold;'>LinkedIn</a> |
            <a href='https://joseasenjo.github.io/portfolio/' target='_blank' style='text-decoration: none; color: #0077b5; font-weight: bold;'>Portfolio</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
