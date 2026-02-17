import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Appsflyer", layout="wide")

st.title("📊 Dashboard de Reporte Appsflyer")

# --- CARGAR DATOS ---
@st.cache_data
def load_data():
    try:
        # AQUÍ ESTÁ EL CAMBIO: Ahora lee "Data.csv" con mayúscula
        df = pd.read_csv("Data.csv")
        
        # Limpieza y conversión de columnas numéricas
        cols_num = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count', 'ok_ratio', 'paced_ratio']
        for col in cols_num:
            # Reemplazar comas si existen y convertir a numérico
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Asegurar que las columnas de filtro sean strings para evitar errores
        df['agency'] = df['agency'].astype(str)
        df['template'] = df['template'].astype(str)
        df['pid'] = df['pid'].astype(str)
            
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'Data.csv'. Asegúrate de que en GitHub el archivo empiece con mayúscula.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")

    # 1. Filtro Agency
    all_agencies = sorted(df['agency'].unique())
    selected_agency = st.sidebar.multiselect("Agency", all_agencies)

    # 2. Filtro Template (Dinámico)
    if selected_agency:
        df_step1 = df[df['agency'].isin(selected_agency)]
        available_templates = sorted(df_step1['template'].unique())
    else:
        available_templates = sorted(df['template'].unique())
        
    selected_template = st.sidebar.multiselect("Template", available_templates)

    # 3. Filtro PID (Dinámico)
    if selected_template:
        # Si hay template seleccionado, filtramos sobre lo anterior
        if selected_agency:
            df_step2 = df[(df['agency'].isin(selected_agency)) & (df['template'].isin(selected_template))]
        else:
            df_step2 = df[df['template'].isin(selected_template)]
        available_pids = sorted(df_step2['pid'].unique())
    elif selected_agency:
        # Si solo hay agencia
        available_pids = sorted(df[df['agency'].isin(selected_agency)]['pid'].unique())
    else:
        # Si no hay nada seleccionado
        available_pids = sorted(df['pid'].unique())

    selected_pid = st.sidebar.multiselect("PID", available_pids)

    # --- APLICAR TODOS LOS FILTROS ---
    df_filtered = df.copy()

    if selected_agency:
        df_filtered = df_filtered[df_filtered['agency'].isin(selected_agency)]
    
    if selected_template:
        df_filtered = df_filtered[df_filtered['template'].isin(selected_template)]

    if selected_pid:
        df_filtered = df_filtered[df_filtered['pid'].isin(selected_pid)]

    # --- KPI CARDS ---
    st.markdown("---")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Registros", len(df_filtered))
    kpi2.metric("Total OK Count", f"{int(df_filtered['cloudfront_ok_count'].sum()):,}")
    kpi3.metric("Promedio OK Ratio", f"{df_filtered['ok_ratio'].mean():.2%}")

    # --- TABLA DE DATOS ---
    with st.expander("Ver Tabla de Datos Detallada", expanded=True):
        st.dataframe(df_filtered, use_container_width=True)

    # --- VISUALIZACIÓN ---
    st.markdown("### 📈 Gráficas")
    
    col_chart_1, col_chart_2 = st.columns(2)
    
    with col_chart_1:
        y_axis_val = st.selectbox("Eje Y (Métrica)", ['cloudfront_ok_count', 'cloudfront_error_count', 'ok_ratio', 'paced_count'])
    
    with col_chart_2:
        x_axis_val = st.selectbox("Eje X (Categoría)", ['agency', 'template', 'pid'])

    if not df_filtered.empty:
        # Agrupar datos para la gráfica
        df_chart = df_filtered.groupby(x_axis_val)[y_axis_val].sum().reset_index()
        # Ordenar y tomar top 20 para que se vea bien
        df_chart = df_chart.sort_values(by=y_axis_val, ascending=False).head(20)

        fig = px.bar(
            df_chart, 
            x=x_axis_val, 
            y=y_axis_val,
            title=f"Top 20 {x_axis_val} por {y_axis_val}",
            color=y_axis_val,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos con los filtros actuales.")

else:
    st.info("Esperando carga de datos...")
