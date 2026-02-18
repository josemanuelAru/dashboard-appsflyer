import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Global", layout="wide")

st.title("📊 Dashboard Integral: Maquinillo vs Ivane")
st.markdown("Carga tus archivos en el menú lateral para activar los análisis.")

# ==========================================
# BARRA LATERAL (CARGA DE DATOS COMÚN)
# ==========================================
st.sidebar.header("📂 Carga de Archivos")

file_maq = st.sidebar.file_uploader("1. CSV Maquinillo", type=["csv"], key="u_maq_side")
file_ivane = st.sidebar.file_uploader("2. CSV Ivane", type=["csv"], key="u_ivane_side")

# Función auxiliar para limpiar números
def clean_numeric_col(series):
    if series.dtype == object:
        return pd.to_numeric(series.astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0)
    return series.fillna(0)

# ==========================================
# PESTAÑAS
# ==========================================
tab_maq, tab_ivane, tab_compare = st.tabs(["🤖 Análisis Maquinillo", "📋 Análisis Ivane", "⚔️ Comparativa Global"])

# ==========================================
# PESTAÑA 1: MAQUINILLO
# ==========================================
with tab_maq:
    if file_maq:
        try:
            # Rebobinar archivo por si acaso
            file_maq.seek(0)
            df_m = pd.read_csv(file_maq)
            df_m.columns = df_m.columns.str.lower().str.strip()
            
            st.markdown("### Configuración Maquinillo")
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
            st.markdown("#### 🔍 Filtros")
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

            # Aplicar Filtros
            df_m_filt = df_m.copy()
            if sel_ag: df_m_filt = df_m_filt[df_m_filt['agency'].isin(sel_ag)]
            if sel_tp: df_m_filt = df_m_filt[df_m_filt['template'].isin(sel_tp)]
            if sel_pid: df_m_filt = df_m_filt[df_m_filt['pid'].isin(sel_pid)]

            # Métricas y Gráfica
            metrics_m = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
            avail_m = [c for c in metrics_m if c in df_m_filt.columns]
            
            # Limpiar métricas
            for col in avail_m:
                df_m_filt[col] = clean_numeric_col(df_m_filt[col])

            st.markdown("---")
            if avail_m:
                df_chart = df_m_filt.groupby(col_date_m)[avail_m].sum().reset_index()
                st.plotly_chart(px.line(df_chart, x=col_date_m, y=avail_m, title="Evolución Maquinillo"), use_container_width=True)
            
            with st.expander("Ver Tabla de Datos"):
                st.dataframe(df_m_filt)

        except Exception as e:
            st.error(f"Error procesando Maquinillo: {e}")
    else:
        st.info("👈 Sube el CSV del Maquinillo en la barra lateral.")

