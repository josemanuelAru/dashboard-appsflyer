import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Comparador Avanzado (PID)", layout="wide")

st.title("⚔️ Comparador Detallado: Maquinillo vs Ivane")
st.markdown("Analiza discrepancias filtrando por PID específico.")

# --- 1. ZONA DE CARGA ---
col_up1, col_up2 = st.columns(2)

with col_up1:
    st.subheader("📂 1. Datos del Maquinillo")
    file_maq = st.file_uploader("Sube CSV Maquinillo", type=["csv"], key="maq")

with col_up2:
    st.subheader("📂 2. Datos de Ivane")
    file_ivane = st.file_uploader("Sube CSV Ivane", type=["csv"], key="ivane")

# --- LÓGICA DE PROCESAMIENTO ---
if file_maq and file_ivane:
    try:
        # Cargar archivos
        df_m = pd.read_csv(file_maq)
        df_i = pd.read_csv(file_ivane)
        
        # Limpieza básica de nombres de columnas
        df_m.columns = df_m.columns.str.strip()
        df_i.columns = df_i.columns.str.strip()

        st.success(f"✅ Archivos cargados.")
        st.markdown("---")

        # --- 2. MAPEO DE COLUMNAS (FECHA Y PID) ---
        st.subheader("⚙️ Configuración de Columnas")
        st.info("Indica qué columnas usar para Fecha (eje X) y PID (para filtrar).")

        c1, c2 = st.columns(2)
        
        # Función auxiliar para buscar columnas por nombre
        def find_col(df, keywords):
            found = [c for c in df.columns if any(k in c.lower() for k in keywords)]
            return df.columns.get_loc(found[0]) if found else 0

        with c1:
            st.markdown("**Maquinillo**")
            date_col_m = st.selectbox("Columna Fecha:", df_m.columns, index=find_col(df_m, ['date', 'fecha', 'time']), key="dm")
            pid_col_m = st.selectbox("Columna PID:", df_m.columns, index=find_col(df_m, ['pid', 'pub', 'id']), key="pm")
        
        with c2:
            st.markdown("**Ivane**")
            date_col_i = st.selectbox("Columna Fecha:", df_i.columns, index=find_col(df_i, ['date', 'fecha', 'time']), key="di")
            pid_col_i = st.selectbox("Columna PID:", df_i.columns, index=find_col(df_i, ['pid', 'pub', 'site', 'source']), key="pi")

        # --- 3. FILTRO DE PID (NUEVO) ---
        st.markdown("---")
        st.subheader("🔍 Filtro por PID")
        
        # Convertir a string para asegurar comparación
        df_m[pid_col_m] = df_m[pid_col_m].astype(str)
        df_i[pid_col_i] = df_i[pid_col_i].astype(str)

        # Obtener lista única de PIDs de ambos archivos
        pids_maq = set(df_m[pid_col_m].unique())
        pids_ivane = set(df_i[pid_col_i].unique())
        
        # Unión de todos los PIDs disponibles
        all_pids = sorted(list(pids_maq.union(pids_ivane)))
        
        # Encontrar PIDs comunes (para sugerir)
        common_pids = sorted(list(pids_maq.intersection(pids_ivane)))
        
        st.write(f"Detectados {len(all_pids)} PIDs totales. ({len(common_pids)} coinciden en ambos archivos).")

        selected_pids = st.multiselect(
            "Selecciona el PID que quieres analizar (Déjalo vacío para ver TODO):",
            options=all_pids,
            default=None
        )

        # --- APLICAR FILTRO ---
        if selected_pids:
            # Filtrar Dataframes ORIGINALES
            df_m_filtered = df_m[df_m[pid_col_m].isin(selected_pids)].copy()
            df_i_filtered = df_i[df_i[pid_col_i].isin(selected_pids)].copy()
            st.caption(f"Filtrando: Maquinillo ({len(df_m_filtered)} filas) | Ivane ({len(df_i_filtered)} filas)")
        else:
            df_m_filtered = df_m.copy()
            df_i_filtered = df_i.copy()

        # --- 4. PREPARACIÓN DE MÉTRICAS (Igual que antes pero con datos filtrados) ---
        
        # Limpiador de números
        def clean_number(x):
            if isinstance(x, str):
                return float(x.replace(',', '').replace(' ', ''))
            return float(x) if x else 0.0

        metrics_maq = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
        metrics_ivane = ['Aftrad IMPs', 'AF Blocked IMPs']

        # Maquinillo Processing
        df_m_filtered[date_col_m] = pd.to_datetime(df_m_filtered[date_col_m], errors='coerce').dt.date
        cols_found_m = []
        for metric in metrics_maq:
            match = next((c for c in df_m_filtered.columns if c.lower() == metric.lower()), None)
            if match:
                df_m_filtered[match] = df_m_filtered[match].apply(clean_number)
                cols_found_m.append(match)

        if cols_found_m:
            df_m_grouped = df_m_filtered.groupby(date_col_m)[cols_found_m].sum().reset_index()
            df_m_grouped = df_m_grouped.rename(columns={date_col_m: 'Fecha'})

        # Ivane Processing
        df_i_filtered[date_col_i] = pd.to_datetime(df_i_filtered[date_col_i], errors='coerce').dt.date
        cols_found_i = []
        for metric in metrics_ivane:
            match = next((c for c in df_i_filtered.columns if c.lower() == metric.lower()), None)
            if match:
                df_i_filtered[match] = df_i_filtered[match].apply(clean_number)
                cols_found_i.append(match)

        if cols_found_i:
            df_i_grouped = df_i_filtered.groupby(date_col_i)[cols_found_i].sum().reset_index()
            df_i_grouped = df_i_grouped.rename(columns={date_col_i: 'Fecha'})

        # --- 5. MERGE Y GRÁFICA ---
        if cols_found_m and cols_found_i:
            # Unir datos ya filtrados y agrupados
            df_final = pd.merge(df_m_grouped, df_i_grouped, on='Fecha', how='outer').sort_values('Fecha').fillna(0)

            st.markdown("### 📈 Visualización")
            
            all_metrics = cols_found_m + cols_found_i
            
            # Selector de métricas visuales
            metrics_to_plot = st.multiselect(
                "Métricas a graficar:",
                options=all_metrics,
                default=all_metrics
            )

            if metrics_to_plot:
                title_chart = f"Análisis: {', '.join(selected_pids)}" if selected_pids else "Análisis Global"
                
                fig = px.line(
                    df_final,
                    x='Fecha',
                    y=metrics_to_plot,
                    markers=True,
                    title=title_chart,
                    labels={'value': 'Eventos', 'variable': 'Métrica'}
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Ver Datos Numéricos"):
                    st.dataframe(df_final)
            else:
                st.info("Selecciona métricas.")
        else:
            st.error("Faltan métricas clave en los archivos.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Carga ambos archivos para empezar.")
