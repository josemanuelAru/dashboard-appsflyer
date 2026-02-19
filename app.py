import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
ivane_col_imps = None
ivane_col_blocked = None

# ==========================================
# PESTAÑAS (Ahora son 4)
# ==========================================
tab_maq, tab_ivane, tab_compare, tab_match = st.tabs([
    "🤖 Análisis Maquinillo", 
    "📋 Análisis Ivane", 
    "⚖️ Comparativa (Filtrada)",
    "🔗 Cruce de Datos (Match)"
])

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
            cols_m = df_m.columns.tolist()
            idx_date = next((i for i, c in enumerate(cols_m) if any(x in c for x in ['date', 'fecha', 'time'])), 0)
            col_date_m = st.selectbox("Columna Fecha:", cols_m, index=idx_date, key="d_m")
            
            try:
                df_m[col_date_m] = pd.to_datetime(df_m[col_date_m])
                df_m = df_m.sort_values(col_date_m)
            except:
                st.warning("⚠️ Fecha no convertible. Se usará como texto.")

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

            df_m_filt = df_m.copy()
            if sel_ag: df_m_filt = df_m_filt[df_m_filt['agency'].isin(sel_ag)]
            if sel_tp: df_m_filt = df_m_filt[df_m_filt['template'].isin(sel_tp)]
            if sel_pid: df_m_filt = df_m_filt[df_m_filt['pid'].isin(sel_pid)]

            metrics_m = ['cloudfront_ok_count', 'cloudfront_error_count', 'http_error_count', 'paced_count']
            avail_m = [c for c in metrics_m if c in df_m_filt.columns]
            
            for col in avail_m:
                df_m_filt[col] = clean_numeric_col(df_m_filt[col])

            st.markdown("---")
            st.info(f"Mostrando datos filtrados: {len(df_m_filt)} registros.")
            
            if avail_m:
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
            c_m1, c_m2, c_m3 = st.columns(3)
            
            def find_idx(keywords):
                for i, col in enumerate(cols_i):
                    if any(k in col.lower() for k in keywords): return i
                return 0

            ivane_col_imps = c_m1.selectbox("Col. Aftrad IMPs:", cols_i, index=find_idx(['aftrad imps', 'imps']), key="c_imps")
            ivane_col_blocked = c_m2.selectbox("Col. Blocked IMPs:", cols_i, index=find_idx(['blocked imps', 'blocked']), key="c_block")
            col_pct = c_m3.selectbox("Col. Blocked %:", cols_i, index=find_idx(['%', 'rate']), key="c_pct")
            
            st.markdown("##### Columnas de Agrupación")
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            col_pid = c_f1.selectbox("PID", cols_i, index=find_idx(['pid', 'site']), key="cp_i")
            col_app = c_f2.selectbox("APP ID", cols_i, index=find_idx(['app', 'bundle']), key="ca_i")
            col_adv = c_f3.selectbox("ADV", cols_i, index=find_idx(['adv']), key="cv_i")
            col_agy = c_f4.selectbox("Agency", cols_i, index=find_idx(['agency', 'partner']), key="cg_i")

            for c in [ivane_col_imps, ivane_col_blocked, col_pct]:
                df_i[c] = clean_numeric_col(df_i[c])

            st.markdown("#### 🔍 Filtros Ivane")
            f1, f2, f3, f4 = st.columns(4)
            sel_pid_i = f1.multiselect("PID", sorted(df_i[col_pid].astype(str).unique()), key="fp_i")
            sel_app_i = f2.multiselect("APP ID", sorted(df_i[col_app].astype(str).unique()), key="fa_i")
            sel_adv_i = f3.multiselect("ADV", sorted(df_i[col_adv].astype(str).unique()), key="fv_i")
            sel_agy_i = f4.multiselect("Agency", sorted(df_i[col_agy].astype(str).unique()), key="fg_i")

            df_i_filt = df_i.copy()
            if sel_pid_i: df_i_filt = df_i_filt[df_i_filt[col_pid].astype(str).isin(sel_pid_i)]
            if sel_app_i: df_i_filt = df_i_filt[df_i_filt[col_app].astype(str).isin(sel_app_i)]
            if sel_adv_i: df_i_filt = df_i_filt[df_i_filt[col_adv].astype(str).isin(sel_adv_i)]
            if sel_agy_i: df_i_filt = df_i_filt[df_i_filt[col_agy].astype(str).isin(sel_agy_i)]

            st.markdown("---")
            st.info(f"Mostrando datos filtrados: {len(df_i_filt)} registros.")

            st.subheader("Totales Generales (Filtrados)")
            k1, k2, k3 = st.columns(3)
            total_imps = df_i_filt[ivane_col_imps].sum()
            total_block = df_i_filt[ivane_col_blocked].sum()
            avg_pct = df_i_filt[col_pct].mean()

            k1.metric("Total Aftrad IMPs", f"{int(total_imps):,}")
            k2.metric("Total Blocked IMPs", f"{int(total_block):,}")
            k3.metric("Blocked % Promedio", f"{avg_pct:.2f}%")

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
    
    has_maq_data = df_m_filt is not None and not df_m_filt.empty
    has_ivane_data = df_i_filt is not None and not df_i_filt.empty
    
    if has_maq_data and has_ivane_data:
        try:
            st.success("✅ Usando los datos filtrados de las pestañas anteriores.")
            
            m_ok = df_m_filt['cloudfront_ok_count'].sum() if 'cloudfront_ok_count' in df_m_filt.columns else 0
            m_err_cf = df_m_filt['cloudfront_error_count'].sum() if 'cloudfront_error_count' in df_m_filt.columns else 0
            m_err_http = df_m_filt['http_error_count'].sum() if 'http_error_count' in df_m_filt.columns else 0
            m_pace = df_m_filt['paced_count'].sum() if 'paced_count' in df_m_filt.columns else 0

            i_imps = df_i_filt[ivane_col_imps].sum() if ivane_col_imps else 0
            i_block = df_i_filt[ivane_col_blocked].sum() if ivane_col_blocked else 0
            
            data_comp = {
                'Métrica': [
                    'Maquinillo: OK Count', 
                    'Maquinillo: CF Error Count', 
                    'Maquinillo: HTTP Error Count', 
                    'Maquinillo: Paced Count', 
                    'Ivane: Aftrad IMPs', 
                    'Ivane: Blocked IMPs'
                ],
                'Total (Filtrado)': [m_ok, m_err_cf, m_err_http, m_pace, i_imps, i_block],
                'Fuente': ['Maquinillo', 'Maquinillo', 'Maquinillo', 'Maquinillo', 'Ivane', 'Ivane']
            }
            
            df_comp_viz = pd.DataFrame(data_comp)

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

            st.subheader("📋 Tabla de Datos Consolidados")
            st.dataframe(df_comp_viz, use_container_width=True)

        except Exception as e:
            st.error(f"Error en la comparativa: {e}")
    else:
        st.warning("⚠️ Esperando datos... Asegúrate de subir archivos y de que los filtros seleccionados no dejen los datos vacíos.")

