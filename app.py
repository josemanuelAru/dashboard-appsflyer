import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Universal", layout="wide")

st.title("⏱️ Analizador de Tráfico (Universal)")
st.markdown("Sube tu CSV. Si las columnas tienen nombres distintos, podrás seleccionarlas manualmente.")

# --- CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Sube tu archivo CSV aquí", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. INTENTO DE LECTURA INTELIGENTE (Detectar separador ; o ,)
        # Leemos las primeras lineas para ver si es ; o ,
        import csv
        uploaded_file.seek(0)
        sample = uploaded_file.read(1024).decode("utf-8", errors="ignore")
        uploaded_file.seek(0)
        
        # Detectar delimitador
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except:
            delimiter = ',' # Por defecto
            
        # Leer el CSV con el delimitador detectado
        df = pd.read_csv(uploaded_file, sep=delimiter)
        
        # Normalizar nombres de columnas (minusculas y sin espacios)
        df.columns = df.columns.str.lower().str.strip()
        
        st.success(f"✅ Archivo cargado correctamente ({len(df)} filas). Separador detectado: '{delimiter}'")

        # --- 2. MAPEO DE COLUMNAS (LO IMPORTANTE) ---
        st.markdown("### 🔧 Configuración de Columnas")
        st.info("Confirma qué columna de tu Excel corresponde a cada dato:")

        cols_disponibles = df.columns.tolist()

        c1, c2, c3, c4 = st.columns(4)
        
        # Función para buscar la columna más parecida por defecto
        def find_default(options, keywords):
            for opt in options:
                if any(k in opt for k in keywords):
                    return opt
            return options[0] if options else None

        # Selectores manuales
        with c1:
            col_agency = st.selectbox(
                "Columna Agencia (Agency)", 
                cols_disponibles, 
                index=cols_disponibles.index(find_default(cols_disponibles, ['agency', 'agencia', 'partner', 'source']))
            )
        
        with c2:
            col_template = st.selectbox(
                "Columna Template", 
                cols_disponibles,
                index=cols_disponibles.index(find_default(cols_disponibles, ['template', 'plantilla', 'creative']))
            )

        with c3:
            col_pid = st.selectbox(
                "Columna PID", 
                cols_disponibles,
                index=cols_disponibles.index(find_default(cols_disponibles, ['pid', 'pub', 'id']))
            )
            
        with c4:
            col_time = st.selectbox(
                "Columna Fecha/Hora", 
                cols_disponibles,
                index=cols_disponibles.index(find_default(cols_disponibles, ['date', 'time', 'fecha', 'hora', 'day']))
            )

        # --- 3. PROCESAMIENTO DE DATOS ---
        
        # Convertir Fecha
        try:
            df[col_time] = pd.to_datetime(df[col_time])
            df = df.sort_values(col_time)
        except:
            st.warning(f"⚠️ La columna '{col_time}' se usará como texto (no es fecha válida).")

        # Limpieza de Métricas (Buscamos las columnas numéricas automáticamente)
        metrics_keywords = ['count', 'ok', 'error', 'paced', 'total']
        possible_metrics = [c for c in cols_disponibles if any(k in c for k in metrics_keywords) and c not in [col_agency, col_template, col_pid, col_time]]
        
        # Si no encuentra métricas obvias, deja elegir al usuario
        if not possible_metrics:
            possible_metrics = st.multiselect("No detecté métricas automáticas. Selecciona las columnas numéricas:", cols_disponibles)
        
        # Convertir a números
        for col in possible_metrics:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Convertir dimensiones a string
        for col in [col_agency, col_template, col_pid]:
            df[col] = df[col].astype(str)

        # --- 4. FILTROS LATERALES ---
        st.sidebar.header("Filtros")

        # Filtro A: Agencia
        all_agencies = sorted(df[col_agency].unique())
        sel_agency = st.sidebar.multiselect("Agency", all_agencies)

        # Filtro B: Template
        if sel_agency:
            df_s1 = df[df[col_agency].isin(sel_agency)]
            opts_templ = sorted(df_s1[col_template].unique())
        else:
            opts_templ = sorted(df[col_template].unique())
        sel_template = st.sidebar.multiselect("Template", opts_templ)

        # Filtro C: PID
        df_s2 = df.copy()
        if sel_agency: df_s2 = df_s2[df_s2[col_agency].isin(sel_agency)]
        if sel_template: df_s2 = df_s2[df_s2[col_template].isin(sel_template)]
        opts_pid = sorted(df_s2[col_pid].unique())
        sel_pid = st.sidebar.multiselect("PID", opts_pid)

        # --- APLICAR FILTROS ---
        df_final = df.copy()
        if sel_agency: df_final = df_final[df_final[col_agency].isin(sel_agency)]
        if sel_template: df_final = df_final[df_final[col_template].isin(sel_template)]
        if sel_pid: df_final = df_final[df_final[col_pid].isin(sel_pid)]

        # --- 5. GRÁFICA ---
        st.markdown("---")
        
        if not df_final.empty:
            # Agrupar
            df_chart = df_final.groupby(col_time)[possible_metrics].sum().reset_index()

            st.markdown(f"### 📈 Evolución: {len(df_final)} registros")
            
            c_sel, c_graph = st.columns([1, 4])
            
            with c_sel:
                metrics_to_plot = st.multiselect(
                    "Métricas a graficar:",
                    options=possible_metrics,
                    default=possible_metrics[:2] if possible_metrics else None
                )
            
            with c_graph:
                if metrics_to_plot:
                    fig = px.line(
                        df_chart, 
                        x=col_time, 
                        y=metrics_to_plot, 
                        markers=True,
                        title="Evolución Temporal",
                        labels={'value': 'Cantidad', col_time: 'Fecha/Hora', 'variable': 'Métrica'}
                    )
                    fig.update_layout(hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Selecciona métricas.")
            
            # Tabla
            with st.expander("Ver Datos"):
                st.dataframe(df_final)
                
        else:
            st.warning("No hay datos con esos filtros.")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("👆 Sube tu archivo CSV.")