# ==========================================
# PESTAÑA 2: IVANE
# ==========================================
with tab_ivane:
    if file_ivane:
        try:
            file_ivane.seek(0)
            df_i = pd.read_csv(file_ivane)
            df_i.columns = df_i.columns.str.strip() # Respetamos mayúsculas originales pero quitamos espacios
            cols_i = df_i.columns.tolist()

            st.markdown("### Configuración Ivane")
            # Mapeo de columnas
            c_d, c_m1, c_m2, c_m3 = st.columns(4)
            
            def find_idx(keywords):
                for i, col in enumerate(cols_i):
                    if any(k in col.lower() for k in keywords): return i
                return 0

            col_date_i = c_d.selectbox("Col. Fecha:", cols_i, index=find_idx(['date', 'fecha']), key="d_i")
            col_imps = c_m1.selectbox("Col. Aftrad IMPs:", cols_i, index=find_idx(['aftrad imps', 'imps']), key="c_imps")
            col_blocked = c_m2.selectbox("Col. Blocked IMPs:", cols_i, index=find_idx(['blocked imps', 'blocked']), key="c_block")
            col_pct = c_m3.selectbox("Col. Blocked %:", cols_i, index=find_idx(['%', 'rate']), key="c_pct")
            
            # Columnas filtro
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            col_pid = c_f1.selectbox("PID", cols_i, index=find_idx(['pid', 'site']), key="cp_i")
            col_app = c_f2.selectbox("APP ID", cols_i, index=find_idx(['app', 'bundle']), key="ca_i")
            col_adv = c_f3.selectbox("ADV", cols_i, index=find_idx(['adv']), key="cv_i")
            col_agy = c_f4.selectbox("Agency", cols_i, index=find_idx(['agency', 'partner']), key="cg_i")

            # Procesamiento Fecha y Números
            try:
                df_i[col_date_i] = pd.to_datetime(df_i[col_date_i], errors='coerce').dt.date
                df_i = df_i.sort_values(col_date_i)
            except:
                pass
            
            for c in [col_imps, col_blocked, col_pct]:
                df_i[c] = clean_numeric_col(df_i[c])

            # Filtros
            st.markdown("#### 🔍 Filtros")
            f1, f2, f3, f4 = st.columns(4)
            sel_pid_i = f1.multiselect("PID", sorted(df_i[col_pid].astype(str).unique()), key="fp_i")
            sel_app_i = f2.multiselect("APP ID", sorted(df_i[col_app].astype(str).unique()), key="fa_i")
            sel_adv_i = f3.multiselect("ADV", sorted(df_i[col_adv].astype(str).unique()), key="fv_i")
            sel_agy_i = f4.multiselect("Agency", sorted(df_i[col_agy].astype(str).unique()), key="fg_i")

            # Aplicar Filtros
            df_i_filt = df_i.copy()
            if sel_pid_i: df_i_filt = df_i_filt[df_i_filt[col_pid].astype(str).isin(sel_pid_i)]
            if sel_app_i: df_i_filt = df_i_filt[df_i_filt[col_app].astype(str).isin(sel_app_i)]
            if sel_adv_i: df_i_filt = df_i_filt[df_i_filt[col_adv].astype(str).isin(sel_adv_i)]
            if sel_agy_i: df_i_filt = df_i_filt[df_i_filt[col_agy].astype(str).isin(sel_agy_i)]

            # Gráfica
            st.markdown("---")
            df_chart_i = df_i_filt.groupby(col_date_i)[[col_imps, col_blocked]].sum().reset_index()
            if not df_chart_i.empty:
                st.plotly_chart(px.line(df_chart_i, x=col_date_i, y=[col_imps, col_blocked], title="Evolución Ivane"), use_container_width=True)

            # Tabla
            st.markdown("##### Tabla Detallada")
            df_table_i = df_i_filt.groupby([col_date_i, col_pid, col_app, col_adv, col_agy]).agg({
                col_imps: 'sum', col_blocked: 'sum', col_pct: 'mean'
            }).reset_index().sort_values(col_date_i, ascending=False)
            st.dataframe(df_table_i, use_container_width=True)

        except Exception as e:
            st.error(f"Error procesando Ivane: {e}")
    else:
        st.info("👈 Sube el CSV de Ivane en la barra lateral.")