# ==========================================
# PESTAÑA 4: CRUCE DE DATOS (MATCH EXACTO)
# ==========================================
with tab_match:
    st.header("🔗 Cruce de Datos (Maquinillo 🤝 Ivane)")
    st.markdown("Esta tabla une los registros donde **Agency, Template/App ID y PID coinciden exactamente** en ambos archivos.")

    if file_maq and file_ivane:
        try:
            # 1. Leer archivos crudos de nuevo
            file_maq.seek(0)
            df_m_match = pd.read_csv(file_maq)
            df_m_match.columns = df_m_match.columns.str.lower().str.strip()
            
            file_ivane.seek(0)
            df_i_match = pd.read_csv(file_ivane)
            df_i_match.columns = df_i_match.columns.str.strip()
            cols_im = df_i_match.columns.tolist()

            # 2. Mapeos Seguros para el cruce
            def find_col(keywords):
                for col in cols_im:
                    if any(k in col.lower() for k in keywords): return col
                return cols_im[0]

            i_col_pid = find_col(['pid', 'site'])
            i_col_app = find_col(['app', 'bundle'])
            i_col_agy = find_col(['agency', 'partner'])
            i_col_imps = find_col(['aftrad imps', 'imps'])
            i_col_block = find_col(['blocked imps', 'blocked'])

            # 3. Métricas Maquinillo a cruzar
            m_metrics = ['cloudfront_ok_count', 'cloudfront_error_count', 'http_error_count', 'paced_count']
            avail_m_metrics = [c for c in m_metrics if c in df_m_match.columns]
            
            # Limpieza numérica
            for c in avail_m_metrics: df_m_match[c] = clean_numeric_col(df_m_match[c])
            for c in [i_col_imps, i_col_block]: df_i_match[c] = clean_numeric_col(df_i_match[c])

            # 4. Agrupar, Renombrar Llaves y Estandarizar a Minúsculas
            map_m = {}
            if 'agency' in df_m_match.columns: map_m['agency'] = 'Match_Agency'
            if 'template' in df_m_match.columns: map_m['template'] = 'Match_App'
            if 'pid' in df_m_match.columns: map_m['pid'] = 'Match_PID'
            
            map_i = {
                i_col_agy: 'Match_Agency',
                i_col_app: 'Match_App',
                i_col_pid: 'Match_PID'
            }

            # Agrupamos Maquinillo
            df_m_g = df_m_match.groupby(list(map_m.keys()))[avail_m_metrics].sum().reset_index()
            df_m_g = df_m_g.rename(columns=map_m)

            # Filtramos map_i para solo cruzar las llaves que sí existen en Maquinillo
            keys_to_merge = list(map_m.values())
            map_i_filtered = {k: v for k, v in map_i.items() if v in keys_to_merge}
            
            # Agrupamos Ivane
            df_i_g = df_i_match.groupby(list(map_i_filtered.keys()))[[i_col_imps, i_col_block]].sum().reset_index()
            df_i_g = df_i_g.rename(columns=map_i_filtered)

            # Estandarizar a minúsculas para cruce perfecto
            for c in keys_to_merge:
                df_m_g[c] = df_m_g[c].astype(str).str.lower().str.strip()
                df_i_g[c] = df_i_g[c].astype(str).str.lower().str.strip()

            # 5. MERGE (CRUCE)
            df_merged = pd.merge(df_m_g, df_i_g, on=keys_to_merge, how='inner')

            # Renombrar columnas llaves al formato final
            rename_final = {
                'Match_Agency': 'Agency',
                'Match_App': 'App ID / Template',
                'Match_PID': 'PID'
            }
            df_merged = df_merged.rename(columns=rename_final)

            # 6. FILTROS EXCLUSIVOS DE ESTA PESTAÑA
            st.markdown("#### 🔍 Filtrar Tabla Cruzada")
            f_m1, f_m2, f_m3 = st.columns(3)

            sel_ag_match, sel_app_match, sel_pid_match = [], [], []

            if 'Agency' in df_merged.columns:
                opts_ag_match = sorted(df_merged['Agency'].unique())
                sel_ag_match = f_m1.multiselect("Filtrar Agency", opts_ag_match, key="fm_ag")
            
            if 'App ID / Template' in df_merged.columns:
                opts_app_match = sorted(df_merged['App ID / Template'].unique())
                sel_app_match = f_m2.multiselect("Filtrar App ID", opts_app_match, key="fm_app")

            if 'PID' in df_merged.columns:
                opts_pid_match = sorted(df_merged['PID'].unique())
                sel_pid_match = f_m3.multiselect("Filtrar PID", opts_pid_match, key="fm_pid")

            # Aplicar filtros
            df_show = df_merged.copy()
            if sel_ag_match and 'Agency' in df_show.columns: 
                df_show = df_show[df_show['Agency'].isin(sel_ag_match)]
            if sel_app_match and 'App ID / Template' in df_show.columns: 
                df_show = df_show[df_show['App ID / Template'].isin(sel_app_match)]
            if sel_pid_match and 'PID' in df_show.columns: 
                df_show = df_show[df_show['PID'].isin(sel_pid_match)]

            # 7. CÁLCULO DEL PORCENTAJE
            col_pct_calc = '% Bloqueado' # <-- AQUÍ ESTÁ EL CAMBIO
            if 'cloudfront_ok_count' in df_show.columns and i_col_block in df_show.columns:
                # Calculamos el porcentaje dividiendo Blocked entre OK Count
                # Usamos fillna(0) y replace(inf) por si el OK Count es 0 (para evitar errores de división por cero)
                df_show[col_pct_calc] = (df_show[i_col_block] / df_show['cloudfront_ok_count'] * 100).fillna(0)
                df_show[col_pct_calc] = df_show[col_pct_calc].replace([np.inf, -np.inf], 0).round(2)

            # 8. MOSTRAR TABLA FINAL
            st.markdown(f"**Coincidencias exactas encontradas:** {len(df_show)} filas combinadas.")
            
            # Ordenamos las columnas para que salgan en el orden correcto
            keys_existentes = [c for c in ['Agency', 'App ID / Template', 'PID'] if c in df_show.columns]
            columnas_finales = keys_existentes + avail_m_metrics + [i_col_imps, i_col_block]
            
            # Añadimos la columna del porcentaje calculada si existen sus dependencias
            if 'cloudfront_ok_count' in df_show.columns and i_col_block in df_show.columns:
                columnas_finales.append(col_pct_calc)
                
            df_show = df_show[columnas_finales]

            st.dataframe(df_show, use_container_width=True)

        except Exception as e:
            st.error(f"Error realizando el cruce de datos: {e}")
    else:
        st.info("👈 Sube AMBOS archivos en la barra lateral para poder cruzarlos.")
