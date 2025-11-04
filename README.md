# MIA-Aplicaciones1-Actividad4
Actividad 4 - APlicaciones 1 - Maestria Inteligencia Artificial - UNISALLE 
Victor Hugo Cardona Cardona

💀 Análisis Dinámico de Mortalidad en Colombia (2019)
📄 Introducción del Proyecto
Este proyecto es una aplicación web dinámica e interactiva desarrollada en Python utilizando el framework Dash y la librería Plotly. Su propósito es ofrecer una herramienta accesible y completa para la exploración y el análisis de la mortalidad registrada en Colombia durante el año 2019, permitiendo identificar patrones demográficos, temporales y regionales clave.

🎯 Objetivo
El objetivo principal es transformar datos brutos de mortalidad, codificación CIE-10 y geolocalización DANE en siete visualizaciones interactivas que permitan a usuarios y analistas:

-Identificar las principales causas de muerte que afectan a la población colombiana.
-Visualizar la distribución geográfica de las muertes, identificando los departamentos y municipios más afectados.
-Analizar la variación temporal de la mortalidad a lo largo del año.
-Comparar las diferencias significativas en la mortalidad según el sexo y el grupo de edad.

🏗️ Estructura del Proyecto
La aplicación utiliza un diseño de archivo único (app.py) para una ejecución sencilla, junto con los archivos de datos necesarios.

Archivo/Carpeta,Descripción
app.py,"Contiene el código fuente completo de la aplicación Dash, incluyendo la carga de datos, el preprocesamiento, el layout y todos los callbacks de las visualizaciones."
data/,"Carpeta que almacena los archivos de datos fuente (Excel, GeoJSON)."
data/datos_mortalidad.xlsx,Datos detallados de las defunciones registradas en 2019.
data/codigos_causas.xlsx,Nombres y códigos de las causas de muerte (CIE-10).
data/divipola.xlsx,Nomenclatura oficial de códigos DANE de departamentos y municipios.
data/proyecciones_poblacion.xlsx,Datos de población municipal 2019 (DANE) para el cálculo de tasas.
assets/,Contiene el archivo GeoJSON (colombia_deptos.geojson) necesario para la visualización del mapa coroplético.
Procfile,Archivo necesario para el despliegue en plataformas como Heroku o Render.
requirements.txt,Lista de todas las librerías Python necesarias.

📦 Requisitos
Para ejecutar esta aplicación, necesitarás Python 3.7 o superior y las siguientes librerías instaladas:

Librería,Versión Mínima Sugerida
Python,3.7+
pandas,1.3.0+
plotly,5.3.1+
dash,2.0.0+
openpyxl,(Necesario para leer archivos .xlsx)

