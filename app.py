import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Multi-Archivo", layout="wide")

st.title("📊 Analizador de Reportes (Multi-Día)")
st.markdown("Sube **uno o varios** archivos CSV. La app los combinará automáticamente.")

# --- ZONA DE CARGA DE ARCHIVOS (Múltiple) ---
uploaded_files = st.file_uploader("Arrastra tus archivos CSV aquí", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    # --- PROCESAR Y COMBINAR ARCHIVOS ---
    all_dataframes = []
    
    try:
        for file in uploaded_files:
            # Leer cada archivo
            df_temp = pd.read_csv(file)
            
            # Añadir columna con el nombre del archivo (para distinguir fechas/días)
            df_temp['source_file'] = file.name
            
            all_dataframes.append(df_temp)
        
        # Combinar todos en una sola tabla gigante
        df = pd.concat(all_dataframes, ignore_index=True)
        
        st.success(f"✅ Se han combinado {len(uploaded_files)} archivos correctamente. Total de filas: {len(df)}")
        
        # --- LIMPIEZA DE DATOS ---
        cols_num = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count', 'ok_ratio', 'paced_ratio']
        
        # Validar columnas (solo chequeamos si existen en el combinado)
        missing_cols = [c for c in cols_num if c not in df.columns]
        if missing_cols:
            st.error(f"⚠️ Error: Faltan columnas clave en tus archivos: {missing_cols}")
            st.stop()

        for col in cols_num:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Asegurar strings
        for col_str in ['agency', 'template', 'pid', 'source_file']:
            if col_str in df.columns:
                df[col_str] = df[col_str].astype(str)
        
        # --- BARRA LATERAL (FILTROS) ---
        st.sidebar.header("Filtros")

        # 0. Filtro por Archivo (Opcional, por si quieres ver solo un día específico del grupo)
        all_files = sorted(df['source_file'].unique())
        selected_files = st.sidebar.multiselect("Filtrar por Archivo/Día", all_files)

        # 1. Filtro Agency
        if selected_files:
            df = df[df['source_file'].isin(selected_files)]
            
        all_agencies = sorted(df['agency'].unique())
        selected_agency = st.sidebar.multiselect("Agency", all_agencies)

        # 2. Filtro Template
        if selected_agency:
            df_step1 = df[df['agency'].isin(selected_agency)]
            available_templates = sorted(df_step1['template'].unique())
        else:
            available_templates = sorted(df['template'].unique())
            
        selected_template = st.sidebar.multiselect("Template", available_templates)

        # 3. Filtro PID
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

        # --- APLICAR RESTO DE FILTROS ---
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
        # Sumamos los totales de TODOS los archivos seleccionados
        kpi1.metric("Total Tráfico OK", f"{int(df_filtered['cloudfront_ok_count'].sum()):,}")
        kpi2.metric("Total Errores", f"{int(df_filtered['cloudfront_error_count'].sum()):,}")
        # Promedio ponderado simple del ratio
        avg_ratio = df_filtered['ok_ratio'].mean() if not df_filtered.empty else 0
        kpi3.metric("Ratio OK Promedio", f"{avg_ratio:.2%}")

        # --- TABLA ---
        with st.expander("Ver Datos Combinados", expanded=False):
            st.dataframe(df_filtered, use_container_width=True)

        # --- GRÁFICAS ---
        st.markdown("### 📈 Visualización Comparativa")
        
        c1, c2 = st.columns(2)
        with c1:
            y_axis = st.selectbox("Métrica (Eje Y)", cols_num)
        with c2:
            # Añadimos 'source_file' para poder comparar días en la gráfica
            x_axis = st.selectbox("Agrupar por (Eje X)", ['agency', 'template', 'pid', 'source_file'])

        if not df_filtered.empty:
            # Agrupar
            df_chart = df_filtered.groupby(x_axis)[y_axis].sum().reset_index()
            # Top 20
            df_chart = df_chart.sort_values(by=y_axis, ascending=False).head(30)

            fig = px.bar(
                df_chart, 
                x=x_axis, 
                y=y_axis,
                title=f"{y_axis} por {x_axis}",
                color=y_axis,
                color_continuous_scale='Viridis',
                text_auto='.2s' # Muestra el valor encima de la barra resumido (ej: 1.5M)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos tras filtrar.")

    except Exception as e:
        st.error(f"Ocurrió un error al procesar los archivos: {e}")

else:
    st.info("👆 Arrastra tus archivos CSV (Reporte_Lunes.csv, Reporte_Martes.csv...) para comenzar.")
