import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Maquinillo vs Ivane", layout="wide")

st.title("⚔️ Comparador: Maquinillo vs Ivane")
st.markdown("Sube los reportes para cruzar datos por día.")

# --- 1. ZONA DE CARGA (Dos columnas separadas) ---
col_up1, col_up2 = st.columns(2)

with col_up1:
    st.subheader("📂 1. Datos del Maquinillo")
    file_maq = st.file_uploader("Sube el CSV del Maquinillo", type=["csv"], key="maq")

with col_up2:
    st.subheader("📂 2. Datos de Ivane")
    file_ivane = st.file_uploader("Sube el CSV de Ivane", type=["csv"], key="ivane")

# --- LÓGICA DE PROCESAMIENTO ---
if file_maq and file_ivane:
    try:
        # Cargar archivos (detectando separadores automáticamente si es posible)
        df_m = pd.read_csv(file_maq)
        df_i = pd.read_csv(file_ivane)

        st.success(f"✅ Archivos cargados. Maquinillo: {len(df_m)} filas | Ivane: {len(df_i)} filas.")
        st.markdown("---")

        # --- 2. SINCRONIZACIÓN DE FECHAS ---
        st.subheader("📅 Sincronizar Fechas")
        st.info("Selecciona la columna que indica el DÍA en cada archivo para poder cruzarlos.")

        c_date1, c_date2 = st.columns(2)
        
        # Intentar adivinar la columna de fecha
        def get_date_col_index(df):
            cols = [c for c in df.columns if any(x in c.lower() for x in ['date', 'fecha', 'time', 'day', 'dia'])]
            return df.columns.get_loc(cols[0]) if cols else 0

        with c_date1:
            date_col_m = st.selectbox("Fecha en Maquinillo:", df_m.columns, index=get_date_col_index(df_m))
        
        with c_date2:
            date_col_i = st.selectbox("Fecha en Ivane:", df_i.columns, index=get_date_col_index(df_i))

        # --- 3. PROCESAMIENTO Y LIMPIEZA ---
        
        # Función para limpiar números (quitar comas y convertir a float)
        def clean_number(x):
            if isinstance(x, str):
                return float(x.replace(',', '').replace(' ', ''))
            return float(x)

        # Definir métricas esperadas
        metrics_maq = ['cloudfront_ok_count', 'cloudfront_error_count', 'paced_count']
        metrics_ivane = ['Aftrad IMPs', 'AF Blocked IMPs']

        # --- PREPARAR MAQUINILLO ---
        # Convertir fecha
        df_m[date_col_m] = pd.to_datetime(df_m[date_col_m], errors='coerce').dt.date
        
        # Validar y limpiar métricas del Maquinillo
        cols_found_m = []
        for metric in metrics_maq:
            # Buscar columna ignorando mayúsculas/minúsculas
            match = next((c for c in df_m.columns if c.lower() == metric.lower()), None)
            if match:
                df_m[match] = df_m[match].apply(clean_number)
                cols_found_m.append(match)
            else:
                st.warning(f"⚠️ No encontré '{metric}' en Maquinillo. (Columnas disponibles: {list(df_m.columns)})")

        # Agrupar Maquinillo por Día
        if cols_found_m:
            df_m_grouped = df_m.groupby(date_col_m)[cols_found_m].sum().reset_index()
            # Renombrar columna fecha para el merge
            df_m_grouped = df_m_grouped.rename(columns={date_col_m: 'Fecha'})

        # --- PREPARAR IVANE ---
        # Convertir fecha
        df_i[date_col_i] = pd.to_datetime(df_i[date_col_i], errors='coerce').dt.date

        # Validar y limpiar métricas de Ivane
        cols_found_i = []
        for metric in metrics_ivane:
            match = next((c for c in df_i.columns if c.lower() == metric.lower()), None)
            if match:
                df_i[match] = df_i[match].apply(clean_number)
                cols_found_i.append(match)
            else:
                st.warning(f"⚠️ No encontré '{metric}' en Ivane. (Columnas disponibles: {list(df_i.columns)})")

        # Agrupar Ivane por Día
        if cols_found_i:
            df_i_grouped = df_i.groupby(date_col_i)[cols_found_i].sum().reset_index()
            df_i_grouped = df_i_grouped.rename(columns={date_col_i: 'Fecha'})

        # --- 4. CRUCE DE DATOS (MERGE) ---
        if cols_found_m and cols_found_i:
            # Unir por la columna 'Fecha'
            df_final = pd.merge(df_m_grouped, df_i_grouped, on='Fecha', how='outer').sort_values('Fecha')
            
            # Rellenar con 0 los días que falten en uno de los dos lados
            df_final = df_final.fillna(0)

            # --- 5. VISUALIZACIÓN ---
            st.markdown("---")
            st.markdown("### 📈 Gráfica Comparativa")

            all_available_metrics = cols_found_m + cols_found_i

            # Selector de métricas
            selected_metrics = st.multiselect(
                "Selecciona las métricas que quieres visualizar:",
                options=all_available_metrics,
                default=all_available_metrics # Por defecto marca todas
            )

            if selected_metrics:
                # Crear gráfica
                fig = px.line(
                    df_final,
                    x='Fecha',
                    y=selected_metrics,
                    markers=True,
                    title="Evolución Diaria: Maquinillo vs Ivane",
                    labels={'value': 'Cantidad', 'variable': 'Métrica'}
                )
                fig.update_layout(hovermode="x unified") # Tooltip comparativo
                st.plotly_chart(fig, use_container_width=True)

                # Tabla de datos
                with st.expander("Ver tabla de datos consolidados"):
                    st.dataframe(df_final)
            else:
                st.info("Selecciona al menos una métrica para ver la gráfica.")
        
        else:
            st.error("No se pudieron encontrar las métricas necesarias en los archivos. Revisa los nombres de las columnas.")

    except Exception as e:
        st.error(f"Error procesando los archivos: {e}")
else:
    st.info("👆 Por favor sube ambos archivos para comenzar.")
