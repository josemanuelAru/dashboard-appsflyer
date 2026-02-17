import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Maquinillo & Ivane", layout="wide")

st.title("📊 Dashboard: Maquinillo & Ivane")
st.markdown("Herramienta de análisis separada por fuente de datos.")

# Pestañas
tab_maq, tab_ivane = st.tabs(["🤖 Reporte Maquinillo", "📋 Reporte Ivane"])

# ==========================================
# PESTAÑA 1: MAQUINILLO
# ==========================================
with tab_maq:
    st.header("Análisis Maquinillo")
    file_maq = st.file_uploader("Sube CSV Maquinillo", type=["csv"], key="u_maq")

    if file_maq:
        try:
            # Carga
            df_m = pd.read_csv(file_maq)
            df_m.columns = df_m.columns.str.lower().str.strip()
            
            # Fecha
            col_date_m = st.selectbox("Columna Fecha (Maquinillo):", df_m.columns, key="date_m")
            try:
                df_m[col_date_m] = pd.to_datetime(df_m[col_date_m])
                df_m = df_m.sort_values(col_date_m)
            except:
                st.warning("⚠️ Fecha no convertible. Se usará como texto.")

            # Filtros Maquinillo (Agency, Template, PID)
            st.markdown("##### 🔍 Filtros")
            c1, c2, c3 = st.columns(3)
            
            # Filtros dinámicos básicos
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

            # Aplicar filtros
            df_m_filt = df_m.copy()
            if sel_ag: df_m_filt = df_m_filt[df_m_filt['agency'].isin(sel_ag)]
            if sel_tp: df_m_filt = df_m_filt[df_m_filt['template'].isin(sel_tp)]
            if sel_pid: df_m_filt = df_m_filt[df_m_filt['pid'].isin(sel_pid)]

            # Gráfica
            st.markdown("---")
            metrics_m = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
            avail_m = [c for c in metrics_m if c in df_m_filt.columns]
            
            if avail_m:
                df_chart = df_m_filt.groupby(col_date_m)[avail_m].sum().reset_index()
                st.plotly_chart(px.line(df_chart, x=col_date_m, y=avail_m, title="Evolución Maquinillo"), use_container_width=True)
            
            with st.expander("Ver Datos"):
                st.dataframe(df_m_filt)

        except Exception as e:
            st.error(f"Error Maquinillo: {e}")

# ==========================================
# PESTAÑA 2: IVANE (RENOVADA)
# ==========================================
with tab_ivane:
    st.header("Análisis Ivane")
    file_ivane = st.file_uploader("Sube CSV Ivane", type=["csv"], key="u_ivane")

    if file_ivane:
        try:
            # 1. Cargar y Limpiar
            df_i = pd.read_csv(file_ivane)
            # Guardamos nombres originales para mostrar, pero normalizamos para buscar
            df_i.columns = df_i.columns.str.strip() 
            
            st.success(f"Archivo cargado: {len(df_i)} filas.")

            # 2. Configuración de Columnas (Mapeo)
            st.subheader("⚙️ Configuración de Columnas")
            cols = df_i.columns.tolist()
            
            c_d, c_m1, c_m2 = st.columns(3)
            
            # Buscar columnas por defecto (inteligente)
            def find_idx(keywords):
                for i, col in enumerate(cols):
                    if any(k in col.lower() for k in keywords): return i
                return 0

            # Fecha
            idx_date = find_idx(['date', 'fecha', 'time', 'day'])
            col_date = c_d.selectbox("Columna Fecha:", cols, index=idx_date, key="date_i")
            
            # Métricas Objetivo (Aftrad IMPs y Blocked IMPs)
            idx_imps = find_idx(['aftrad imps', 'imps', 'impressions'])
            col_imps = c_m1.selectbox("Col. Aftrad IMPs:", cols, index=idx_imps, key="c_imps")
            
            idx_blocked = find_idx(['blocked', 'block', 'b. imps'])
            col_blocked = c_m2.selectbox("Col. AF Blocked IMPs:", cols, index=idx_blocked, key="c_block")

            # Columnas de Filtro (PID, APP ID, ADV, Agency)
            st.caption("Verifica las columnas de filtro:")
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            col_pid = c_f1.selectbox("Col. PID:", cols, index=find_idx(['pid', 'pub', 'site']), key="c_pid")
            col_app = c_f2.selectbox("Col. APP ID:", cols, index=find_idx(['app', 'bundle', 'package']), key="c_app")
            col_adv = c_f3.selectbox("Col. ADV:", cols, index=find_idx(['adv', 'advertiser']), key="c_adv")
            col_agency = c_f4.selectbox("Col. Agency:", cols, index=find_idx(['agency', 'partner', 'network']), key="c_agy")

            # Procesar Fecha
            try:
                df_i[col_date] = pd.to_datetime(df_i[col_date], errors='coerce').dt.date
                df_i = df_i.sort_values(col_date)
            except:
                st.warning("⚠️ Fecha tratada como texto.")

            # Procesar Métricas (Limpiar números)
            for col in [col_imps, col_blocked]:
                if df_i[col].dtype == object:
                    df_i[col] = pd.to_numeric(df_i[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

            # --- 3. FILTROS ---
            st.markdown("---")
            st.subheader("🔍 Filtros")
            
            f1, f2, f3, f4 = st.columns(4)
            
            # Filtros independientes (para que sea fácil de usar)
            # PID
            opts_pid = sorted(df_i[col_pid].astype(str).unique())
            sel_pid = f1.multiselect("Filtrar PID", opts_pid, key="f_pid")
            
            # APP ID
            opts_app = sorted(df_i[col_app].astype(str).unique())
            sel_app = f2.multiselect("Filtrar APP ID", opts_app, key="f_app")
            
            # ADV
            opts_adv = sorted(df_i[col_adv].astype(str).unique())
            sel_adv = f3.multiselect("Filtrar ADV", opts_adv, key="f_adv")
            
            # Agency
            opts_agy = sorted(df_i[col_agency].astype(str).unique())
            sel_agy = f4.multiselect("Filtrar Agency", opts_agy, key="f_agy")

            # Aplicar Filtros
            df_final = df_i.copy()
            if sel_pid: df_final = df_
