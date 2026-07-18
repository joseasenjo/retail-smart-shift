import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ------------------ CONFIGURACIÓN GENERAL ------------------
st.set_page_config(page_title="Smart Shift Planner | Retail Analytics", layout="wide")

st.title("📊 Optimizador de Cuadrantes (Smart Shift Planner)")
st.markdown("Herramienta avanzada para Store Managers: Optimización de plantilla, asignación de zonas (Zoning) y cálculo de impacto financiero.")

# ------------------ SELECCIÓN DEL MODO DE ANÁLISIS ------------------
modo = st.radio("🔍 Selecciona el modo de análisis:", ["📅 Diario", "🗓️ Semanal"], horizontal=True)

# ------------------ CARGA DE DATOS ------------------
col_upload, col_demo = st.columns([2, 1])

with col_upload:
    if modo == "📅 Diario":
        uploaded_file = st.file_uploader(
            "Sube el archivo CSV diario (Columnas: Hora, Trafico_Clientes, Personal_Actual)", 
            type=["csv"]
        )
    else:
        uploaded_file = st.file_uploader(
            "Sube el archivo CSV semanal (Columnas: Dia, Hora, Trafico_Clientes, Personal_Actual)", 
            type=["csv"]
        )

with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    demo_mode = st.checkbox("🚀 Modo Demo")

# ------------------ CARGA DE DATOS (ARCHIVO O DEMO) ------------------
df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if modo == "📅 Diario":
        df["Dia"] = "Hoy"   # columna unificada para facilitar el tratamiento
elif demo_mode:
    if modo == "📅 Diario":
        # Datos demo diario (12 horas)
        datos = {
            "Hora": ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],
            "Trafico_Clientes": [15, 45, 95, 40, 15, 25, 80, 130, 160, 110, 50, 20],
            "Personal_Actual": [2, 2, 3, 3, 2, 2, 3, 4, 4, 4, 3, 2]
        }
        df = pd.DataFrame(datos)
        df["Dia"] = "Hoy"
    else:
        # Datos demo semanal
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

