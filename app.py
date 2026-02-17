import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Comparador de CSVs", layout="wide")

st.title("⚔️ Comparador de Reportes (Cruce de Datos)")
st.markdown("Sube dos archivos diferentes y define sus equivalencias para comparar métricas.")

# --- PASO 1: SUBIR LOS DOS ARCHIVOS ---
c1, c2 = st.columns(2)
with c1:
    file1 = st.file_uploader("📂 Archivo 1 (Izquierda)", type=["csv"], key="f1")
with c2:
    file2 = st.file_uploader("📂 Archivo 2 (Derecha)", type=["csv"], key="f2")

if file1 and file2:
    try:
        # Cargar archivos
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        # Limpiar nombres de columnas (minúsculas y sin espacios) para facilitar lectura
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        st.success(f"✅ Archivos cargados. Archivo 1: {len(df1)} filas | Archivo 2: {len(df2)} filas.")
        st.markdown("---")

        # --- PASO 2: DEFINIR EQUIVALENCIAS (KEYS) ---
        st.subheader("1️⃣ Definir la columna en común (La Llave)")
        st.info("Selecciona la columna que identifica lo mismo en ambos archivos (Ej: 'PID' en uno y 'Publisher_ID' en el otro).")

        col_key1, col_key2 = st.columns(2)
        
        with col_key1:
            key1 = st.selectbox(f"Llave en {file1.name}:", df1.columns)
        
        with col_key2:
            key2 = st.selectbox(f"Llave en {file2.name}:", df2.columns)

        # --- PASO 3: HACER EL CRUCE (MERGE) ---
        # Realizamos el 'merge' inner (solo lo que coincide en ambos)
        # Añadimos sufijos _1 y _2 para distinguir columnas con el mismo nombre (ej: count_1, count_2)
        df_merged = pd.merge(df1, df2, left_on=key1, right_on=key2, how='inner', suffixes=('_Archivo1', '_Archivo2'))
        
        if df_merged.empty:
            st.error("❌ El cruce no generó resultados. No hay valores coincidentes en las columnas seleccionadas.")
        else:
            st.success(f"🔗 ¡Cruce exitoso! Se encontraron {len(df_merged)} coincidencias exactas.")
            
            # --- PASO 4: COMPARAR MÉTRICAS ---
            st.markdown("---")
            st.subheader("2️⃣ Comparativa Gráfica")
            
            # Identificar columnas numéricas para graficar
            nums1 = df_merged.select_dtypes(include=['float', 'int']).columns.tolist()
            
            if not nums1:
                st.warning("No se encontraron columnas numéricas para comparar.")
            else:
                cg1, cg2, cg3 = st.columns(3)
                
                with cg1:
                    metric_x = st.selectbox("Eje X (Dato del Archivo 1)", nums1, index=0)
                with cg2:
                    metric_y = st.selectbox("Eje Y (Dato del Archivo 2)", nums1, index=1 if len(nums1)>1 else 0)
                with cg3:
                    # Opcional: Color por categoría
                    cat_cols = df_merged.select_dtypes(include=['object']).columns.tolist()
                    color_col = st.selectbox("Color por (Opcional)", ["Ninguno"] + cat_cols)

                # Calcular la diferencia/discrepancia
                df_merged['Diferencia'] = df_merged[metric_x] - df_merged[metric_y]
                df_merged['% Discrepancia'] = ((df_merged[metric_x] - df_merged[metric_y]) / df_merged[metric_x]).fillna(0) * 100

                # --- GRÁFICA DE DISPERSIÓN (SCATTER) ---
                # Es la mejor para comparar A vs B. Si los puntos están en la linea diagonal, coinciden perfecto.
                fig = px.scatter(
                    df_merged,
                    x=metric_x,
                    y=metric_y,
                    color=None if color_col == "Ninguno" else color_col,
                    hover_data=[key1, key2, 'Diferencia', '% Discrepancia'],
                    title=f"Comparativa: {metric_x} vs {metric_y}",
                    template="plotly_white"
                )
                
                # Añadir una línea diagonal de referencia (donde X = Y)
                fig.add_shape(type="line",
                    x0=min(df_merged[metric_x].min(), df_merged[metric_y].min()),
                    y0=min(df_merged[metric_x].min(), df_merged[metric_y].min()),
                    x1=max(df_merged[metric_x].max(), df_merged[metric_y].max()),
                    y1=max(df_merged[metric_x].max(), df_merged[metric_y].max()),
                    line=dict(color="Red", dash="dash"),
                    opacity=0.5
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.caption("💡 La línea roja discontinua representa la coincidencia perfecta. Los puntos alejados son discrepancias.")

            # --- TABLA DE DATOS CRUZADOS ---
            with st.expander("Ver Tabla de Datos Cruzados y Discrepancias"):
                st.dataframe(df_merged)

    except Exception as e:
        st.error(f"Error procesando los archivos: {e}")

else:
    st.info("👆 Sube dos archivos CSV para comenzar la comparativa.")
