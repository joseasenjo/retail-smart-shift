import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Smart Shift Planner | Weekly Edition", layout="wide")

st.title("📊 Smart Shift Planner: Vista Semanal")
st.markdown("Gestión operativa integral: Optimización de turnos, Zoning y control de horas semanales.")

# --- CARGA DE DATOS ---
col_upload, col_demo = st.columns([2, 1])
with col_upload:
    uploaded_file = st.file_uploader("Sube tu CSV semanal (Columnas: Dia, Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])
with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    demo_mode = st.checkbox("🚀 Cargar Semana de Demostración")

df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif demo_mode:
    # Generar datos para 7 días
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas = [f"{h}:00" for h in range(10, 22)]
    data = []
    for dia in dias:
        for hora in horas:
            # Patrón: fin de semana más tráfico
            trafico = np.random.randint(20, 80) if dia in ["Lunes", "Martes"] else np.random.randint(60, 150)
            data.append([dia, hora, trafico, 3])
    df = pd.DataFrame(data, columns=["Dia", "Hora", "Trafico_Clientes", "Personal_Actual"])

if df is not None:
    # Sidebar
    st.sidebar.header("⚙️ Configuración")
    clientes_por_empleado = st.sidebar.slider("Clientes/Empleado hora", 10, 50, 25)
    
    # Cálculos
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    
    # --- FILTRO POR DÍA ---
    dia_seleccionado = st.selectbox("Selecciona el día para gestionar:", df['Dia'].unique())
    df_dia = df[df['Dia'] == dia_seleccionado].copy()

    # Métricas Semanales Totales
    st.markdown("### 🗓️ Resumen Semanal de Necesidades")
    total_horas_optimas = df['Personal_Optimo'].sum()
    st.info(f"Total de horas de trabajo necesarias esta semana: **{int(total_horas_optimas)} horas hombre**")

    # Mostrar día seleccionado
    st.markdown(f"### 📋 Operativa para: {dia_seleccionado}")
    
    # Zoning
    def asignar_zonas(p):
        return "1 Caja | 1 Probador | Resto Planta" if p > 2 else "1 Caja | 1 Planta"
    df_dia['Zoning'] = df_dia['Personal_Optimo'].apply(asignar_zonas)
    
    st.table(df_dia[['Hora', 'Trafico_Clientes', 'Personal_Optimo', 'Zoning']])

    # Gráfico Semanal
    st.markdown("### 📈 Tendencia de Tráfico Semanal")
    fig = px.bar(df, x="Hora", y="Trafico_Clientes", color="Dia", barmode="group", title="Comparativa de tráfico por franjas horarias")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Sube un CSV con las columnas: Dia, Hora, Trafico_Clientes, Personal_Actual")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center;'>Desarrollado por <b>Jose Luis Asenjo</b> | <a href='https://www.linkedin.com/in/joseluisasenjo'>LinkedIn</a></div>", unsafe_allow_html=True)
