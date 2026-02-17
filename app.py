import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Dinámico", layout="wide")

st.title("📊 Analizador de Reportes Appsflyer")
st.markdown("Sube tu archivo CSV para comenzar el análisis automáticamente.")

# --- ZONA DE CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Arrastra tu archivo CSV aquí", type=["csv"])

if uploaded_file is not None:
    # --- PROCESAR EL ARCHIVO SUBIDO ---
    try:
        df = pd.read_csv(uploaded_file)
        
        # Limpieza y conversión de columnas numéricas (igual que antes)
        cols_num = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count', 'ok_ratio', 'paced_ratio']
        
        # Validar que las columnas existan
        missing_cols = [c for c in cols_num if c not in df.columns]
        if missing_cols:
            st.error(f"⚠️ El archivo subido no tiene las columnas correctas. Faltan: {missing_cols}")
            st.stop() # Detener la ejecución si el archivo no es válido

        for col in cols_num:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Asegurar strings para filtros
        for col_str in ['agency', 'template', 'pid']:
            if col_str in df.columns:
                df[col_str] = df[col_str].astype(str)
        
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
            if selected_agency:
                df_step2 = df[(df['agency'].isin(selected_agency)) & (df['template'].isin(selected_template))]
            else:
                df_step2 = df[df['template'].isin(selected_template)]
            available_pids = sorted(df_step2['pid'].unique())
        elif selected_agency:
            available_pids = sorted(df[df['agency'].isin(selected_agency)]['pid'].unique())
        else:
            available_pids = sorted(df['pid'].unique())

        selected_pid = st.sidebar.multiselect("PID", available_pids)

        # --- APLICAR FILTROS ---
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

        # --- TABLA ---
        with st.expander("Ver Tabla de Datos", expanded=True):
            st.dataframe(df_filtered, use_container_width=True)

        # --- GRAFICAS ---
        st.markdown("### 📈 Visualización")
        
        c1, c2 = st.columns(2)
        with c1:
            y_axis = st.selectbox("Eje Y", cols_num)
        with c2:
            x_axis = st.selectbox("Eje X", ['agency', 'template', 'pid'])

        if not df_filtered.empty:
            df_chart = df_filtered.groupby(x_axis)[y_axis].sum().reset_index()
            df_chart = df_chart.sort_values(by=y_axis, ascending=False).head(20)

            fig = px.bar(
                df_chart, 
                x=x_axis, 
                y=y_axis,
                title=f"Top 20 {x_axis} por {y_axis}",
                color=y_axis,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos para mostrar con esos filtros.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

else:
    # --- PANTALLA DE BIENVENIDA (SIN ARCHIVO) ---
    st.info("👆 Sube un archivo CSV en el recuadro de arriba para empezar.")
