import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Temporal Completo", layout="wide")

st.title("⏱️ Analizador de Tráfico (Filtros + Tiempo)")
st.markdown("Sube tu CSV histórico. Podrás filtrar por Agency/Template/PID y ver la evolución temporal.")

# --- CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Sube tu archivo CSV único aquí", type=["csv"])

if uploaded_file is not None:
    try:
        # Cargar datos
        df = pd.read_csv(uploaded_file)
        
        # --- TRUCO: NORMALIZAR COLUMNAS ---
        # Convertimos todos los nombres de columnas a minúsculas para evitar errores
        # Así funciona igual si tu columna se llama "Agency", "AGENCY" o "agency"
        df.columns = df.columns.str.lower().str.strip()
        
        st.success(f"✅ Archivo cargado: {len(df)} filas detectadas.")

        # --- 1. CONFIGURACIÓN DE TIEMPO ---
        st.markdown("### 1️⃣ Configuración de Tiempo")
        
        # Buscamos columnas que parezcan fechas
        possible_time_cols = [c for c in df.columns if any(x in c for x in ['date', 'time', 'fecha', 'hora', 'day', 'dia'])]
        default_idx = df.columns.get_loc(possible_time_cols[0]) if possible_time_cols else 0
        
        time_col = st.selectbox("¿Cuál es la columna de Fecha/Hora?", df.columns, index=default_idx)

        # Convertir a datetime
        try:
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col)
        except Exception as e:
            st.warning(f"⚠️ La columna '{time_col}' se usará como texto (no se pudo convertir a fecha).")

        # --- 2. LIMPIEZA DE MÉTRICAS ---
        # Definimos las columnas que queremos ver (ignorando los ratios)
        cols_metrics = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
        
        # Verificamos cuáles existen realmente en el archivo
        available_metrics = [c for c in cols_metrics if c in df.columns]
        
        if not available_metrics:
            st.error(f"❌ No encuentro las columnas de datos: {cols_metrics}. Revisa tu CSV.")
            st.stop()

        # Limpiar números (quitar comas de miles si las hay)
        for col in available_metrics:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Asegurar que los filtros sean texto
        for col in ['agency', 'template', 'pid']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # --- 3. BARRA LATERAL CON FILTROS (Agency -> Template -> PID) ---
        st.sidebar.header("Filtros")

        # Filtro A: Agency
        if 'agency' in df.columns:
            all_agencies = sorted(df['agency'].unique())
            sel_agency = st.sidebar.multiselect("Agency", all_agencies)
        else:
            sel_agency = []
            st.sidebar.warning("No encontré la columna 'agency'")

        # Filtro B: Template (Dinámico)
        if 'template' in df.columns:
            # Si hay agencia seleccionada, mostramos solo sus templates
            if sel_agency:
                df_filtered_step1 = df[df['agency'].isin(sel_agency)]
                opts_templ = sorted(df_filtered_step1['template'].unique())
            else:
                opts_templ = sorted(df['template'].unique())
                
            sel_template = st.sidebar.multiselect("Template", opts_templ)
        else:
            sel_template = []

        # Filtro C: PID (Dinámico)
        if 'pid' in df.columns:
            # Filtramos PID basado en lo anterior
            df_step2 = df.copy()
            if sel_agency:
                df_step2 = df_step2[df_step2['agency'].isin(sel_agency)]
            if sel_template:
                df_step2 = df_step2[df_step2['template'].isin(sel_template)]
                
            opts_pid = sorted(df_step2['pid'].unique())
            sel_pid = st.sidebar.multiselect("PID", opts_pid)
        else:
            sel_pid = []

        # --- APLICAR TODOS LOS FILTROS ---
        df_final = df.copy()
        if sel_agency: df_final = df_final[df_final['agency'].isin(sel_agency)]
        if sel_template: df_final = df_final[df_final['template'].isin(sel_template)]
        if sel_pid: df_final = df_final[df_final['pid'].isin(sel_pid)]

        # --- 4. GRÁFICA Y DATOS ---
        st.markdown("---")
        
        if not df_final.empty:
            # Agrupar datos por la fecha seleccionada
            df_chart = df_final.groupby(time_col)[available_metrics].sum().reset_index()

            st.markdown(f"### 📈 Evolución: {len(df_final)} registros filtrados")

            col_izq, col_der = st.columns([1, 4])
            
            with col_izq:
                st.markdown("**Elige Métricas:**")
                metrics_to_plot = st.multiselect(
                    "Mostrar en gráfica:",
                    options=available_metrics,
                    default=available_metrics[:1] # Marca la primera por defecto
                )

            with col_der:
                if metrics_to_plot:
                    fig = px.line(
                        df_chart, 
                        x=time_col, 
                        y=metrics_to_plot, 
                        markers=True,
                        title="Tráfico en el tiempo",
                        labels={'value': 'Total Eventos', time_col: 'Fecha/Hora', 'variable': 'Métrica'}
                    )
                    fig.update_layout(hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Selecciona una métrica a la izquierda para ver la gráfica.")

            # KPI Resumen
            kpi_cols = st.columns(len(available_metrics))
            for i, metric in enumerate(available_metrics):
                val = df_final[metric].sum()
                kpi_cols[i].metric(label=f"Total {metric}", value=f"{int(val):,}")

            # Tabla
            with st.expander("Ver Tabla de Datos Filtrados"):
                st.dataframe(df_final)
        else:
            st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")

else:
    st.info("👆 Sube tu CSV único con columnas: agency, template, pid y una fecha/hora.")
