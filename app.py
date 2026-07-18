import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Smart Shift Planner | Retail Analytics", layout="wide")

st.title("📊 Optimizador de Cuadrantes (Smart Shift Planner)")
st.markdown("Herramienta de apoyo para Store Managers. Optimiza la cobertura de la tienda basándose en el tráfico de clientes y minimiza el estrés operativo del equipo.")

# Subida de archivo (Procesamiento directo en RAM, Zero-Disk Storage)
uploaded_file = st.file_uploader("Sube el archivo CSV de tráfico y horarios (Tráfico, Ventas, Personal_Actual)", type=["csv"])

if uploaded_file is not None:
    # Leer datos en memoria
    df = pd.read_csv(uploaded_file)
    
    # Parámetro ajustable por el Store Manager
    st.sidebar.header("Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", min_value=10, max_value=40, value=20)
    
    # Cálculos operativos
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo de pérdida de ventas)', 
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso de personal)', 'Óptimo'))

    # Métricas principales
    st.markdown("### 🎯 Resumen Operativo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Horas de Riesgo (Falta Personal)", f"{len(df[df['Deficit_Personal'] > 0])} hrs")
    col2.metric("Horas Ineficientes (Exceso Personal)", f"{len(df[df['Deficit_Personal'] < 0])} hrs")
    col3.metric("Tráfico Total Analizado", f"{df['Trafico_Clientes'].sum()} clientes")

    # Gráfico 1: Tráfico vs Personal
    st.markdown("### 📈 Curva de Tráfico y Cobertura Óptima")
    fig_trafico = px.line(df, x='Hora', y=['Trafico_Clientes'], markers=True, title="Tráfico de Clientes a lo largo del día")
    st.plotly_chart(fig_trafico, use_container_width=True)

    # Gráfico 2: Mapa de Calor del Estrés Operativo
    st.markdown("### ⚠️ Mapa de Estrés Operativo del Equipo")
    fig_estres = px.bar(df, x='Hora', y='Deficit_Personal', 
                        color='Nivel_Estres',
                        color_discrete_map={'Alto (Riesgo de pérdida de ventas)': '#e74c3c', 
                                            'Óptimo': '#2ecc71', 
                                            'Bajo (Exceso de personal)': '#3498db'},
                        title="Déficit o Exceso de Personal por Franja Horaria")
    st.plotly_chart(fig_estres, use_container_width=True)

    st.markdown("### 📋 Tabla de Planificación Recomendada")
    st.dataframe(df[['Hora', 'Trafico_Clientes', 'Personal_Actual', 'Personal_Optimo', 'Nivel_Estres']], use_container_width=True)

else:
    st.info("Por favor, sube un archivo CSV para generar el modelo de cuadrantes.")
    
    # Ejemplo de estructura esperada para el usuario
    st.markdown("**Estructura esperada del CSV:**")
    ejemplo_df = pd.DataFrame({
        "Hora": ["10:00", "11:00", "12:00", "13:00"],
        "Trafico_Clientes": [15, 45, 85, 30],
        "Ventas_Euros": [250, 600, 1200, 400],
        "Personal_Actual": [2, 2, 3, 3]
    })
    st.dataframe(ejemplo_df)
