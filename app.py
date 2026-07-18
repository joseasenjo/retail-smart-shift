import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Smart Shift Planner | Retail Analytics", layout="wide")

st.title("📊 Optimizador de Cuadrantes (Smart Shift Planner)")
st.markdown("Herramienta avanzada para Store Managers: Optimización de plantilla, asignación de zonas (Zoning) y cálculo de impacto financiero.")

# Subida de archivo (Procesamiento directo en RAM)
uploaded_file = st.file_uploader("Sube el archivo CSV (Columnas requeridas: Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # --- SIDEBAR: PARÁMETROS OPERATIVOS Y FINANCIEROS ---
    st.sidebar.header("⚙️ Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", min_value=10, max_value=40, value=20)
    
    st.sidebar.header("💰 Parámetros Financieros")
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (€)", min_value=5.0, value=25.0, step=1.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", min_value=5, max_value=50, value=15) / 100.0

    # --- CÁLCULOS BASE ---
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo)', 
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso)', 'Óptimo'))

    # --- 1. CALCULADORA DE FUGA DE VENTAS ---
    # Calculamos cuántos clientes exceden la capacidad de atención del personal actual
    df['Capacidad_Actual'] = df['Personal_Actual'] * clientes_por_empleado
    df['Clientes_Excedentes'] = np.maximum(0, df['Trafico_Clientes'] - df['Capacidad_Actual'])
    # Estimamos el dinero perdido asumiendo que esos clientes no compran por falta de atención
    df['Fuga_Ventas_Euros'] = df['Clientes_Excedentes'] * tasa_conversion * ticket_medio

    # --- 2. MÓDULO DE ASIGNACIÓN DE ZONAS (ZONING) ---
    def asignar_zonas(personal):
        if personal <= 0:
            return "Tienda Cerrada"
        elif personal == 1:
            return "1 Multitarea (Caja y Planta)"
        elif personal == 2:
            return "1 Caja | 1 Planta/Visual"
        elif personal == 3:
            return "1 Caja | 1 Probadores | 1 Planta"
        else:
            return f"2 Caja | 1 Probadores | {int(personal)-3} Planta"
            
    df['Zoning_Recomendado'] = df['Personal_Optimo'].apply(asignar_zonas)

    # --- MÉTRICAS PRINCIPALES ---
    st.markdown("### 🎯 Resumen Operativo y Financiero")
    fuga_total = df['Fuga_Ventas_Euros'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Horas de Riesgo", f"{len(df[df['Deficit_Personal'] > 0])} hrs", help="Horas donde falta personal")
    col2.metric("Horas Ineficientes", f"{len(df[df['Deficit_Personal'] < 0])} hrs", help="Horas donde sobra personal")
    col3.metric("Fuga de Ventas Estimada", f"€ {fuga_total:,.2f}", delta="- Pérdida", delta_color="inverse")
    col4.metric("Tráfico Total", f"{df['Trafico_Clientes'].sum()} pax")

    # --- GRÁFICOS ---
    col_graf_1, col_graf_2 = st.columns(2)
    
    with col_graf_1:
        fig_estres = px.bar(df, x='Hora', y='Deficit_Personal', 
                            color='Nivel_Estres',
                            color_discrete_map={'Alto (Riesgo)': '#e74c3c', 'Óptimo': '#2ecc71', 'Bajo (Exceso)': '#3498db'},
                            title="Mapa de Estrés Operativo (Déficit/Exceso de Personal)")
        st.plotly_chart(fig_estres, use_container_width=True)
        
    with col_graf_2:
        fig_fuga = px.line(df, x='Hora', y='Fuga_Ventas_Euros', markers=True, 
                           title="Impacto Financiero: Fuga de Ventas por Hora (€)",
                           color_discrete_sequence=['#e67e22'])
        fig_fuga.update_traces(line_shape='spline')
        st.plotly_chart(fig_fuga, use_container_width=True)

    # --- TABLA DE PLANIFICACIÓN Y ZONING ---
    st.markdown("### 📋 Planificación Recomendada y Zoning")
    tabla_mostrar = df[['Hora', 'Trafico_Clientes', 'Personal_Actual', 'Personal_Optimo', 'Zoning_Recomendado', 'Fuga_Ventas_Euros']].copy()
    tabla_mostrar.columns = ['Hora', 'Tráfico Clientes', 'Personal Actual', 'Personal Óptimo', 'Distribución (Zoning)', 'Fuga de Ventas (€)']
    
    # Formatear la columna de euros para la tabla
    tabla_mostrar['Fuga de Ventas (€)'] = tabla_mostrar['Fuga de Ventas (€)'].apply(lambda x: f"€ {x:,.2f}")
    st.dataframe(tabla_mostrar, use_container_width=True)

    # --- 3. OPTIMIZADOR DE DESCANSOS (BREAK PLANNER) ---
    st.markdown("### ☕ Optimizador de Descansos (Break Planner)")
    horas_valle = df[df['Deficit_Personal'] < 0][['Hora', 'Deficit_Personal', 'Personal_Actual']].copy()
    
    if not horas_valle.empty:
        horas_valle['Deficit_Personal'] = horas_valle['Deficit_Personal'].abs() # Convertir a número positivo para leer "Exceso"
        horas_valle.columns = ['Franja Horaria', 'Exceso de Personal', 'Personal en Tienda']
        st.success("✅ Se han detectado franjas seguras. Se recomienda organizar los descansos del equipo en los siguientes tramos:")
        st.table(horas_valle.sort_values(by='Exceso de Personal', ascending=False).head(3))
    else:
        st.warning("⚠️ No se detectan franjas con exceso de personal. Ajustar descansos requerirá refuerzos externos o cierres parciales de zonas.")

else:
    st.info("Por favor, sube un archivo CSV para generar el modelo de cuadrantes.")
    
    # Ejemplo visual para que sepas qué formato subir
    st.markdown("**Estructura esperada del archivo CSV:**")
    ejemplo_df = pd.DataFrame({
        "Hora": ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"],
        "Trafico_Clientes": [15, 45, 95, 40, 15, 30, 110],
        "Personal_Actual": [2, 2, 3, 3, 3, 2, 3]
    })
    st.dataframe(ejemplo_df, hide_index=True)

# --- FOOTER (Firma y Contacto) ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555555; padding: 20px;'>
        <p style='font-size: 16px; margin-bottom: 5px;'>Desarrollado por <b>Jose Luis Asenjo</b></p>
        <a href='https://www.linkedin.com/in/joseluisasenjo' target='_blank' style='text-decoration: none; color: #0077b5; font-weight: bold;'>
            🔗 Conecta conmigo en LinkedIn
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)