# ------------------ SI HAY DATOS -> MOSTRAR HERRAMIENTA ------------------
if df is not None:
    # ---------- SIDEBAR: PARÁMETROS ----------
    st.sidebar.header("⚙️ Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", 10, 40, 20)
    st.sidebar.header("💰 Parámetros Financieros")
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (€)", 5.0, 500.0, 25.0, 1.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", 5, 50, 15) / 100.0

    # ---------- CÁLCULOS UNIVERSALES ----------
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo)', 
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso)', 'Óptimo'))
    df['Capacidad_Actual'] = df['Personal_Actual'] * clientes_por_empleado
    df['Clientes_Excedentes'] = np.maximum(0, df['Trafico_Clientes'] - df['Capacidad_Actual'])
    df['Fuga_Ventas_Euros'] = df['Clientes_Excedentes'] * tasa_conversion * ticket_medio

    def asignar_zonas(personal):
        if personal <= 0: return "Tienda Cerrada"
        if personal == 1: return "1 Multitarea (Caja y Planta)"
        if personal == 2: return "1 Caja | 1 Planta/Visual"
        if personal == 3: return "1 Caja | 1 Probadores | 1 Planta"
        return f"2 Caja | 1 Probadores | {int(personal)-3} Planta"

    df['Zoning_Recomendado'] = df['Personal_Optimo'].apply(asignar_zonas)

    # ---------- INTERFAZ SEGÚN MODO ----------
    if modo == "📅 Diario":
        # Métricas globales del día
        fuga_total = df['Fuga_Ventas_Euros'].sum()
        st.markdown("---")
        st.markdown("### 🎯 Resumen Operativo y Financiero")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Horas de Riesgo", f"{len(df[df['Deficit_Personal'] > 0])} hrs")
        c2.metric("Horas Ineficientes", f"{len(df[df['Deficit_Personal'] < 0])} hrs")
        c3.metric("Fuga de Ventas Estimada", f"€ {fuga_total:,.2f}", delta="− Pérdida", delta_color="inverse")
        c4.metric("Tráfico Total", f"{df['Trafico_Clientes'].sum()} pax")

        # Gráficos
        colg1, colg2 = st.columns(2)
        with colg1:
            fig1 = px.bar(df, x='Hora', y='Deficit_Personal', color='Nivel_Estres',
                          color_discrete_map={'Alto (Riesgo)':'#e74c3c','Óptimo':'#2ecc71','Bajo (Exceso)':'#3498db'},
                          title="Mapa de Estrés Operativo")
            st.plotly_chart(fig1, use_container_width=True)
        with colg2:
            fig2 = px.line(df, x='Hora', y='Fuga_Ventas_Euros', markers=True,
                           title="Fuga de Ventas por Hora (€)", color_discrete_sequence=['#e67e22'])
            fig2.update_traces(line_shape='spline')
            st.plotly_chart(fig2, use_container_width=True)

        # Tabla
        st.markdown("### 📋 Planificación Recomendada y Zoning")
        tabla = df[['Hora','Trafico_Clientes','Personal_Actual','Personal_Optimo','Zoning_Recomendado','Fuga_Ventas_Euros']].copy()
        tabla.columns = ['Hora','Tráfico Clientes','Personal Actual','Personal Óptimo','Distribución (Zoning)','Fuga de Ventas (€)']
        tabla['Fuga de Ventas (€)'] = tabla['Fuga de Ventas (€)'].apply(lambda x: f"€ {x:,.2f}")
        st.dataframe(tabla, use_container_width=True, hide_index=True)

        # Break Planner
        st.markdown("### ☕ Optimizador de Descansos")
        valles = df[df['Deficit_Personal'] < 0][['Hora','Deficit_Personal','Personal_Actual']].copy()
        if not valles.empty:
            valles['Deficit_Personal'] = valles['Deficit_Personal'].abs()
            valles.columns = ['Franja Horaria','Exceso de Personal','Personal en Tienda']
            st.success("✅ Franjas seguras detectadas para organizar descansos:")
            st.table(valles.sort_values('Exceso de Personal', ascending=False).head(3))
        else:
            st.warning("⚠️ No se detectan franjas con exceso de personal.")

    else:  # Modo Semanal
        st.markdown("---")
        st.markdown("### 🗓️ Control Semanal")
        total_horas_opt = df['Personal_Optimo'].sum()
        st.info(f"📋 **Análisis de Capacidad:** El volumen de tráfico requiere un total de **{int(total_horas_opt)} horas de trabajo efectivas** distribuidas en la semana.")

        dia_sel = st.selectbox("Selecciona un día para auditar en detalle:", df['Dia'].unique())
        df_dia = df[df['Dia'] == dia_sel].copy()

        # KPIs del día
        fuga_dia = df_dia['Fuga_Ventas_Euros'].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Horas de Riesgo", f"{len(df_dia[df_dia['Deficit_Personal'] > 0])} hrs")
        c2.metric("Horas Ineficientes", f"{len(df_dia[df_dia['Deficit_Personal'] < 0])} hrs")
        c3.metric("Fuga de Ventas Estimada", f"€ {fuga_dia:,.2f}", delta="− Pérdida", delta_color="inverse")
        c4.metric("Tráfico del Día", f"{df_dia['Trafico_Clientes'].sum()} pax")

        colg1, colg2 = st.columns(2)
        with colg1:
            fig1 = px.bar(df_dia, x='Hora', y='Deficit_Personal', color='Nivel_Estres',
                          color_discrete_map={'Alto (Riesgo)':'#e74c3c','Óptimo':'#2ecc71','Bajo (Exceso)':'#3498db'},
                          title=f"Mapa de Estrés ({dia_sel})")
            st.plotly_chart(fig1, use_container_width=True)
        with colg2:
            fig2 = px.line(df_dia, x='Hora', y='Fuga_Ventas_Euros', markers=True,
                           title=f"Fuga de Ventas ({dia_sel})", color_discrete_sequence=['#e67e22'])
            fig2.update_traces(line_shape='spline')
            st.plotly_chart(fig2, use_container_width=True)

        # Tendencia semanal
        st.markdown("### 📈 Tendencia Comparativa del Tráfico Semanal")
        fig_sem = px.bar(df, x="Hora", y="Trafico_Clientes", color="Dia", barmode="group",
                         title="Patrones de tráfico horario – 7 días")
        st.plotly_chart(fig_sem, use_container_width=True)

        # Tabla del día
        st.markdown(f"### 📋 Planificación y Zoning ({dia_sel})")
        tabla = df_dia[['Hora','Trafico_Clientes','Personal_Actual','Personal_Optimo','Zoning_Recomendado','Fuga_Ventas_Euros']].copy()
        tabla.columns = ['Hora','Tráfico Clientes','Personal Actual','Personal Óptimo','Distribución (Zoning)','Fuga de Ventas (€)']
        tabla['Fuga de Ventas (€)'] = tabla['Fuga de Ventas (€)'].apply(lambda x: f"€ {x:,.2f}")
        st.dataframe(tabla, use_container_width=True, hide_index=True)

        # Break Planner del día
        st.markdown(f"### ☕ Optimizador de Descansos ({dia_sel})")
        valles = df_dia[df_dia['Deficit_Personal'] < 0][['Hora','Deficit_Personal','Personal_Actual']].copy()
        if not valles.empty:
            valles['Deficit_Personal'] = valles['Deficit_Personal'].abs()
            valles.columns = ['Franja Horaria','Exceso de Personal','Personal en Tienda']
            st.success("✅ Franjas seguras para organizar descansos:")
            st.table(valles.sort_values('Exceso de Personal', ascending=False).head(3))
        else:
            st.warning("⚠️ No se detectan franjas con exceso de personal en este día.")

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
