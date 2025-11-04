import pandas as pd
import plotly.express as px
import dash
import json
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

# --- Cargar y Preparar Datos ---
PATH_MUERTES = 'datos_mortalidad.xlsx'
PATH_CODIGOS = 'codigos_causas.xlsx'
PATH_DIVIPOLA = 'divipola.xlsx'
# 1. Cargar DataFrames
try:
    df_muertes = pd.read_excel(PATH_MUERTES)
    df_codigos = pd.read_excel(PATH_CODIGOS)
    df_divipola = pd.read_excel(PATH_DIVIPOLA)
except FileNotFoundError as e:
    print(f"Error al cargar archivos: {e}")
    exit()

print("Datos cargados exitosamente.")

try:
    with open('Colombia.geo.json', 'r') as f:
        geojson_data = json.load(f)
except FileNotFoundError:
    print("¡Advertencia! No se encontró 'Colombia.geo.json'. El mapa no funcionará sin este archivo.")
    geojson_data = None

print("Archivo Geoson listo.")


# # ** Importante: Fusión y limpieza de datos aquí **
df_muertes['FECHA_DEFUNCION'] = pd.to_datetime(df_muertes['FECHA_DEFUNCION'], errors='coerce')
df_muertes.dropna(subset=['FECHA_DEFUNCION'], inplace=True) # Elimina filas sin fecha

# 🔑 Estandarizar el código DANE completo (5 dígitos)
# Ejemplo de nombres de columnas en el archivo de mortalidad
COL_DPTO_MUERTES = 'COD_DEPARTAMENTO' # Código del departamento
COL_MPIO_MUERTES = 'COD_MUNICIPIO' # Código del municipio
COL_CAUSA_MUERTES = 'COD_MUERTE' # Código CIE-10

# Crear el código DANE completo de 5 dígitos (e.g., 05 + 001 = 05001)
df_muertes['COD_DANE_DPTO'] = df_muertes[COL_DPTO_MUERTES].astype(str).str.zfill(2)
df_muertes['COD_DANE_MPIO'] = df_muertes[COL_MPIO_MUERTES].astype(str).str.zfill(3)
df_muertes['COD_DANE_COMPLETO'] = df_muertes['COD_DANE_DPTO'] + df_muertes['COD_DANE_MPIO']

# Asegurar que el código CIE-10 sea String
df_muertes[COL_CAUSA_MUERTES] = df_muertes[COL_CAUSA_MUERTES].astype(str).str.strip()

print("df_muertes listo.")

# Ejemplo de nombres de columnas en el archivo DIVIPOLA
COL_DPTO_DIVIPOLA = 'COD_DEPARTAMENTO'
COL_MPIO_DIVIPOLA = 'COD_MUNICIPIO'
COL_NOMBRE_DPTO = 'DEPARTAMENTO'
COL_NOMBRE_MPIO = 'MUNICIPIO'

# 🔑 Crear el código DANE completo de 5 dígitos
df_divipola['COD_DANE_DPTO'] = df_divipola[COL_DPTO_DIVIPOLA].astype(str).str.zfill(2)
df_divipola['COD_DANE_MPIO'] = df_divipola[COL_MPIO_DIVIPOLA].astype(str).str.zfill(3)
df_divipola['COD_DANE_COMPLETO'] = df_divipola['COD_DANE_DPTO'] + df_divipola['COD_DANE_MPIO']

# Seleccionar solo las columnas necesarias para evitar duplicados en la fusión
df_divipola = df_divipola[[
    'COD_DANE_COMPLETO', 
    COL_NOMBRE_DPTO, 
    COL_NOMBRE_MPIO
]].drop_duplicates()

print("df_divipola listo.")


# Ejemplo de nombres de columnas en el archivo de Códigos
COL_CODIGO_CAUSA = 'Codigo' # CIE-10
COL_NOMBRE_CAUSA = 'Nombre Causa'

