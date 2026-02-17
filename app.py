import streamlit as st
import pandas as pd
import plotly.express as px
import re # Librería para buscar números en texto

# Configuración de la página
st.set_page_config(page_title="Dashboard Evolutivo", layout="wide")

st.title("📊 Dashboard Appsflyer (Evolución por Día)")
st.markdown("Sube tus archivos. Puedes nombrarlos simplemente '12', '13', '14'... el sistema los ordenará correctamente.")

# --- CARGA DE ARCHIVOS ---
uploaded_files = st.file_uploader("Sube tus CSVs aquí", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    # --- PROCESAMIENTO ---
    all_dataframes = []
    
    try:
        for file in uploaded_files:
            df_temp = pd.read_csv(file)
            
            # 1. Limpiamos el nombre (quitamos .csv)
            clean_name = file.name.replace('.csv', '').replace('.CSV', '')
            
            # 2. Buscamos el número del día para ordenar bien
            # Esto busca el primer número que encuentre en el nombre del archivo
            found_numbers = re.findall(r'\d+', clean_name)
            
            if found_numbers:
                day_number = int(found_numbers[0])
            else:
                day_number = 0 # Si no hay número, lo pone al principio
            
            # Guardamos el nombre para mostrar y el número para ordenar
            df_temp['source_name'] = clean_name
            df_temp['day_sort_key'] = day_number
            
            all_dataframes.append(df_temp)
        
        # Unir todos
        df = pd.concat(all_dataframes, ignore_index=True)
        
        # --- ORDENAR INTELIGENTE ---
        # Ordenamos por el número encontrado, no por el texto
        df = df.sort_values('day_sort_key')
        
        st.success(f"✅ Se han cargado {len(uploaded_files)} días. Ordenados del día {df['day_sort_key'].min()} al {df['day_sort_key'].max()}.")
        
        # --- LIMPIEZA DE COLUMNAS ---
        cols_metrics = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count', 'ok_ratio', 'paced_ratio']
        
        # Validar columnas
        missing = [c for c in cols_metrics if c not in df.columns]
        if missing:
            st.error(f"Faltan columnas clave: {missing}")
            st.stop()

        # Convertir a números
        for col in cols_metrics:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Convertir textos
        for col in ['agency', 'template', 'pid', 'source_name']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # --- FILTROS ---
        st.sidebar.header("Filtros")

        # 1. Agency
        all_agencies = sorted(df['agency'].unique())
        sel_agency = st.sidebar.multiselect("Agency", all_agencies)

        # 2. Template
        if sel_agency:
            df_s1 = df[df['agency'].isin(sel_agency)]
            opts_templ = sorted(df_s1['template'].unique())
        else:
            opts_templ = sorted(df['template'].unique())
        sel_template = st.sidebar.multiselect("Template", opts_templ)

        # 3. PID
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

        # --- APLICAR FILTROS ---
        df_filtered = df.copy()
        if sel_agency: df_filtered = df_filtered[df_filtered['agency'].isin(sel_agency)]
        if sel_template: df_filtered = df_filtered[df_filtered['template'].isin(sel_template)]
        if sel_pid: df_filtered = df_filtered[df_filtered['pid'].isin(sel_pid)]

        # --- GRÁFICA DE EVOLUCIÓN ---
        st.markdown("---")
        st.markdown("### 📈 Evolución Mensual")

        # Agrupar por día (usando source_name y day_sort_key)
        agg_rules = {
            'cloudfront_ok_count': 'sum',
            'cloudfront_error_count': 'sum',
            'paced_count': 'sum',
            'ok_ratio': 'mean',
            'paced_ratio': 'mean',
            'day_sort_key': 'first' # Mantenemos el número para ordenar la gráfica
        }
        
        # Agrupamos por el nombre del archivo
        df_time = df_filtered.groupby('source_name').agg(agg_rules).reset_index()
        
        # ¡IMPORTANTE! Volvemos a ordenar la tabla resumida para que la gráfica salga bien
        df_time = df_time.sort_values('day_sort_key')

        col_sel, col_chart = st.columns([1, 3])
        
        with col_sel:
            st.markdown("**Elige qué ver:**")
            metrics_to_plot = st.multiselect(
                "Métricas",
                options=cols_metrics,
                default=['cloudfront_ok_count']
            )

        with col_chart:
            if metrics_to_plot:
                fig_line = px.line(
                    df_time, 
                    x='source_name', 
                    y=metrics_to_plot, 
                    markers=True,
                    title="Tendencia Diaria",
                    labels={'source_name': 'Día (Archivo)', 'value': 'Valor', 'variable': 'Métrica'}
                )
                fig_line.update_layout(hovermode="x unified")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Selecciona métricas a la izquierda.")

        # --- TABLA DE DATOS ---
        with st.expander("Ver detalle de datos"):
            st.dataframe(df_filtered)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Sube tus archivos CSV (Ej: '12.csv', '13.csv').")
