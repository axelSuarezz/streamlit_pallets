import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Análisis Temporal de Pallets", layout="wide")

# --- Ruta del archivo (compatible con Windows y Linux) ---
def get_file_path():
    # Ruta en Windows
    windows_path = r"C:\Users\Sistemas\streamlit_pallets\data\marzo_limpio.xlsx"
    # Conversión para Linux (Streamlit Cloud / Docker)
    linux_path = windows_path.replace("C:\\", "/mnt/c/").replace("\\", "/")
    
    # Verifica cuál ruta existe
    if os.path.exists(windows_path):
        return windows_path
    elif os.path.exists(linux_path):
        return linux_path
    else:
        st.error("❌ No se encontró el archivo en ninguna ruta esperada.")
        st.stop()

# Carga de datos
@st.cache_data
def load_data():
    file_path = get_file_path()
    return pd.read_excel(file_path)

try:
    df = load_data()
    df['fecha'] = pd.to_datetime(df['fecha'])
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

    # Sidebar con controles
    st.sidebar.header("🔍 Filtros de Análisis")

    # Selector múltiple de socios
    selected_socios = st.sidebar.multiselect(
        "Seleccionar socios para comparar",
        options=df['socio'].unique(),
        default=[df['socio'].unique()[0]]
    )

    # Selector de rango de fechas
    fecha_min, fecha_max = st.sidebar.slider(
        "Seleccionar rango de fechas",
        min_value=df['fecha'].min().to_pydatetime(),
        max_value=df['fecha'].max().to_pydatetime(),
        value=(df['fecha'].min().to_pydatetime(), df['fecha'].max().to_pydatetime())
    )

    # Filtrado de datos
    filtered_df = df[
        (df['socio'].isin(selected_socios)) & 
        (df['fecha'].between(fecha_min, fecha_max))
    ]

    # Página principal
    st.title("📈 Evolución Diaria de Pallets por Socio")
    st.markdown("---")

    # Gráfico principal
    if not selected_socios:
        st.warning("Por favor selecciona al menos un socio")
    else:
        fig = px.line(
            filtered_df,
            x='fecha',
            y='pallets',
            color='socio',
            title=f"Pallets Diarios por Socio ({fecha_min.date()} al {fecha_max.date()})",
            labels={'pallets': 'Cantidad de Pallets', 'fecha': 'Fecha'},
            markers=True
        )
        
        # Añadir línea de total final por socio (promedio diario estimado)
        for socio in selected_socios:
            socio_data = filtered_df[filtered_df['socio'] == socio]
            if not socio_data.empty:
                cupo_total = socio_data['Total final por socio'].iloc[0]

                
                fig.add_hline(
                    y=cupo_total,
                    line_dash="dot",
                    line_color= "red",
                    opacity=0.5,
                    annotation_text=f"Cupo. {socio}: {cupo_total:.1f}",
                    annotation_position="bottom right",
                    annotation_font_color="red",
                    annotation_font_size=10,
                    
                )
        
        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Fecha',
            yaxis_title='Cantidad de Pallets',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Métricas complementarias
    st.subheader("📊 Resumen por Socio Seleccionado")

    for socio in selected_socios:
        socio_data = filtered_df[filtered_df['socio'] == socio]
        if not socio_data.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                promedio = socio_data['Promedio pallets por socio diario'].mean()
                st.metric(f"{socio} - Promedio de pallets mensual", promedio)

            with col2:
                st.metric("Total Final Por Contrato", socio_data['Total final por socio'].iloc[0])

            with col3:
                st.metric("Promedio Diario Real", f"{socio_data['pallets'].mean():.1f}")

    # Tabla detallada
    st.subheader("📋 Datos Detallados")
    st.dataframe(
        filtered_df[['fecha', 'socio', 'pallets', 'Total final por socio']]
        .assign(
            Diferencia=lambda x: (x['pallets'] - x['Total final por socio'])*(-1),
        )
        .sort_values(['socio', 'fecha']),
        hide_index=True,
        use_container_width=True,
        height=400,
        # Configuración de columnas
        column_config={
        'fecha': st.column_config.DateColumn(
            '📅 Fecha',
            format="DD/MM/YYYY",),
        'socio': '🤝 Socio',
        'pallets': '📦 Pallets por dia',
        'Total final por socio': '💰 Cupo asignado',
        'Diferencia': st.column_config.NumberColumn(
            '⚠️ Excedente',
            format="%+d",
            help="Positivo = exceso, Negativo = dentro del cupo"),
        'Exceso Palets contra (Fijo+Variable)': '⚠️ Exceso de Pallets' }
    )