df_codigos[COL_CODIGO_CAUSA] = df_codigos[COL_CODIGO_CAUSA].astype(str).str.strip()

# Renombrar para claridad después de la fusión
df_codigos = df_codigos.rename(columns={
    COL_CODIGO_CAUSA: COL_CAUSA_MUERTES,
    COL_NOMBRE_CAUSA: 'NOMBRE_CAUSA_CIE10'
})

print("df_codigos listo.")



# 1. Fusión Geográfica (muertes + divipola)
df_final = pd.merge(
    df_muertes, 
    df_divipola, 
    on='COD_DANE_COMPLETO', 
    how='left'
)

# 2. Fusión de Causas de Muerte (df_final + codigos)
df_final = pd.merge(
    df_final, 
    df_codigos, 
    on=COL_CAUSA_MUERTES, 
    how='left'
)

# --- Limpieza Final de Columnas para Dash ---
# Crear el mes como una columna numérica para el gráfico de líneas
df_final['MES'] = df_final['FECHA_DEFUNCION'].dt.month

# Renombrar columnas clave para que coincidan con la lógica del Dash:
df_final = df_final.rename(columns={
    COL_NOMBRE_DPTO: 'DEPARTAMENTO',
    COL_NOMBRE_MPIO: 'MUNICIPIO',
    'NOMBRE_CAUSA_CIE10': 'CAUSA_NOMBRE',
    COL_CAUSA_MUERTES: 'CAUSA_CODIGO',
    'SEXO': 'SEXO', # Asegúrate que esta columna existe en tu archivo de muertes
    'GRUPO_EDAD1': 'GRUPO_EDAD1' # Asegúrate que esta columna existe
})

# ¡DataFrame final listo para ser usado por Plotly y Dash!
print("\n✅ Fusión completa. DataFrame final (df_final) creado.")
print(f"Número de registros en el DataFrame final: {len(df_final)}")
print(df_final[['DEPARTAMENTO', 'MUNICIPIO', 'CAUSA_NOMBRE', 'MES','COD_DANE_COMPLETO']].head())



# --- MAPEO DE GRUPOS DE EDAD DANE A CATEGORÍA ---
def categorizar_grupo_edad(codigo):
    """Convierte el código numérico de GRUPO_EDAD1 a la categoría descriptiva."""
    try:
        codigo = int(codigo) # Asegurar que es un entero para la comparación

        if codigo in range(0, 5): return 'Mortalidad neonatal (<1 mes)'
        if codigo in range(5, 7): return 'Mortalidad infantil (1 a 11 meses)'
        if codigo in range(7, 9): return 'Primera infancia (1 a 4 años)'
        if codigo in range(9, 11): return 'Niñez (5 a 14 años)'
        if codigo == 11: return 'Adolescencia (15 a 19 años)'
        if codigo in range(12, 14): return 'Juventud (20 a 29 años)'
        if codigo in range(14, 17): return 'Adultez temprana (30 a 44 años)'
        if codigo in range(17, 20): return 'Adultez intermedia (45 a 59 años)'
        if codigo in range(20, 25): return 'Vejez (60 a 84 años)'
        if codigo in range(25, 29): return 'Longevidad / Centenarios (85+)'
        if codigo == 29: return 'Edad desconocida'
        return 'Código no válido'

    except (ValueError, TypeError):
        return 'Dato faltante o incorrecto'

# Crea una nueva columna categórica con los nombres descriptivos
df_final['GRUPO_EDAD_CAT'] = df_final['GRUPO_EDAD1'].apply(categorizar_grupo_edad)

# Suponiendo que el archivo DANE se llama 'proyecciones_poblacion_municipal.xlsx'
df_poblacion_raw = pd.read_excel('proyecciones_poblacion_municipal.xlsx')

# 1. Filtrar solo los datos de 2019 --->>> No consegui los datos del 2019, entonces estoy usando datos del 2020
print("Iniciando filtrado y preparación del DataFrame de Población...")
    
 # --- 1. Filtrado Crucial ---
