import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Temporal", layout="wide")

st.title("⏱️ Analizador de Tráfico por Horas/Días")
st.markdown("Sube tu CSV con datos históricos (debe tener una columna de fecha u hora).")

# --- CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Sube tu archivo CSV único aquí", type=["csv"])

if uploaded_file is not None:
    try:
        # Cargar datos
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ Archivo cargado: {len(df)} filas.")

        # --- SELECCIÓN DE COLUMNA DE TIEMPO ---
        st.markdown("### 1️⃣ Configuración de Tiempo")
        st.info("Selecciona cuál de tus columnas contiene la fecha/hora para ordenar la gráfica.")
        
        # Intentamos adivinar columnas comunes de tiempo
        possible_time_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'fecha' in c.lower() or 'hora' in c.lower()]
        default_idx = df.columns.get_loc(possible_time_cols[0]) if possible_time_cols else 0
        
        time_col = st.selectbox("Columna de Fecha/Hora:", df.columns, index=default_idx)

        # Convertir esa columna a datetime para que se ordene bien
        try:
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col) # Ordenamos por tiempo
        except Exception as e:
            st.warning(f"⚠️ No pudimos convertir '{time_col}' a formato fecha automáticamente. Se usará como texto. Error: {e}")

        # --- LIMPIEZA DE MÉTRICAS ---
        # Solo las que pediste (sin ratios)
        cols_metrics = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
        
        # Validar que existan
        available_metrics = [c for c in cols_metrics if c in df.columns]
        if not available_metrics:
            st.error(f"❌ No se encontraron las columnas de métricas esperadas: {cols_metrics}")
            st.stop()

        # Convertir a números (limpiar comas si las hay)
        for col in available_metrics:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Convertir filtros a texto
        for col in ['agency', 'template', 'pid']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # --- FILTROS ---
        st.sidebar.header("Filtros")

        # 1. Agency
        if 'agency' in df.columns:
            all_agencies = sorted(df['agency'].unique())
            sel_agency = st.sidebar.multiselect("Agency", all_agencies)
        else:
            sel_agency = []

        # 2. Template
        if 'template' in df.columns:
            if sel_agency:
                df_s1 = df[df['agency'].isin(sel_agency)]
                opts_templ = sorted(df_s1['template'].unique())
            else:
                opts_templ = sorted(df['template'].unique())
            sel_template = st.sidebar.multiselect("Template", opts_templ)
        else:
            sel_template = []

        # 3. PID
        if 'pid' in df.columns:
            if sel_template:
                if sel_agency:
                    df_s2 = df[(df['agency'].isin(sel_agency)) & (df['template'].isin(sel_template))]
                else:
                    df_s2 = df[df['template'].isin(sel_template)]
                opts_pid = sorted(df_s2['pid'].unique())
            elif sel_agency:
                opts_pid = sorted(df[df['agency'].isin(sel_agency)]['pid'].unique())
            else:
                opts_pid = sorted(df['pid'].unique())
            sel_pid = st.sidebar.multiselect("PID", opts_pid)
        else:
            sel_pid = []

        # --- APLICAR FILTROS ---
        df_filtered = df.copy()
        if sel_agency: df_filtered = df_filtered[df_filtered['agency'].isin(sel_agency)]
        if sel_template: df_filtered = df_filtered[df_filtered['template'].isin(sel_template)]
        if sel_pid: df_filtered = df_filtered[df_filtered['pid'].isin(sel_pid)]

        # --- GRÁFICA DE EVOLUCIÓN ---
        st.markdown("---")
        st.markdown(f"### 📈 Evolución por {time_col}")

        # Agrupar por la columna de tiempo seleccionada
        # Sumamos los contadores
        df_time = df_filtered.groupby(time_col)[available_metrics].sum().reset_index()

        col_sel, col_chart = st.columns([1,
