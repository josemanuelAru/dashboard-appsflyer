import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Global", layout="wide")

st.title("📊 Dashboard Integral: Maquinillo vs Ivane")
st.markdown("Carga tus archivos y aplica filtros en cada pestaña. La comparativa final respetará esos filtros.")

# ==========================================
# BARRA LATERAL (CARGA DE DATOS)
# ==========================================
st.sidebar.header("📂 Carga de Archivos")

file_maq = st.sidebar.file_uploader("1. CSV Maquinillo", type=["csv"], key="u_maq_side")
file_ivane = st.sidebar.file_uploader("2. CSV Ivane", type=["csv"], key="u_ivane_side")

# Función auxiliar para limpiar números
def clean_numeric_col(series):
    if series.dtype == object:
        return pd.to_numeric(series.astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0)
    return series.fillna(0)

# Inicializamos variables globales para compartir datos entre pestañas
df_m_filt = None
df_i_filt = None
# Variables para guardar los nombres de las columnas seleccionadas en Ivane
ivane_col_imps = None
ivane_col_blocked = None

# ==========================================
# PESTAÑAS
# ==========================================
tab_maq, tab_ivane, tab_compare = st.tabs(["🤖 Análisis Maquinillo", "📋 Análisis Ivane", "⚖️ Comparativa (Filtrada)"])

# ==========================================
# PESTAÑA 1: MAQUINILLO (CON FECHA)
# ==========================================
with tab_maq:
    if file_maq:
        try:
            file_maq.seek(0)
            df_m = pd.read_csv(file_maq)
            df_m.columns = df_m.columns.str.lower().str.strip()
            
            st.markdown("### 🗓️ Configuración Maquinillo")
            # Selección de Fecha
            cols_m = df_m.columns.tolist()
            idx_date = next((i for i, c in enumerate(cols_m) if any(x in c for x in ['date', 'fecha', 'time'])), 0)
            col_date_m = st.selectbox("Columna Fecha:", cols_m, index=idx_date, key="d_m")
            
            # Convertir Fecha
            try:
                df_m[col_date_m] = pd.to_datetime(df_m[col_date_m])
                df_m = df_m.sort_values(col_date_m)
            except:
                st.warning("⚠️ Fecha no convertible. Se usará como texto.")

            # Filtros
            st.markdown("#### 🔍 Filtros Maquinillo")
            c1, c2, c3 = st.columns(3)
            
            sel_ag = []
            if 'agency' in df_m.columns:
                sel_ag = c1.multiselect("Agency", sorted(df_m['agency'].astype(str).unique()), key="f_ag_m")
            
            sel_tp = []
            if 'template' in df_m.columns:
                opts = df_m[df_m['agency'].isin(sel_ag)]['template'].unique() if sel_ag else df_m['template'].unique()
                sel_tp = c2.multiselect("Template", sorted(opts.astype(str)), key="f_tp_m")

            sel_pid = []
            if 'pid' in df_m.columns:
                temp = df_m.copy()
                if sel_ag: temp = temp[temp['agency'].isin(sel_ag)]
                if sel_tp: temp = temp[temp['template'].isin(sel_tp)]
                sel_pid = c3.multiselect("PID", sorted(temp['pid'].astype(str).unique()), key="f_pid_m")

            # Aplicar Filtros (Guardamos en df_m_filt para usarlo luego)
            df_m_filt = df_m.copy()
            if sel_ag: df_m_filt = df_m_filt[df_m_filt['agency'].isin(sel_ag)]
            if sel_tp: df_m_filt = df_m_filt[df_m_filt['template'].isin(sel_tp)]
            if sel_pid: df_m_filt = df_m_filt[df_m_filt['pid'].isin(sel_pid)]

            # Métricas y Gráfica (Añadido http_error_count)
            metrics_m = ['cloudfront_ok_count', 'cloudfront_error_count', 'http_error_count', 'paced_count']
            avail_m = [c for c in metrics_m if c in df_m_filt.columns]
            
            # Limpiar métricas
            for col in avail_m:
                df_m_filt[col] = clean_numeric_col(df_m_filt[col])

            st.markdown("---")
            st.info(f"Mostrando datos filtrados: {len(df_m_filt)} registros.")
            
            if avail_m:
                # Gráfica Temporal
                df_chart = df_m_filt.groupby(col_date_m)[avail_m].sum().reset_index()
                st.plotly_chart(px.line(df_chart, x=col_date_m, y=avail_m, title="Evolución Temporal Maquinillo"), use_container_width=True)
            
            with st.expander("Ver Tabla de Datos Maquinillo"):
                st.dataframe(df_m_filt)

        except Exception as e:
            st.error(f"Error procesando Maquinillo: {e}")
    else:
        st.info("👈 Sube el CSV del Maquinillo en la barra lateral.")