# a. Filtrar por el año 2019  --->>> No consegui los datos del 2019, entonces estoy usando datos del 2020
df_poblacion = df_poblacion_raw[df_poblacion_raw['AÑO'] == 2020].copy()
df_poblacion = df_poblacion[df_poblacion['AREA'] == 'Total'].copy()

# 2. SOLUCIÓN CRUCIAL: Conversión a String y Relleno de Ceros
df_poblacion['COD_DANE_COMPLETO'] = (
    df_poblacion['MPIO']
    .astype(str)   # 1. Convertir a string (ej. 5001.0 -> '5001.0')
    .str.replace(r'\.0$', '', regex=True) # 2. Eliminar el ".0" si viene de un float (ej. '5001')
    .str.strip()   # 3. Eliminar espacios en blanco
    .str.zfill(5)  # 4. Rellenar con ceros a la izquierda hasta tener 5 dígitos (ej. '5001' -> '05001')
)

# 3. Renombrar y seleccionar columnas clave
df_poblacion = df_poblacion.rename(columns={'TOTAL': 'POBLACION_2019'})
df_poblacion = df_poblacion[['COD_DANE_COMPLETO', 'POBLACION_2019']].copy()

# Asegurar que la población sea numérica y manejar NaN (si los hay)
df_poblacion['POBLACION_2019'] = pd.to_numeric(df_poblacion['POBLACION_2019'], errors='coerce')
df_poblacion.dropna(subset=['POBLACION_2019'], inplace=True)
    
print(f"DataFrame de Población listo. Registros de 2019: {len(df_poblacion)}")
print(df_poblacion.head())


# 1. Contar el total de muertes por municipio (usando el código DANE completo)
df_muertes_muni = df_final.groupby('COD_DANE_COMPLETO').size().reset_index(name='Total Muertes')

# 2. Fusionar el conteo de muertes con la población (df_poblacion)
df_tbm = pd.merge(
    df_muertes_muni, 
    df_poblacion, 
    on='COD_DANE_COMPLETO', 
    how='inner' # Asegura que solo se incluyan municipios con datos de población en 2019
)

# 3. Calcular la Tasa Bruta de Mortalidad (TBM)
# TBM = (Total de Muertes / Población) * 100,000
df_tbm['TASA_MORTALIDAD'] = (df_tbm['Total Muertes'] / df_tbm['POBLACION_2019']) * 100000

# 4. Fusionar con DIVIPOLA para obtener el NOMBRE del Municipio
# Necesitas una versión de df_divipola con la columna 'MUNICIPIO' y 'COD_DANE_COMPLETO'
df_nombres = df_divipola[['COD_DANE_COMPLETO', 'MUNICIPIO']].drop_duplicates()

df_tbm_completo = pd.merge(
    df_tbm,
    df_nombres,
    on='COD_DANE_COMPLETO',
    how='left'
)

# 5. Filtrar municipios con población mínima y seleccionar el Top 10 con la TBM más baja
POBLACION_MINIMA = 10000 # Filtro para excluir municipios rurales muy pequeños y evitar tasas extremas
df_tbm_final = df_tbm_completo[df_tbm_completo['POBLACION_2019'] >= POBLACION_MINIMA]

# Seleccionar el Top 10 con la Tasa MÁS BAJA (ascendente=True)
df_tbm_top_10_menor = df_tbm_final.sort_values(by='TASA_MORTALIDAD', ascending=True).head(10)

# El DataFrame 'df_tbm_top_10_menor' está listo para el callback.
print("DataFrame para Gráfico Circular de Menor Mortalidad listo.")
print(df_tbm_top_10_menor[['MUNICIPIO', 'TASA_MORTALIDAD']])

