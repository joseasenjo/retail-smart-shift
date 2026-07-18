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
    st.markdown("<br>", unsafe_allow_html=True) 
    demo_mode = st.checkbox("🚀 Cargar Semana de Demostración (Modo Demo)")

# Variable para almacenar el dataframe completo
df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif demo_mode:
    # Generar datos demo simulando una semana completa real
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    horas_jornada = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
    
    trafico_laborables = [15, 45, 95, 40, 15, 25, 80, 130, 160, 110, 50, 20]
    trafico_fin_semana = [30, 75, 140, 90, 40, 55, 120, 180, 210, 175, 90, 35]
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

if df is not None:
    # --- SIDEBAR: PARÁMETROS ---
    st.sidebar.header("⚙️ Parámetros Operativos")
    clientes_por_empleado = st.sidebar.slider("Clientes asumibles por empleado/hora", 10, 40, 20)
    ticket_medio = st.sidebar.number_input("Ticket Medio Estimado (€)", 5.0, 100.0, 25.0)
    tasa_conversion = st.sidebar.slider("Tasa de Conversión Esperada (%)", 5, 50, 15) / 100.0

    # --- CÁLCULOS ---
    df['Personal_Optimo'] = np.ceil(df['Trafico_Clientes'] / clientes_por_empleado)
    df['Deficit_Personal'] = df['Personal_Optimo'] - df['Personal_Actual']
    df['Nivel_Estres'] = np.where(df['Deficit_Personal'] > 0, 'Alto (Riesgo)', 
                                  np.where(df['Deficit_Personal'] < 0, 'Bajo (Exceso)', 'Óptimo'))
    df['Capacidad_Actual'] = df['Personal_Actual'] * clientes_por_empleado
    df['Clientes_Excedentes'] = np.maximum(0, df['Trafico_Clientes'] - df['Capacidad_Actual'])
    df['Fuga_Ventas_Euros'] = df['Clientes_Excedentes'] * tasa_conversion * ticket_medio

    def asignar_zonas(p):
        if p <= 0: return "Tienda Cerrada"
        elif p == 1: return "1 Multitarea (Caja y Planta)"
        elif p == 2: return "1 Caja | 1 Planta/Visual"
        elif p == 3: return "1 Caja | 1 Probadores | 1 Planta"
        else: return f"2 Caja | 1 Probadores | {int(p)-3} Planta"
            
    df['Zoning_Recomendado'] = df['Personal_Optimo'].apply(asignar_zonas)

    # --- VISTA SEMANAL ---
    st.markdown("---")
    st.markdown("### 🗓️ Control y Planificación de la Semana")
    st.info(f"📋 **Análisis de Capacidad:** Requiere cubrir un total de **{int(df['Personal_Optimo'].sum())} horas efectivas** esta semana.")
    
    dia_seleccionado = st.selectbox("Selecciona un día para auditar:", df['Dia'].unique())
    df_dia = df[df['Dia'] == dia_seleccionado].copy()

    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Horas Riesgo", f"{len(df_dia[df_dia['Deficit_Personal'] > 0])} hrs")
    col2.metric("Horas Ineficientes", f"{len(df_dia[df_dia['Deficit_Personal'] < 0])} hrs")
    col3.metric("Fuga Ventas", f"€ {df_dia['Fuga_Ventas_Euros'].sum():,.2f}")
    col4.metric("Tráfico Total", f"{df_dia['Trafico_Clientes'].sum()} pax")

    # Gráficos
    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(px.bar(df_dia, x='Hora', y='Deficit_Personal', color='Nivel_Estres', title="Estrés Operativo"), use_container_width=True)
    with c2: st.plotly_chart(px.line(df_dia, x='Hora', y='Fuga_Ventas_Euros', markers=True, title="Fuga de Ventas (€)"), use_container_width=True)

    # Tabla
    st.markdown(f"### 📋 Planificación: {dia_seleccionado}")
    st.dataframe(df_dia[['Hora', 'Trafico_Clientes', 'Personal_Actual', 'Personal_Optimo', 'Zoning_Recomendado']], use_container_width=True, hide_index=True)

    # Descansos
    if not df_dia[df_dia['Deficit_Personal'] < 0].empty:
        st.success("✅ Franjas recomendadas para descansos detectadas en la tabla anterior (donde sobra personal).")
    
else:
    st.info("👈 Sube CSV semanal o activa **Modo Demo**.")

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
)
