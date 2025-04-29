import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Análisis Temporal de Pallets", layout="wide")

# Autenticación
if not st.session_state.get("authenticated", False):
    password = st.text_input("🔐 Ingresa la contraseña para acceder:", type="password")
    clave_valida = st.secrets["general"]["PASSWORD"]

    if password == clave_valida:
        st.session_state.authenticated = True
        st.rerun()
    elif password != "":
        st.error("❌ Contraseña incorrecta")
        st.stop()  # Detiene la ejecución si la contraseña es incorrecta

# Contenido de la app: solo se ejecuta si estás autenticado
if st.session_state.get("authenticated"):

    # Carga de datos
    @st.cache_data
    def load_data():
        return pd.read_excel('C:/Users/Sistemas/Desktop/proyecto_pallets/data/marzo_limpio.xlsx')

    df = load_data()
    df['fecha'] = pd.to_datetime(df['fecha'])

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