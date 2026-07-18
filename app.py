import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Smart Shift Planner | Weekly Edition", layout="wide")

st.title("📊 Optimizador de Cuadrantes (Smart Shift Planner)")
st.markdown("Herramienta avanzada para Store Managers: Optimización de plantilla, vista semanal, asignación de zonas (Zoning) y cálculo de impacto financiero.")

# Opciones de carga de datos
col_upload, col_demo = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader("Sube el archivo CSV semanal (Columnas requeridas: Dia, Hora, Trafico_Clientes, Personal_Actual)", type=["csv"])

with col_demo:
    st.markdown("<br>", unsafe_allow_html=True) # Espaciado
    demo_mode = st.checkbox("🚀 Cargar Semana de Demostración (Modo Demo)")

# Variable para almacenar el dataframe completo de la semana
df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif demo_mode:
    # Generar datos demo simulando una semana completa real en Retail (Fast-Fashion)
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas_jornada = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
    
    # Curvas base de tráfico según el tipo de día para darle realismo
    trafico_laborables = [15, 45, 95, 40, 15, 25, 80, 130, 160, 110, 50, 20]
    trafico_fin_semana = [30, 75, 140, 90, 40, 55, 120, 180, 210, 175, 90, 35]
    
    # Plantillas actuales medias programadas habitualmente
    personal_laborables = [2, 2, 3, 3, 2, 2, 3, 4, 4, 4, 3, 2]
    personal_fin_semana = [3, 3, 4, 4, 3, 3, 4, 5, 5, 5, 4, 3]
    
    registros = []
    for dia in dias_semana:
        es_finde = dia in ["Viernes", "Sábado", "Domingo"]
        trafico_dia = trafico_fin_semana if es_finde else trafico_laborables
        personal_dia = personal_fin_semana if es_finde else personal_laborables
        
        for idx, hora in enumerate(horas_jornada):
            registros.append({
                "Dia": dia,
                "Hora": hora,
                "Trafico_Clientes": trafico_dia[idx],
                "Personal_Actual": personal_dia[idx]
            })
    df = pd.DataFrame(registros)