# ==========================================
# PESTAÑA 2: IVANE (SIN FECHA - SOLO TOTALES)
# ==========================================
with tab_ivane:
    if file_ivane:
        try:
            file_ivane.seek(0)
            df_i = pd.read_csv(file_ivane)
            df_i.columns = df_i.columns.str.strip()
            cols_i = df_i.columns.tolist()

            st.markdown("### 🔢 Configuración Ivane")
            
            # Mapeo de columnas
            c_m1, c_m2, c_m3 = st.columns(3)
            
            def find_idx(keywords):
                for i, col in enumerate(cols_i):
                    if any(k in col.lower() for k in keywords): return i
                return 0

            # Guardamos los nombres de las columnas en variables globales
            ivane_col_imps = c_m1.selectbox("Col. Aftrad IMPs:", cols_i, index=find_idx(['aftrad imps', 'imps']), key="c_imps")
            ivane_col_blocked = c_m2.selectbox("Col. Blocked IMPs:", cols_i, index=find_idx(['blocked imps', 'blocked']), key="c_block")
            col_pct = c_m3.selectbox("Col. Blocked %:", cols_i, index=find_idx(['%', 'rate']), key="c_pct")
            
            # Columnas filtro
            st.markdown("##### Columnas de Agrupación")
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            col_pid = c_f1.selectbox("PID", cols_i, index=find_idx(['pid', 'site']), key="cp_i")
            col_app = c_f2.selectbox("APP ID", cols_i, index=find_idx(['app', 'bundle']), key="ca_i")
            col_adv = c_f3.selectbox("ADV", cols_i, index=find_idx(['adv']), key="cv_i")
            col_agy = c_f4.selectbox("Agency", cols_i, index=find_idx(['agency', 'partner']), key="cg_i")

            # Procesamiento Números
            for c in [ivane_col_imps, ivane_col_blocked, col_pct]:
                df_i[c] = clean_numeric_col(df_i[c])

            # Filtros
            st.markdown("#### 🔍 Filtros Ivane")
            f1, f2, f3, f4 = st.columns(4)
            sel_pid_i = f1.multiselect("PID", sorted(df_i[col_pid].astype(str).unique()), key="fp_i")
            sel_app_i = f2.multiselect("APP ID", sorted(df_i[col_app].astype(str).unique()), key="fa_i")
            sel_adv_i = f3.multiselect("ADV", sorted(df_i[col_adv].astype(str).unique()), key="fv_i")
            sel_agy_i = f4.multiselect("Agency", sorted(df_i[col_agy].astype(str).unique()), key="fg_i")

            # Aplicar Filtros (Guardamos en df_i_filt)
            df_i_filt = df_i.copy()
            if sel_pid_i: df_i_filt = df_i_filt[df_i_filt[col_pid].astype(str).isin(sel_pid_i)]
            if sel_app_i: df_i_filt = df_i_filt[df_i_filt[col_app].astype(str).isin(sel_app_i)]
            if sel_adv_i: df_i_filt = df_i_filt[df_i_filt[col_adv].astype(str).isin(sel_adv_i)]
            if sel_agy_i: df_i_filt = df_i_filt[df_i_filt[col_agy].astype(str).isin(sel_agy_i)]

            st.markdown("---")
            st.info(f"Mostrando datos filtrados: {len(df_i_filt)} registros.")

            # --- VISUALIZACIÓN DE TOTALES ---
            st.subheader("Totales Generales (Filtrados)")
            k1, k2, k3 = st.columns(3)
            total_imps = df_i_filt[ivane_col_imps].sum()
            total_block = df_i_filt[ivane_col_blocked].sum()
            avg_pct = df_i_filt[col_pct].mean()

            k1.metric("Total Aftrad IMPs", f"{int(total_imps):,}")
            k2.metric("Total Blocked IMPs", f"{int(total_block):,}")
            k3.metric("Blocked % Promedio", f"{avg_pct:.2f}%")

            # Tabla Detallada
            st.markdown("##### 📋 Tabla Detallada")
            group_cols = [col_pid, col_app, col_adv, col_agy]
            df_table_i = df_i_filt.groupby(group_cols).agg({
                ivane_col_imps: 'sum', 
                ivane_col_blocked: 'sum', 
                col_pct: 'mean'
            }).reset_index().sort_values(ivane_col_imps, ascending=False)
            
            st.dataframe(df_table_i, use_container_width=True)

        except Exception as e:
            st.error(f"Error procesando Ivane: {e}")
    else:
        st.info("👈 Sube el CSV de Ivane en la barra lateral.")