# 1. Lista actualizada para forzar el orden cronológico de las categorías
ORDEN_GRUPOS_EDAD_FINAL = [
    'Mortalidad neonatal (<1 mes)', 
    'Mortalidad infantil (1 a 11 meses)', 
    'Primera infancia (1 a 4 años)', 
    'Niñez (5 a 14 años)', 
    'Adolescencia (15 a 19 años)', 
    'Juventud (20 a 29 años)', 
    'Adultez temprana (30 a 44 años)', 
    'Adultez intermedia (45 a 59 años)', 
    'Vejez (60 a 84 años)', 
    'Longevidad / Centenarios (85+)',
    'Edad desconocida'
]
# ----------------------------------------------------------------------
# --- Fin del Preprocesamiento 




app = dash.Dash(__name__)
# Set the page title
app.title = "Análisis de Mortalidad en Colombia"
# --- Diseño (Layout) de la Aplicación ---
app.layout = html.Div([
    html.Img(src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Logo_de_la_Univesidad_de_la_Salle_%28Bogot%C3%A1%29.svg/330px-Logo_de_la_Univesidad_de_la_Salle_%28Bogot%C3%A1%29.svg.png", alt="Universidad de la Salle", style={'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto', 'width': '500px'}),
    html.H1("MAESTRIA EN INTELIGENCIA ARTIFICIAL", style={'textAlign': 'center'}),
    html.H1("APLICACIONES I", style={'textAlign': 'center'}),
    html.H2("Unidad 2. Aplicación web con dashboard interactivo en Python", style={'textAlign': 'center'}),
    html.H2("Actividad 4: Aplicación web interactiva para el análisis de mortalidad en Colombia", style={'textAlign': 'center'}),
    html.Hr(),
    html.H2("Estudiante: Victor Hugo Cardona Cardona", style={'textAlign': 'center'}),
    html.Hr(),
    html.H1("💀 Análisis de Mortalidad en Colombia (2019) 💀", style={'textAlign': 'center'}),
    html.Hr(),

    # Contenedor para el Mapa y el Gráfico de Barras Apiladas (Visualizaciones Regionales)
    html.Div([
        html.Div([
            html.H3("Mapa de Muertes por Departamento"),
            dcc.Graph(id='mapa-departamentos'),
        ], style={'width': '100%', 'display': 'inline-block', 'padding': '0 20'}),
    ]),
    html.Hr(),

    html.Div([
        html.Div([
            html.H3("Muertes por Mes"),
            dcc.Graph(id='lineas-mensual'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),

         html.Div([
            html.H3("Top 5 Ciudades más Violentas (Homicidios)"),
            dcc.Graph(id='barras-violencia'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    
    ]),
    html.Hr(),

    # Contenedor para Gráfico de Líneas y Tabla (Visualizaciones Temporales y Top Causas)
    html.Div([
        html.Div([
            html.H3("Top 10 Ciudades con Menor Índice de Mortalidad"),
            dcc.Graph(id='circular-menor-mortalidad'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),

        html.Div([
            html.H3("Top 10 Causas de Muerte"),
            html.Div(id='tabla-top-causas'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    ]),
    html.Hr(),

    # Contenedor para Gráficos de Barras y Circular (Violencia y Menor Mortalidad)
    html.Div([
        html.Div([
            html.H3("Muertes por Sexo y Departamento"),
            dcc.Graph(id='barras-apiladas-sexo'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
      
        html.Div([
            html.H3("Distribución de Muertes por Grupo de Edad"),
            dcc.Graph(id='histograma-edad'),
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),        
    ]),
])

# --- Callbacks para Generar los Gráficos (La lógica) ---

# Asegúrate de usar 'df_final' de tu preprocesamiento
@app.callback(
    Output('mapa-departamentos', 'figure'),
    [Input('mapa-departamentos', 'id')] # Input dummy
)
def update_map_chart(_):
    if geojson_data is None:
        # Devuelve una figura vacía o de error si el GeoJSON no se cargó
        return px.scatter(title="Error: GeoJSON no disponible para el mapa.")
    
    # --- 1. Agregación de Datos ---
    # Contar el total de muertes por el código DANE de 2 dígitos (COD_DANE_DPTO)
    # Se usa el código DANE de 2 dígitos para coincidir con la clave del GeoJSON.
    df_mapa = df_final.groupby('COD_DANE_DPTO').size().reset_index(name='Total Muertes')

    # --- 2. Creación del Mapa Coroplético (Choropleth) ---
    fig = px.choropleth(
        df_mapa, 
        geojson=geojson_data,
        locations='COD_DANE_DPTO',  # Columna de datos con los códigos DANE de 2 dígitos
        color='Total Muertes',      # Columna que define el color (intensidad de muertes)
        featureidkey="properties.DPTO", # Clave en el GeoJSON que contiene el código DANE
        
        # Parámetros visuales
        color_continuous_scale="Reds",  # Escala de color
        title="Distribución Total de Muertes por Departamento, Colombia 2019",
        labels={'Total Muertes': 'Total Muertes Registradas'},
        height=650
    )
    
    # --- 3. Ajustes de Layout Geográfico ---
    # Centrar y enfocar el mapa en Colombia
    fig.update_geos(
        fitbounds="locations",          # Ajustar los límites del mapa a los datos
        visible=False                   # Ocultar la capa de fondo global
    )
    
    # Ajustes finales para el mapa
    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title="Muertes",
            thicknessmode="pixels", thickness=20,
            lenmode="pixels", len=300,
            yanchor="top", y=1,
            xanchor="left", x=0.01
        )
    )
    
    return fig



# Lista de nombres de meses en español para etiquetar el eje X
NOMBRES_MESES = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
]

@app.callback(
    Output('lineas-mensual', 'figure'),
    [Input('lineas-mensual', 'id')] # Input dummy para que se ejecute al cargar
)
def update_line_chart(_):
    # --- 1. Agregación de Datos ---
    # Contar el total de muertes por el número de mes (columna 'MES')
    df_mensual = df_final.groupby('MES').size().reset_index(name='Total Muertes')
    
    # Asegurar que todos los meses (1 a 12) estén presentes, llenando con 0 si es necesario
    df_meses_completos = pd.DataFrame({'MES': range(1, 13)})
    df_mensual = pd.merge(df_meses_completos, df_mensual, on='MES', how='left').fillna(0)
    
    # --- 2. Preparación de Etiquetas ---
    # Añadir los nombres de los meses para una mejor visualización en el eje X
    df_mensual['Nombre Mes'] = df_mensual['MES'].apply(lambda x: NOMBRES_MESES[x - 1])

    # --- 3. Creación del Gráfico (Plotly Express) ---
    fig = px.line(
        df_mensual, 
        x='Nombre Mes', 
        y='Total Muertes', 
        title='Total de Muertes por Mes en Colombia (2019)',
        labels={'Nombre Mes': 'Mes', 'Total Muertes': 'Total de Muertes'},
        markers=True,  # Mostrar puntos en cada mes
        line_shape='spline', # Suavizar la línea de tendencia
        height=500
    )
    
    # --- 4. Ajustes de Layout ---
    fig.update_traces(
        mode='lines+markers', 
        marker={'size': 8} # Ajustar el tamaño de los marcadores
    )
    
    fig.update_layout(
        xaxis_title="Mes", 
        yaxis_title="Total Muertes",
        xaxis={'categoryorder':'array', 'categoryarray': NOMBRES_MESES}, # Forzar el orden cronológico
        hovermode="x unified"
    )
    
    return fig


# Lista de los códigos CIE-10 que representan los homicidios (violencia)
# NOTA: Debes verificar que estos códigos coincidan con tu archivo de datos.
CODIGOS_HOMICIDIO = ['X950','X951','X952','X953','X954','X955','X956','X957','X958','X959','Y871'] 
# Aquí usamos X95 (disparo)

@app.callback(
    Output('barras-violencia', 'figure'),
    [Input('barras-violencia', 'id')] # Input dummy para que se ejecute al cargar
)
def update_violencia_bar_chart(_):
    # --- 1. Filtrado de Datos ---
    # Filtrar el DataFrame final para incluir solo las filas que coinciden con los códigos de homicidio
    df_violencia = df_final[df_final['CAUSA_CODIGO'].isin(CODIGOS_HOMICIDIO)].copy()

    # --- 2. Agregación y Top 5 ---
    # Contar los casos por municipio
    df_top_ciudades = df_violencia.groupby('MUNICIPIO').size().reset_index(name='Total Homicidios')
    
    # Ordenar y seleccionar el Top 5
    df_top_5 = df_top_ciudades.sort_values(by='Total Homicidios', ascending=False).head(5)

    # --- 3. Creación del Gráfico (Plotly Express) ---
    fig = px.bar(
        df_top_5,
        x='MUNICIPIO',
        y='Total Homicidios',
        title='Top 5 Ciudades con Mayor Número de Homicidios (2019)',
        labels={'MUNICIPIO': 'Ciudad', 'Total Homicidios': 'Número de Homicidios'},
        color='Total Homicidios', # Usar el conteo para la intensidad de color
        color_continuous_scale=px.colors.sequential.YlOrRd, # Escala de color que indica peligro
        text='Total Homicidios', # Mostrar el valor exacto sobre la barra
        height=500
    )
    
    # Ajustes de Layout
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis={'categoryorder':'total descending'}, # Asegura que las barras estén ordenadas
        margin={"r":20,"t":40,"l":20,"b":20}
    )
    
    return fig



@app.callback(
    Output('tabla-top-causas', 'children'),
    [Input('tabla-top-causas', 'id')] # Input dummy
)
def update_top_causes_table(_):
    # --- 1. Agregación y Conteo ---
    # Agrupar por el código y el nombre de la causa de muerte y contar las ocurrencias.
    df_causas_agg = df_final.groupby(['CAUSA_CODIGO', 'CAUSA_NOMBRE']).size().reset_index(name='Total Casos')

    # --- 2. Selección del Top 10 ---
    # Ordenar de mayor a menor y tomar solo las 10 primeras filas.
    df_top_10_causas = df_causas_agg.sort_values(by='Total Casos', ascending=False).head(10)
    
    # Renombrar columnas para la tabla final
    df_top_10_causas.columns = ['Código CIE-10', 'Causa de Muerte', 'Total Casos']

    # --- 3. Creación de la Tabla (dash_table.DataTable) ---
    tabla_html = dash.dash_table.DataTable(
        id='datatable-top-causas',
        
        # Define las columnas visibles y sus IDs
        columns=[{"name": i, "id": i} for i in df_top_10_causas.columns],
        
        # Convierte el DataFrame en una lista de diccionarios que Dash puede leer
        data=df_top_10_causas.to_dict('records'),
        
        # --- Estilos ---
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'column_id': 'Total Casos'}, # Resaltar la columna de conteo
                'fontWeight': 'bold',
                'textAlign': 'right'
            }
        ]
    )
    
    return tabla_html


#Gráfico de Barras Apiladas (Muertes por Sexo y Departamento)
@app.callback(
    Output('barras-apiladas-sexo', 'figure'),
    [Input('barras-apiladas-sexo', 'id')] # Input dummy para que se ejecute al cargar
)
def update_stacked_bar_chart(_):
    # --- 1. Agregación de Datos ---
    # Contar el total de muertes por DEPARTAMENTO y por SEXO
    # El resultado tendrá tres columnas: DEPARTAMENTO, SEXO, y Total Muertes.
    df_agg = df_final.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='Total Muertes')

    # --- 2. Preparación para Plotly Express ---
    # Opcional: Para el orden visual en el gráfico, puedes ordenar por el total general de muertes
    df_totales = df_agg.groupby('DEPARTAMENTO')['Total Muertes'].sum().sort_values(ascending=False).index
    df_agg['DEPARTAMENTO'] = pd.Categorical(df_agg['DEPARTAMENTO'], categories=df_totales, ordered=True)
    df_agg = df_agg.sort_values('DEPARTAMENTO')

    # --- 3. Creación del Gráfico (Plotly Express) ---
    fig = px.bar(
        df_agg,
        x='DEPARTAMENTO',
        y='Total Muertes',
        color='SEXO',          # Columna usada para apilar las barras (Hombres vs. Mujeres)
        title='Comparación de Muertes por Sexo y Departamento, Colombia 2019',
        labels={'DEPARTAMENTO': 'Departamento', 'Total Muertes': 'Total de Casos'},
        barmode='stack',       # Configura las barras para que se apilen
        height=600,
        color_discrete_map={
            'MASCULINO': '#1f77b4', # Color para hombres
            'FEMENINO': '#ff7f0e'   # Color para mujeres
            # Ajusta estos nombres según cómo estén en tu columna 'SEXO'
        }
    )
    
    # Ajustes de layout
    fig.update_layout(
        xaxis={'categoryorder':'total descending', 'tickangle': 45}, # Ordena los departamentos por total descendente y gira etiquetas
        legend_title_text='Género'
    )
    return fig


@app.callback(
    Output('circular-menor-mortalidad', 'figure'),
    [Input('circular-menor-mortalidad', 'id')] # Input dummy
)
def update_pie_chart_menor_mortalidad(_):
    # Usar el DataFrame de tasas precalculado
    df_pie = df_tbm_top_10_menor.copy()
    
    # Crear la etiqueta para el gráfico circular: Ciudad (Tasa)
    df_pie['Etiqueta'] = df_pie['MUNICIPIO'] + ' (' + df_pie['TASA_MORTALIDAD'].round(1).astype(str) + ')'

    # --- Creación del Gráfico (Plotly Express) ---
    fig = px.pie(
        df_pie,
        values='TASA_MORTALIDAD',
        names='Etiqueta', # Usar la etiqueta combinada para el hover y la leyenda
        title='Top 10 Municipios con Menor Tasa Bruta de Mortalidad (2019)',
        hole=.4, # Crear un "donut chart" para mejor visualización
        height=600,
        color_discrete_sequence=px.colors.sequential.Teal, # Escala de color que indica seguridad/bienestar
    )
    
    # Ajustes de Layout
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Tasa: %{value:.2f} por 100k hab.<extra></extra>"
    )
    
    fig.update_layout(
        showlegend=False, # Ocultar la leyenda si las etiquetas en el gráfico son suficientes
        margin={"r":10,"t":40,"l":10,"b":10}
    )

    return fig



@app.callback(
    Output('histograma-edad', 'figure'),
    [Input('histograma-edad', 'id')]
)
def update_age_histogram(_):
    # --- 1. Creación del Histograma (Plotly Express) ---
    fig = px.histogram(
        df_final,
        x='GRUPO_EDAD_CAT', # Usamos la nueva columna categórica
        title='Distribución de Muertes por Grupo de Edad (2019)',
        labels={'GRUPO_EDAD_CAT': 'Grupo de Edad', 'count': 'Total de Muertes'},
        color_discrete_sequence=['#4c78a8'], 
        height=550
    )
    
    # --- 2. Ajustes de Layout y Orden ---
    fig.update_layout(
        xaxis_title="Grupo de Edad",
        yaxis_title="Total de Muertes",
        # Forzar el orden cronológico de las categorías
        xaxis={'categoryorder':'array', 'categoryarray': ORDEN_GRUPOS_EDAD_FINAL},
        xaxis_tickangle=-45, 
        bargap=0.1
    )
    
    # Opcional: Mostrar el conteo exacto sobre cada barra
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

    return fig


# 1. Necesitas exponer el objeto del servidor de Flask subyacente de Dash.
# Esto es lo que Gunicorn buscará.
server = app.server

if __name__ == '__main__':  
    #app.run_server(debug=True)
    app.run(debug=True)