# Si hay datos (ya sea por archivo o por demo), mostramos la herramienta
if df is not None:
    
    # --- SIDEBAR: PARÁMETROS OPERATIVOS Y FINANCIEROS ---
    st.sidebar.header("⚙️ Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", min_value=10, max_value=40, value=20)
    
    st.sidebar.header("💰 Parámetros Financieros")
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (€)", min_value=5.0, value=25.0, step=1.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", min_value=5, max_value=50, value=15) / 100.0

    # --- CÁLCULOS GLOBALES SEMANALES ---
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo)', 
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso)', 'Óptimo'))

    # Calculadora de Fuga de Ventas Semanal
    df['Capacidad_Actual'] = df['Personal_Actual'] * clientes_por_empleado
    df['Clientes_Excedentes'] = np.maximum(0, df['Trafico_Clientes'] - df['Capacidad_Actual'])
    df['Fuga_Ventas_Euros'] = df['Clientes_Excedentes'] * tasa_conversion * ticket_medio

    # Módulo de Asignación de Zonas (Zoning)
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

    # --- SECTOR DE CONTROL TEMPORAL (SELECTOR DE DÍA) ---
    st.markdown("---")
    st.markdown("### 🗓️ Control y Planificación de la Semana")
    
    # KPI Global del total de horas necesarias a la semana (Mulaya: Control de costes de personal)
    total_horas_semanales_optimas = df['Personal_Optimo'].sum()
    st.info(f"📋 **Análisis de Capacidad:** El volumen de tráfico detectado requiere cubrir un total de **{int(total_horas_semanales_optimas)} horas de trabajo efectivas** distribuidas en la semana.")
    
    dias_disponibles = df['Dia'].unique()
    dia_seleccionado = st.selectbox("Selecciona un día específico para auditar y ver su Zoning en detalle:", dias_disponibles)
    
    # Filtrar el dataframe para mostrar solo la jornada seleccionada
    df_filtrado = df[df['Dia'] == dia_seleccionado].copy()

    # --- MÉTRICAS PRINCIPALES DEL DÍA SELECCIONADO ---
    st.markdown(f"### 🎯 Resumen Operativo y Financiero ({dia_seleccionado})")
    fuga_total_dia = df_filtrado['Fuga_Ventas_Euros'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Horas de Riesgo", f"{len(df_filtrado[df_filtrado['Deficit_Personal'] > 0])} hrs", help="Horas donde falta personal en este día")
    col2.metric("Horas Ineficientes", f"{len(df_filtrado[df_filtrado['Deficit_Personal'] < 0])} hrs", help="Horas donde sobra personal en este día")
    col3.metric("Fuga de Ventas Estimada", f"€ {fuga_total_dia:,.2f}", delta="- Pérdida", delta_color="inverse")
    col4.metric("Tráfico Total del Día", f"{df_filtrado['Trafico_Clientes'].sum()} pax")

    # --- GRÁFICOS DEL DÍA SELECCIONADO ---
    col_graf_1, col_graf_2 = st.columns(2)
    
    with col_graf_1:
        fig_estres = px.bar(df_filtrado, x='Hora', y='Deficit_Personal', 
                            color='Nivel_Estres',
                            color_discrete_map={'Alto (Riesgo)': '#e74c3c', 'Óptimo': '#2ecc71', 'Bajo (Exceso)': '#3498db'},
                            title=f"Mapa de Estrés Operativo ({dia_seleccionado})")
        st.plotly_chart(fig_estres, use_container_width=True)
        
    with col_graf_2:
        fig_fuga = px.line(df_filtrado, x='Hora', y='Fuga_Ventas_Euros', markers=True, 
                           title=f"Impacto Financiero: Fuga de Ventas por Hora ({dia_seleccionado})",
                           color_discrete_sequence=['#e67e22'])
        fig_fuga.update_traces(line_shape='spline')
        st.plotly_chart(fig_fuga, use_container_width=True)

    # --- TENDENCIA COMPLETA SEMANAL (NUEVA PERSPECTIVA COMPARATIVA) ---
    st.markdown("### 📈 Tendencia Comparativa del Tráfico Semanal")
    fig_semanal = px.bar(df, x="Hora", y="Trafico_Clientes", color="Dia", barmode="group",
                         title="Análisis de patrones de tráfico horario cruzando los 7 días de la semana")
    st.plotly_chart(fig_semanal, use_container_width=True)

    # --- TABLA DE PLANIFICACIÓN Y ZONING DEL DÍA ---
    st.markdown(f"### 📋 Planificación Recomendada y Zoning ({dia_seleccionado})")
    tabla_mostrar = df_filtrado[['Hora', 'Trafico_Clientes', 'Personal_Actual', 'Personal_Optimo', 'Zoning_Recomendado', 'Fuga_Ventas_Euros']].copy()
    tabla_mostrar.columns = ['Hora', 'Tráfico Clientes', 'Personal Actual', 'Personal Óptimo', 'Distribución (Zoning)', 'Fuga de Ventas (€)']
    
    tabla_mostrar['Fuga de Ventas (€)'] = tabla_mostrar['Fuga de Ventas (€)'].apply(lambda x: f"€ {x:,.2f}")
    st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True)

    # --- 3. OPTIMIZADOR DE DESCANSOS (BREAK PLANNER) ---
    st.markdown(f"### ☕ Optimizador de Descansos (Break Planner - {dia_seleccionado})")
    horas_valle = df_filtrado[df_filtrado['Deficit_Personal'] < 0][['Hora', 'Deficit_Personal', 'Personal_Actual']].copy()
    
    if not horas_valle.empty:
        horas_valle['Deficit_Personal'] = horas_valle['Deficit_Personal'].abs()
        horas_valle.columns = ['Franja Horaria', 'Exceso de Personal (Plantilla Libre)', 'Personal Total en Tienda']
        st.success("✅ Se han detectado franjas seguras. Se recomienda organizar los descansos del equipo en los siguientes tramos:")
        st.table(horas_valle.sort_values(by='Exceso de Personal (Plantilla Libre)', ascending=False).head(3))
    else:
        st.warning("⚠️ No se detectan franjas con exceso de personal para esta jornada. Ajustar descansos requerirá refuerzos externos o cierres parciales de zonas.")

else:
    # Pantalla de inicio si no hay datos ni demo activa
    st.info("👈 Sube tu archivo CSV semanal o activa el **Modo Demo** en la barra superior para visualizar el Optimizador.")
    
    st.markdown("**Estructura esperada del archivo CSV Semanal:**")
    ejemplo_df = pd.DataFrame({
        "Dia": ["Lunes", "Lunes", "Martes", "Martes"],
        "Hora": ["12:00", "18:00", "12:00", "18:00"],
        "Trafico_Clientes": [95, 160, 45, 130],
        "Personal_Actual": [3, 4, 2, 4]
    })
    st.dataframe(ejemplo_df, hide_index=True)

# --- FOOTER ---
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
))
