import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Dashboard Global", layout="wide")

st.title("📊 Dashboard Integral: Maquinillo vs Ivane")
st.markdown("Analiza y compara los datos que coinciden exactamente entre ambas plataformas.")

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

# Variables globales para compartir entre pestañas
df_show = None
avail_m_metrics = []
i_col_imps = None
i_col_block = None

# ==========================================
# PESTAÑAS
# ==========================================
tab_match, tab_compare = st.tabs([
    "🔗 Cruce de Datos (Match)", 
    "⚖️ Comparativa (Filtrada)"
])

# ==========================================
# PESTAÑA 1: CRUCE DE DATOS (MATCH EXACTO)
# ==========================================
with tab_match:
    st.header("🔗 Cruce de Datos (Maquinillo 🤝 Ivane)")
    st.markdown("Esta tabla une los registros donde **Agency, Template/App ID y PID coinciden exactamente** en ambos archivos.")

    if file_maq and file_ivane:
        try:
            # 1. Leer archivos crudos
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
            i_col_adv = find_col(['adv', 'advertiser'])
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
            
            # Agrupamos Ivane (Añadiendo ADV a la agrupación para no perderlo)
            keys_i_group = list(map_i_filtered.keys())
            if i_col_adv not in keys_i_group:
                keys_i_group.append(i_col_adv)
                
            df_i_g = df_i_match.groupby(keys_i_group)[[i_col_imps, i_col_block]].sum().reset_index()
            df_i_g = df_i_g.rename(columns=map_i_filtered)
            df_i_g = df_i_g.rename(columns={i_col_adv: 'ADV'}) # Renombramos la columna a 'ADV'

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

            # 6. FILTROS EXCLUSIVOS
            st.markdown("#### 🔍 Filtrar Datos")
            f_m1, f_m2, f_m3, f_m4 = st.columns(4)

            sel_adv_match, sel_ag_match, sel_app_match, sel_pid_match = [], [], [], []

            if 'ADV' in df_merged.columns:
                opts_adv_match = sorted(df_merged['ADV'].astype(str).unique())
                sel_adv_match = f_m1.multiselect("Filtrar ADV", opts_adv_match, key="fm_adv")

            if 'Agency' in df_merged.columns:
                opts_ag_match = sorted(df_merged['Agency'].unique())
                sel_ag_match = f_m2.multiselect("Filtrar Agency", opts_ag_match, key="fm_ag")
            
            if 'App ID / Template' in df_merged.columns:
                opts_app_match = sorted(df_merged['App ID / Template'].unique())
                sel_app_match = f_m3.multiselect("Filtrar App ID", opts_app_match, key="fm_app")

            if 'PID' in df_merged.columns:
                opts_pid_match = sorted(df_merged['PID'].unique())
                sel_pid_match = f_m4.multiselect("Filtrar PID", opts_pid_match, key="fm_pid")

            # Aplicar filtros
            df_show = df_merged.copy()
            if sel_adv_match and 'ADV' in df_show.columns: 
                df_show = df_show[df_show['ADV'].astype(str).isin(sel_adv_match)]
            if sel_ag_match and 'Agency' in df_show.columns: 
                df_show = df_show[df_show['Agency'].isin(sel_ag_match)]
            if sel_app_match and 'App ID / Template' in df_show.columns: 
                df_show = df_show[df_show['App ID / Template'].isin(sel_app_match)]
            if sel_pid_match and 'PID' in df_show.columns: 
                df_show = df_show[df_show['PID'].isin(sel_pid_match)]

            # 7. CÁLCULO DE LOS PORCENTAJES
            col_pct_calc = '% Bloqueado'
            col_pct_maq_calc = '% bloqueado Maquinillo'
            
            # % Bloqueado original (Blocked IMPs vs cloudfront_ok_count)
            if 'cloudfront_ok_count' in df_show.columns and i_col_block in df_show.columns:
                df_show[col_pct_calc] = (df_show[i_col_block] / df_show['cloudfront_ok_count'] * 100).fillna(0)
                df_show[col_pct_calc] = df_show[col_pct_calc].replace([np.inf, -np.inf], 0).round(2)

            # NUEVO % bloqueado Maquinillo (cloudfront_ok_count vs Aftrad IMPs)
            if 'cloudfront_ok_count' in df_show.columns and i_col_imps in df_show.columns:
                df_show[col_pct_maq_calc] = (df_show['cloudfront_ok_count'] / df_show[i_col_imps] * 100).fillna(0)
                df_show[col_pct_maq_calc] = df_show[col_pct_maq_calc].replace([np.inf, -np.inf], 0).round(2)

            # 8. MOSTRAR TABLA FINAL
            st.markdown(f"**Coincidencias exactas encontradas:** {len(df_show)} filas combinadas.")
            
            # Ordenamos las columnas poniendo ADV primero
            keys_existentes = [c for c in ['ADV', 'Agency', 'App ID / Template', 'PID'] if c in df_show.columns]
            columnas_finales = keys_existentes + avail_m_metrics + [i_col_imps, i_col_block]
            
            # Añadimos los porcentajes si las columnas existen
            if 'cloudfront_ok_count' in df_show.columns and i_col_block in df_show.columns:
                columnas_finales.append(col_pct_calc)
                
            if 'cloudfront_ok_count' in df_show.columns and i_col_imps in df_show.columns:
                columnas_finales.append(col_pct_maq_calc)
                
            df_show = df_show[columnas_finales]

            st.dataframe(df_show, use_container_width=True)

        except Exception as e:
            st.error(f"Error realizando el cruce de datos: {e}")
    else:
        st.info("👈 Sube AMBOS archivos en la barra lateral para comenzar.")

# ==========================================
# PESTAÑA 2: COMPARATIVA (USANDO FILTROS DE MATCH)
# ==========================================
with tab_compare:
    st.header("⚖️ Comparativa de Totales (Filtrada)")
    
    if df_show is not None and not df_show.empty:
        try:
            st.success("✅ Usando los datos exactos de la pestaña 'Cruce de Datos'.")
            
            # Sumamos las columnas directamente de df_show (ya filtrado y macheado)
            m_ok = df_show['cloudfront_ok_count'].sum() if 'cloudfront_ok_count' in df_show.columns else 0
            m_err_cf = df_show['cloudfront_error_count'].sum() if 'cloudfront_error_count' in df_show.columns else 0
            m_err_http = df_show['http_error_count'].sum() if 'http_error_count' in df_show.columns else 0
            m_pace = df_show['paced_count'].sum() if 'paced_count' in df_show.columns else 0

            i_imps = df_show[i_col_imps].sum() if i_col_imps in df_show.columns else 0
            i_block = df_show[i_col_block].sum() if i_col_block in df_show.columns else 0
            
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

            st.subheader("📊 Gráfica de Volúmenes (Datos Cruzados)")
            fig_comp = px.bar(
                df_comp_viz, 
                x='Métrica', 
                y='Total (Filtrado)', 
                color='Fuente', 
                text_auto='.2s',
                title="Totales Globales (Respetando Match y Filtros)"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            st.subheader("📋 Tabla de Datos Consolidados")
            st.dataframe(df_comp_viz, use_container_width=True)

        except Exception as e:
            st.error(f"Error en la comparativa: {e}")
    else:
        st.warning("⚠️ Esperando datos... Sube los archivos en la barra lateral y asegúrate de que haya coincidencias en la primera pestaña.")
