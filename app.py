import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Separado", layout="wide")

st.title("📊 Dashboard: Maquinillo & Ivane (Separados)")
st.markdown("Analiza cada reporte por separado con sus propias gráficas y tablas.")

# Creamos dos pestañas para separar los análisis
tab_maq, tab_ivane = st.tabs(["🤖 Reporte Maquinillo", "📋 Reporte Ivane"])

# ==========================================
# PESTAÑA 1: MAQUINILLO (Lógica clásica)
# ==========================================
with tab_maq:
    st.header("Análisis Maquinillo")
    file_maq = st.file_uploader("Sube CSV Maquinillo", type=["csv"], key="u_maq")

    if file_maq:
        try:
            # Carga y limpieza
            df_m = pd.read_csv(file_maq)
            df_m.columns = df_m.columns.str.lower().str.strip()
            
            # Columnas clave
            col_date_m = st.selectbox("Columna Fecha (Maquinillo):", df_m.columns, index=0, key="date_m")
            
            # Convertir fecha
            try:
                df_m[col_date_m] = pd.to_datetime(df_m[col_date_m])
                df_m = df_m.sort_values(col_date_m)
            except:
                st.warning("No se pudo convertir la fecha automáticamente.")

            # Filtros básicos (Agency, Template, PID)
            st.markdown("##### 🔍 Filtros")
            c1, c2, c3 = st.columns(3)
            
            # Agency
            if 'agency' in df_m.columns:
                opts_ag = sorted(df_m['agency'].astype(str).unique())
                sel_ag = c1.multiselect("Agency", opts_ag, key="f_ag")
            else:
                sel_ag = []
            
            # Template
            if 'template' in df_m.columns:
                if sel_ag:
                    opts_tp = sorted(df_m[df_m['agency'].isin(sel_ag)]['template'].astype(str).unique())
                else:
                    opts_tp = sorted(df_m['template'].astype(str).unique())
                sel_tp = c2.multiselect("Template", opts_tp, key="f_tp")
            else:
                sel_tp = []

            # PID
            if 'pid' in df_m.columns:
                df_temp = df_m.copy()
                if sel_ag: df_temp = df_temp[df_temp['agency'].isin(sel_ag)]
                if sel_tp: df_temp = df_temp[df_temp['template'].isin(sel_tp)]
                opts_pid = sorted(df_temp['pid'].astype(str).unique())
                sel_pid = c3.multiselect("PID", opts_pid, key="f_pid")
            else:
                sel_pid = []

            # Aplicar filtros
            df_m_filt = df_m.copy()
            if sel_ag: df_m_filt = df_m_filt[df_m_filt['agency'].isin(sel_ag)]
            if sel_tp: df_m_filt = df_m_filt[df_m_filt['template'].isin(sel_tp)]
            if sel_pid: df_m_filt = df_m_filt[df_m_filt['pid'].isin(sel_pid)]

            # Gráfica Maquinillo
            st.markdown("---")
            metrics_m = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
            avail_metrics_m = [c for c in metrics_m if c in df_m_filt.columns]
            
            # Agrupar por día para la gráfica
            if avail_metrics_m:
                df_m_chart = df_m_filt.groupby(col_date_m)[avail_metrics_m].sum().reset_index()
                
                st.subheader("📈 Gráfica Maquinillo")
                fig_m = px.line(df_m_chart, x=col_date_m, y=avail_metrics_m, markers=True)
                st.plotly_chart(fig_m, use_container_width=True)
            
            with st.expander("Ver Datos Maquinillo"):
                st.dataframe(df_m_filt)

        except Exception as e:
            st.error(f"Error en Maquinillo: {e}")

# ==========================================
# PESTAÑA 2: IVANE (Sumatorios por día)
# ==========================================
with tab_ivane:
    st.header("Análisis Ivane (Sumatorios Diarios)")
    file_ivane = st.file_uploader("Sube CSV Ivane", type=["csv"], key="u_ivane")

    if file_ivane:
        try:
            # 1. Cargar
            df_i = pd.read_csv(file_ivane)
            
            # Limpiar columnas
            df_i.columns = df_i.columns.str.strip()
            
            st.success(f"Cargado: {len(df_i)} filas.")

            # 2. Configurar Fecha
            col_date_i = st.selectbox("Selecciona la columna de FECHA:", df_i.columns, key="date_i")
            
            # Convertir a fecha real (solo día)
            try:
                df_i[col_date_i] = pd.to_datetime(df_i[col_date_i], errors='coerce').dt.date
                df_i = df_i.sort_values(col_date_i)
            except:
                st.warning("⚠️ No se pudo convertir a formato fecha. Se usará como texto.")

            st.markdown("---")
            st.subheader("🔍 Filtros Dinámicos")
            
            # 3. Generar filtros automáticamente para columnas de texto
            # Identificamos columnas que NO son números y NO son la fecha
            cat_cols = df_i.select_dtypes(include=['object']).columns.tolist()
            cat_cols = [c for c in cat_cols if c != col_date_i]
            
            # Filtros en columnas (3 por fila)
            cols_filter = st.columns(3)
            filters_applied = {}
            
            for idx, col in enumerate(cat_cols):
                with cols_filter[idx % 3]:
                    # Llenamos el filtro con los valores únicos
                    options = sorted(df_i[col].astype(str).unique())
                    selected = st.multiselect(f"Filtrar por {col}", options, key=f"fil_{col}")
                    if selected:
                        filters_applied[col] = selected

            # 4. Aplicar Filtros
            df_i_filt = df_i.copy()
            for col, vals in filters_applied.items():
                df_i_filt = df_i_filt[df_i_filt[col].astype(str).isin(vals)]

            st.markdown(f"**Registros después de filtrar:** {len(df_i_filt)}")

            # 5. TABLA DE SUMATORIOS POR DÍA (Lo que pediste)
            st.markdown("---")
            st.subheader("∑ Tabla de Sumatorios por Día")
            
            # Identificar columnas numéricas para sumar
            num_cols = df_i_filt.select_dtypes(include=['float', 'int']).columns.tolist()
            # Quitamos la fecha si la detectó como número por error
            num_cols = [c for c in num_cols if c != col_date_i]

            if num_cols:
                # AGRUPAR Y SUMAR
                df_sum = df_i_filt.groupby(col_date_i)[num_cols].sum().reset_index()
                
                # Mostrar tabla
                st.dataframe(df_sum, use_container_width=True)

                # 6. GRÁFICA IVANE
                st.subheader("📈 Gráfica de Tendencia (Ivane)")
                metrics_plot = st.multiselect("Métricas a graficar:", num_cols, default=num_cols[:2] if num_cols else None, key="plot_i")
                
                if metrics_plot:
                    fig_i = px.line(df_sum, x=col_date_i, y=metrics_plot, markers=True, title="Totales Diarios")
                    st.plotly_chart(fig_i, use_container_width=True)
            else:
                st.warning("No se encontraron columnas numéricas para sumar.")

        except Exception as e:
            st.error(f"Error procesando Ivane: {e}")
