import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Análisis Temporal de Pallets", layout="wide")

# Carga de datos
@st.cache_data
def load_data():
    return pd.read_excel('C:/Users/Sistemas/Desktop/proyecto_pallets/data/enero_limpio.xlsx')

df = load_data()
df['fecha'] = pd.to_datetime(df['fecha'])

# Sidebar con controles
st.sidebar.header("🔍 Filtros de Análisis")

# Selector múltiple de socios
selected_socios = st.sidebar.multiselect(
    "Seleccionar socios para comparar",
    options=df['socio'].unique(),
    default=[df['socio'].unique()[0]]  # Primero por defecto
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
            total_final = socio_data['Total final por socio'].iloc[0]
            dias = (fecha_max - fecha_min).days + 1
            promedio_diario = total_final / dias
            
            fig.add_hline(
                y=promedio_diario,
                line_dash="dot",
                line_color=px.colors.qualitative.Plotly[selected_socios.index(socio) % len(px.colors.qualitative.Plotly)],
                annotation_text=f"Ref. {socio}: {promedio_diario:.1f} pallets/día",
                annotation_position="bottom right"
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
       # with col4:
       #     variacion = ((socio_data['pallets'].mean() / (socio_data['Total final por socio'].iloc[0] / len(socio_data)) - 1)
       #                 if socio_data['Total final por socio'].iloc[0] != 0 else 0)
        #    st.metric("Variación vs Contrato", f"{variacion:.1%}")

# Tabla detallada
st.subheader("📋 Datos Detallados")
st.dataframe(
    filtered_df[['fecha', 'socio', 'pallets', 'Total final por socio', 'Exceso Palets contra (Fijo+Variable)']]
    .sort_values(['socio', 'fecha']),
    use_container_width=True,
    height=400
)