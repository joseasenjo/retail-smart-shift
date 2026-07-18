import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ------------------ CONFIGURACIÓN GENERAL ------------------
st.set_page_config(page_title="Smart Shift Planner | Retail Analytics", layout="wide")

st.title("📊 Optimizador de Cuadrantes (Smart Shift Planner)")
st.markdown("Herramienta avanzada para Store Managers: Optimización de plantilla, asignación de zonas (Zoning) y cálculo de impacto financiero.")

# ------------------ GUÍA DIDÁCTICA INICIAL ------------------
with st.expander("📘 Guía didáctica: cómo interpretar esta herramienta"):
    st.markdown("""
    ### 🎯 ¿Por qué automatizar la planificación de personal?
    La asignación manual de turnos genera desequilibrios que se traducen en:
    - **Pérdida de ventas** cuando falta personal en horas punta (clientes no atendidos).
    - **Costes innecesarios** cuando sobra personal en horas valle.
    
    Un modelo basado en tráfico real y tasa de servicio permite alcanzar un **equilibrio rentable**, maximizando la atención al cliente y controlando el gasto de personal.
    
    ### 📊 KPIs clave que vas a manejar
    - **Clientes asumibles por empleado/hora**: cuántos clientes puede atender eficazmente un empleado en una hora. Este dato varía según el formato de tienda.
    - **Déficit / Exceso de personal**: diferencia entre el personal óptimo (calculado a partir del tráfico) y el personal realmente programado.
    - **Fuga de ventas (€)**: clientes que no pueden ser atendidos por falta de personal × tasa de conversión × ticket medio.
    - **Coste de oportunidad (margen bruto)**: fuga de ventas multiplicada por el % de margen bruto. Muestra el impacto real en la cuenta de resultados.
    - **ROI de la optimización**: retorno que se obtendría al ajustar la plantilla exactamente a lo necesario.
    - **Punto de equilibrio de tráfico**: cuántos clientes deben entrar en una hora para que un empleado sea rentable.
    
    ### 🏬 Zoning inteligente
    La herramienta sugiere automáticamente cómo distribuir al personal entre caja, probadores y planta en función del número óptimo de empleados, aplicando criterios de eficiencia operativa.
    """)

# ------------------ SELECCIÓN DEL MODO ------------------
modo = st.radio("🔍 Selecciona el modo de análisis:", ["📅 Diario", "🗓️ Semanal"], horizontal=True)

# ------------------ CARGA DE DATOS ------------------
col_upload, col_demo = st.columns([2, 1])