# ==========================================
# PESTAÑA 3: COMPARATIVA (USANDO FILTROS)
# ==========================================
with tab_compare:
    st.header("⚖️ Comparativa de Totales (Filtrada)")
    
    # Verificamos si los Dataframes filtrados existen y no están vacíos
    has_maq_data = df_m_filt is not None and not df_m_filt.empty
    has_ivane_data = df_i_filt is not None and not df_i_filt.empty
    
    if has_maq_data and has_ivane_data:
        try:
            st.success("✅ Usando los datos filtrados de las pestañas anteriores.")
            
            # --- DATOS MAQUINILLO (YA FILTRADOS) ---
            # Sumamos las columnas directamente del dataframe filtrado
            m_ok = df_m_filt['cloudfront_ok_count'].sum() if 'cloudfront_ok_count' in df_m_filt.columns else 0
            m_err_cf = df_m_filt['cloudfront_error_count'].sum() if 'cloudfront_error_count' in df_m_filt.columns else 0
            m_err_http = df_m_filt['http_error_count'].sum() if 'http_error_count' in df_m_filt.columns else 0
            m_pace = df_m_filt['paced_count'].sum() if 'paced_count' in df_m_filt.columns else 0

            # --- DATOS IVANE (YA FILTRADOS) ---
            # Usamos los nombres de columna que el usuario eligió en la pestaña 2
            i_imps = df_i_filt[ivane_col_imps].sum() if ivane_col_imps else 0
            i_block = df_i_filt[ivane_col_blocked].sum() if ivane_col_blocked else 0

            # --- VISUALIZACIÓN COMPARATIVA ---
            
            # Crear DataFrame Resumen
            data_comp = {
                'Métrica': [
                    'Maquinillo: OK Count', 
                    'Maquinillo: Cloudfront Error Count', 
                    'Maquinillo: HTTP Error Count', 
                    'Maquinillo: Paced Count', 
                    'Ivane: Aftrad IMPs', 
                    'Ivane: Blocked IMPs'
                ],
                'Total (Filtrado)': [m_ok, m_err_cf, m_err_http, m_pace, i_imps, i_block],
                'Fuente': ['Maquinillo', 'Maquinillo', 'Maquinillo', 'Maquinillo', 'Ivane', 'Ivane']
            }
            
            df_comp_viz = pd.DataFrame(data_comp)

            # Gráfica de Barras Comparativa
            st.subheader("📊 Gráfica de Volúmenes (Datos Filtrados)")
            fig_comp = px.bar(
                df_comp_viz, 
                x='Métrica', 
                y='Total (Filtrado)', 
                color='Fuente', 
                text_auto='.2s',
                title="Comparativa Final Respetando Filtros"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            # Tabla Resumen
            st.subheader("📋 Tabla de Datos Consolidados")
            st.dataframe(df_comp_viz, use_container_width=True)

        except Exception as e:
            st.error(f"Error en la comparativa: {e}")
            
    else:
        st.warning("⚠️ Esperando datos... Asegúrate de subir archivos y de que los filtros seleccionados no dejen los datos vacíos.")
        if not has_maq_data:
            st.caption("- Faltan datos de Maquinillo (revisa Pestaña 1).")
        if not has_ivane_data:
            st.caption("- Faltan datos de Ivane (revisa Pestaña 2).")