# ==========================================
# PESTAÑA 3: COMPARATIVA (NUEVA)
# ==========================================
with tab_compare:
    st.header("⚔️ Comparativa Global (Maquinillo + Ivane)")
    
    if file_maq and file_ivane:
        try:
            st.info("Esta sección combina los datos de ambos archivos por FECHA.")
            
            # --- 1. RE-LEER Y PREPARAR MAQUINILLO ---
            # Necesitamos re-leer para tener una copia limpia sin filtrar
            file_maq.seek(0)
            df_m_comp = pd.read_csv(file_maq)
            df_m_comp.columns = df_m_comp.columns.str.lower().str.strip()
            
            # Usamos la misma columna de fecha detectada/seleccionada en la Pestaña 1
            # Para simplificar, pedimos confirmar si no está claro, pero intentaremos automatizar
            cols_mc = df_m_comp.columns.tolist()
            # Mapeo Métricas Maquinillo
            col_ok_m = next((c for c in cols_mc if 'ok_count' in c), 'cloudfront_ok_count')
            col_err_m = next((c for c in cols_mc if 'error_count' in c), 'cloudfront_error_count')
            col_pace_m = next((c for c in cols_mc if 'paced_count' in c), 'paced_count')
            
            # Buscar fecha
            idx_dm = next((i for i, c in enumerate(cols_mc) if any(x in c for x in ['date', 'fecha', 'time'])), 0)
            c_dm_sel = st.selectbox("Fecha Maquinillo:", cols_mc, index=idx_dm, key="comp_dm")
            
            # Limpiar y Agrupar Maquinillo
            df_m_comp[c_dm_sel] = pd.to_datetime(df_m_comp[c_dm_sel], errors='coerce').dt.date
            for c in [col_ok_m, col_err_m, col_pace_m]:
                if c in df_m_comp.columns:
                    df_m_comp[c] = clean_numeric_col(df_m_comp[c])
            
            # Agrupado por día
            metrics_m_list = [c for c in [col_ok_m, col_err_m, col_pace_m] if c in df_m_comp.columns]
            df_m_grouped = df_m_comp.groupby(c_dm_sel)[metrics_m_list].sum().reset_index()
            df_m_grouped.rename(columns={c_dm_sel: 'Fecha'}, inplace=True)


            # --- 2. RE-LEER Y PREPARAR IVANE ---
            file_ivane.seek(0)
            df_i_comp = pd.read_csv(file_ivane)
            df_i_comp.columns = df_i_comp.columns.str.strip()
            cols_ic = df_i_comp.columns.tolist()
            
            # Mapeo Métricas Ivane
            def find_i(k): return next((c for c in cols_ic if k in c.lower()), cols_ic[0])
            c_imps_i = find_i('aftrad imps')
            c_block_i = find_i('blocked imps') # O 'blocked'
            
            # Buscar fecha
            idx_di = next((i for i, c in enumerate(cols_ic) if any(x in c.lower() for x in ['date', 'fecha', 'time'])), 0)
            c_di_sel = st.selectbox("Fecha Ivane:", cols_ic, index=idx_di, key="comp_di")
            
            # Limpiar y Agrupar Ivane
            df_i_comp[c_di_sel] = pd.to_datetime(df_i_comp[c_di_sel], errors='coerce').dt.date
            for c in [c_imps_i, c_block_i]:
                df_i_comp[c] = clean_numeric_col(df_i_comp[c])
                
            metrics_i_list = [c_imps_i, c_block_i]
            df_i_grouped = df_i_comp.groupby(c_di_sel)[metrics_i_list].sum().reset_index()
            df_i_grouped.rename(columns={c_di_sel: 'Fecha'}, inplace=True)


            # --- 3. MERGE Y GRÁFICA FINAL ---
            st.markdown("---")
            
            # Unir las dos tablas por Fecha
            df_final = pd.merge(df_m_grouped, df_i_grouped, on='Fecha', how='outer').sort_values('Fecha').fillna(0)
            
            # Lista de todas las métricas disponibles para graficar
            all_metrics = metrics_m_list + metrics_i_list
            
            st.subheader("📈 Gráfica Combinada de 5 Métricas")
            st.caption("Selecciona/Deselecciona las métricas haciendo clic en la leyenda de la gráfica.")
            
            fig_comp = px.line(
                df_final,
                x='Fecha',
                y=all_metrics,
                markers=True,
                title="Visión Global: Maquinillo vs Ivane",
                labels={'value': 'Cantidad', 'variable': 'Métrica'}
            )
            fig_comp.update_layout(hovermode="x unified")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            with st.expander("Ver Datos Consolidados"):
                st.dataframe(df_final)

        except Exception as e:
            st.error(f"Error en la comparativa: {e}")
            
    else:
        st.warning("⚠️ Para ver la comparativa, debes subir AMBOS archivos en la barra lateral.")