with col_upload:
    if modo == "📅 Diario":
        uploaded_file = st.file_uploader("Sube el CSV diario (Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])
    else:
        uploaded_file = st.file_uploader("Sube el CSV semanal (Dia, Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])

with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    demo_mode = st.checkbox("🚀 Modo Demo")

# ------------------ CARGA DE DATOS ------------------
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if modo == "📅 Diario":
        df["Dia"] = "Hoy"
elif demo_mode:
    if modo == "📅 Diario":
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
    st.sidebar.header("⚙️ Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", 10, 40, 20)
    
    st.sidebar.header("💰 Parámetros Financieros Básicos")
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (€)", 5.0, 500.0, 25.0, 1.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", 5, 50, 15) / 100.0
    
    # --- Parámetros financieros avanzados ---
    with st.sidebar.expander("💰 Configuración Financiera Avanzada"):
        coste_laboral_hora = st.number_input("Coste laboral medio por hora (€)", 5.0, 50.0, 12.0, 1.0,
                                             help="Incluye salario bruto + cotizaciones. Dato de RRHH.")
        margen_bruto_pct = st.slider("Margen bruto (%)", 30, 90, 60) / 100.0
        if modo == "📅 Diario":
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

    # Zoning
    def asignar_zonas(personal):
        if personal <= 0: return "Tienda Cerrada"
        if personal == 1: return "1 Multitarea (Caja y Planta)"
        if personal == 2: return "1 Caja | 1 Planta/Visual"
        if personal == 3: return "1 Caja | 1 Probadores | 1 Planta"
        return f"2 Caja | 1 Probadores | {int(personal)-3} Planta"
    df['Zoning_Recomendado'] = df['Personal_Optimo'].apply(asignar_zonas)

    # ---------- FUNCIÓN PARA FILTRAR DÍA EN MODO SEMANAL ----------
    if modo == "🗓️ Semanal":
        st.markdown("---")
        st.markdown("### 🗓️ Control Semanal")
        total_horas_opt = df['Personal_Optimo'].sum()
        st.info(f"📋 **Análisis de Capacidad:** El volumen de tráfico requiere un total de **{int(total_horas_opt)} horas de trabajo efectivas** en la semana.")
        dia_sel = st.selectbox("Selecciona un día para auditar:", df['Dia'].unique())
        df_vista = df[df['Dia'] == dia_sel].copy()
    else:
        dia_sel = "Hoy"
        df_vista = df.copy()
        total_horas_opt = df['Personal_Optimo'].sum()

    # ---------- MÉTRICAS PRINCIPALES ----------
    fuga_total = df_vista['Fuga_Ventas_Euros'].sum()
    margen_perdido_total = df_vista['Margen_Perdido'].sum()

    st.markdown(f"### 🎯 Resumen Operativo y Financiero ({dia_sel})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Horas de Riesgo", f"{len(df_vista[df_vista['Deficit_Personal'] > 0])} hrs")
    col2.metric("Horas Ineficientes", f"{len(df_vista[df_vista['Deficit_Personal'] < 0])} hrs")
    col3.metric("Fuga de Ventas Estimada", f"€ {fuga_total:,.2f}", delta="− Pérdida", delta_color="inverse")
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
                       title=f"Fuga de Ventas por Hora (€) – {dia_sel}",
                       color_discrete_sequence=['#e67e22'])
        fig2.update_traces(line_shape='spline')
        st.plotly_chart(fig2, use_container_width=True)

    # ---------- EXPANDER: COSTE DE OPORTUNIDAD, ROI, PUNTO DE EQUILIBRIO, ALERTA ----------
    with st.expander("🧮 Coste de Oportunidad (Margen Bruto)"):
        st.markdown(f"**Margen bruto perdido en {dia_sel}:** € {margen_perdido_total:,.2f}")
        st.markdown(f"*Este es el impacto real en el beneficio después de descontar el coste de la mercancía vendida (margen del {margen_bruto_pct*100:.0f}%).*")

    # ROI de la optimización (solo horas con déficit positivo)
    deficit_positivo = df_vista[df_vista['Deficit_Personal'] > 0]
    if not deficit_positivo.empty:
        coste_extra = (deficit_positivo['Deficit_Personal'] * coste_laboral_hora).sum()
        ventas_recuperables = deficit_positivo['Fuga_Ventas_Euros'].sum()  # ya es ventas perdidas por falta de personal
        margen_recuperable = ventas_recuperables * margen_bruto_pct
        roi = (margen_recuperable - coste_extra) / coste_extra * 100 if coste_extra > 0 else 0
    else:
        coste_extra = 0
        ventas_recuperables = 0
        margen_recuperable = 0
        roi = 0

    with st.expander("📈 ROI de la Optimización"):
        st.markdown(f"**Coste de cubrir el déficit con personal extra:** € {coste_extra:,.2f}")
        st.markdown(f"**Margen bruto recuperable al eliminar la fuga:** € {margen_recuperable:,.2f}")
        st.markdown(f"**ROI estimado:** {roi:.1f}%")
        if roi > 0:
            st.success("✅ Ajustar la plantilla genera un retorno positivo. Cada euro invertido en personal extra retorna margen adicional.")
        else:
            st.warning("⚠️ El coste de la plantilla extra supera el margen recuperable. Revisa los parámetros financieros o la tasa de conversión.")

    # Punto de equilibrio de tráfico por empleado/hora
    clientes_equilibrio = coste_laboral_hora / (ticket_medio * tasa_conversion)
    with st.expander("📊 Punto de Equilibrio de Tráfico"):
        st.markdown(f"Para que un empleado sea rentable en una hora, se necesitan al menos **{clientes_equilibrio:.1f} clientes** que compren.")
        st.markdown(f"*(Cálculo: coste laboral {coste_laboral_hora:.2f}€ / (ticket medio {ticket_medio:.2f}€ × conversión {tasa_conversion:.0%}))*")

    # Alerta presupuestaria
    horas_reales = df_vista['Personal_Actual'].sum()
    horas_optimas = df_vista['Personal_Optimo'].sum()
    with st.expander("⚠️ Alerta Presupuestaria"):
        if modo == "📅 Diario":
            texto_presup = f"Presupuesto diario: {horas_presupuesto} h"
        else:
            texto_presup = f"Presupuesto semanal: {horas_presupuesto} h"
        st.markdown(f"**Horas programadas actuales:** {horas_reales:.0f} h")
        st.markdown(f"**Horas óptimas necesarias:** {horas_optimas:.0f} h")
        st.markdown(f"**{texto_presup}**")
        if horas_optimas > horas_presupuesto:
            st.error("🚨 La propuesta óptima supera el presupuesto. Negocia con RRHH o ajusta la tasa de servicio.")
        elif horas_optimas <= horas_presupuesto:
            st.success("✅ La propuesta óptima se ajusta al presupuesto disponible.")

    # ---------- TABLA DE PLANIFICACIÓN ----------
    st.markdown(f"### 📋 Planificación y Zoning ({dia_sel})")
    tabla = df_vista[['Hora','Trafico_Clientes','Personal_Actual','Personal_Optimo','Zoning_Recomendado','Fuga_Ventas_Euros']].copy()
    tabla.columns = ['Hora','Tráfico Clientes','Personal Actual','Personal Óptimo','Distribución (Zoning)','Fuga de Ventas (€)']
    tabla['Fuga de Ventas (€)'] = tabla['Fuga de Ventas (€)'].apply(lambda x: f"€ {x:,.2f}")
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    # ---------- BREAK PLANNER ----------
    st.markdown(f"### ☕ Optimizador de Descansos ({dia_sel})")
    valles = df_vista[df_vista['Deficit_Personal'] < 0][['Hora','Deficit_Personal','Personal_Actual']].copy()
    if not valles.empty:
        valles['Deficit_Personal'] = valles['Deficit_Personal'].abs()
        valles.columns = ['Franja Horaria','Exceso de Personal','Personal en Tienda']
        st.success("✅ Franjas seguras para descansos:")
        st.table(valles.sort_values('Exceso de Personal', ascending=False).head(3))
    else:
        st.warning("⚠️ Sin franjas con exceso. Los descansos requerirán refuerzos o cierre parcial de zonas.")

    # ---------- RECOMENDACIONES AUTOMÁTICAS ----------
    with st.expander("📝 Recomendaciones Automáticas para el Store Manager"):
        deficit_horas = df_vista[df_vista['Deficit_Personal'] > 0]
        if not deficit_horas.empty:
            horas_criticas = ', '.join(deficit_horas['Hora'].values)
            st.markdown(f"🔴 **Horas críticas detectadas:** {horas_criticas}")
            st.markdown(f"Se recomienda **reforzar con {int(deficit_horas['Deficit_Personal'].max())} persona(s) extra** en las franjas de mayor déficit para evitar la fuga de ventas estimada de **€ {fuga_total:,.2f}**.")
        else:
            st.markdown("🟢 La plantilla está equilibrada o hay exceso de personal. Revisa si puedes recolocar horas en otros días o reducir costes.")

    # ---------- SIMULADOR WHAT-IF ----------
    with st.expander("🔮 Simulador de escenarios 'What-If'"):
        st.markdown("Modifica los valores para ver cómo cambiarían las pérdidas:")
        sim_conversion = st.slider("Tasa de conversión simulada (%)", 5, 50, int(tasa_conversion*100)) / 100.0
        sim_ticket = st.number_input("Ticket medio simulado (€)", 5.0, 500.0, ticket_medio, 1.0)
        df_sim = df_vista.copy()
        df_sim['Fuga_Ventas_Sim'] = df_sim['Clientes_Excedentes'] * sim_conversion * sim_ticket
        fuga_sim = df_sim['Fuga_Ventas_Sim'].sum()
        delta = fuga_sim - fuga_total
        st.metric("Fuga de ventas simulada", f"€ {fuga_sim:,.2f}",
                  delta=f"{'↑' if delta>0 else '↓'} € {abs(delta):,.2f} vs actual")

    # ---------- EXPLICACIÓN VISUAL CLIENTES/EMPLEADO (DENTRO DE UN EXPANDER) ----------
    with st.expander("👥 Visualización del concepto 'Clientes por empleado/hora'"):
        ejemplo_trafico = np.arange(0, 200, 10)
        capacidad = clientes_por_empleado
        fig_conc = px.bar(x=ejemplo_trafico, y=[min(c, capacidad) for c in ejemplo_trafico],
                          labels={'x':'Clientes que entran en una hora','y':'Clientes atendidos'})
        fig_conc.add_hline(y=capacidad, line_dash="dash", line_color="red",
                           annotation_text=f"Capacidad máx. 1 empleado = {capacidad} clientes")
        fig_conc.update_layout(title="Atención al cliente vs tráfico entrante")
        st.plotly_chart(fig_conc, use_container_width=True)
        st.markdown("Cuando el tráfico supera la línea roja, los clientes adicionales no son atendidos → se genera fuga de ventas.")

    # ---------- GRÁFICO SEMANAL SOLO EN MODO SEMANAL ----------
    if modo == "🗓️ Semanal":
        st.markdown("### 📈 Tendencia Comparativa del Tráfico Semanal")
        fig_sem = px.bar(df, x="Hora", y="Trafico_Clientes", color="Dia", barmode="group",
                         title="Patrones horarios – 7 días")
        st.plotly_chart(fig_sem, use_container_width=True)

else:
    st.info("👈 Sube un archivo CSV o activa el **Modo Demo** para comenzar.")
    if modo == "📅 Diario":
        st.markdown("**Estructura esperada del CSV diario:** `Hora, Trafico_Clientes, Personal_Actual`")
    else:
        st.markdown("**Estructura esperada del CSV semanal:** `Dia, Hora, Trafico_Clientes, Personal_Actual`")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555; padding: 20px;'>
        <p style='font-size: 16px;'>Desarrollado por <b>Jose Luis Asenjo</b></p>
        <a href='https://www.linkedin.com/in/joseluisasenjo' target='_blank' style='text-decoration: none; color: #0077b5; font-weight: bold;'>
            🔗 Conecta conmigo en LinkedIn
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
