# Guía de trabajo de GeoNormML

GeoNormML prepara y evalúa clasificadores de rocas. GeoNormPy calcula la
mineralogía normativa CIPW y se mantiene en el repositorio hermano.

## Dónde está cada cosa

| Ubicación | Uso |
| --- | --- |
| src/geonormml | Configuración, datos, variables, control de calidad, particiones y modelos |
| scripts | Etapas ejecutables; consulta el [catálogo](../scripts/README.md) |
| tests | Pruebas automáticas con datos sintéticos y archivos temporales |
| docs | Metodología, revisiones, informes, publicaciones y figuras |
| poster_cpg23 | Generadores, configuraciones, presentaciones y previsualizaciones del congreso |
| Dataset/Filtered/final | Base oficial, referencia v4 y auditorías locales; fuera de Git |
| artifacts | Modelos, particiones, validación, SHAP y archivo histórico; fuera de Git |

## Base que debe utilizarse

La entrada oficial es Dataset/Filtered/final/GeoNormML_training_curated.xlsx:
2.755 muestras, 1.764 volcánicas y 991 plutónicas. Su manifiesto es el archivo
con el mismo nombre y extensión .audit.json. La referencia es el v4 consistente.

La versión de 2.887 filas contenía 132 repeticiones espaciales. La de 2.651
filas es un experimento restrictivo. No sustituir la base oficial por ninguna
de ellas ni descartar IDs por coincidencia química o advertencias CIPW.

Las métricas vigentes están en artifacts/validation/baseline_validation.json.
Antes de usarlas, comprobar que su hash del dataset coincide con el manifiesto
y el archivo real. Validación por grupos de muestras no demuestra transferencia
geográfica independiente. Los modelos exportados se reajustan con toda la base;
sus datos de entrenamiento no son una evaluación externa.

## Entorno de esta PC

El entorno aislado vive en
D:\DevResources\Projects\GeoNormML-11cc092a72\.venv.
No es necesario activar ni modificar el Python global. Desde la raíz del
repositorio, ejecutar los comandos a través del lanzador local:

    .\DEVRESOURCES_RUN.cmd D:\DevResources\Projects\GeoNormML-11cc092a72\.venv\Scripts\python.exe -m pytest -q
    .\DEVRESOURCES_RUN.cmd D:\DevResources\Projects\GeoNormML-11cc092a72\.venv\Scripts\python.exe -m ruff check src scripts tests
    .\DEVRESOURCES_RUN.cmd D:\DevResources\Projects\GeoNormML-11cc092a72\.venv\Scripts\python.exe -m pip check

El lanzador coordina los bloqueos y crea temporales propios en Sessions.
requirements.txt instala el paquete, las herramientas de desarrollo y GeoNormPy;
constraints-py311.txt fija las versiones científicas comprobadas.
Para otra PC, crear un entorno bajo su raíz local de recursos e instalar
requirements.txt desde este repositorio. La letra de unidad puede variar.

## Consultar el pipeline sin ejecutar cálculos

Con el mismo intérprete y lanzador:

    python -m scripts.run_pipeline --list
    python -m scripts.run_pipeline --dry-run

Estos dos comandos muestran las etapas. Ejecutar el pipeline sin esas opciones
puede reconstruir tablas y entrenar modelos. La revisión de organización no
requiere hacerlo. Antes de una corrida nueva, configurar
GEONORMML_ARTIFACTS_DIR con una salida propia para conservar los resultados
anteriores y revisar las salidas fijas de las etapas antiguas de preparación.
GEONORMML_DATASET_PATH permite elegir otra entrada auditada; no autoriza a
reemplazar la base oficial.

## Pósteres

Los scripts permanecen en poster_cpg23 y sus imágenes fuente están en
docs/figuras. Los generadores de tótem Python e Illustrator usan salidas locales
bajo artifacts/posters; GEONORMML_POSTER_OUTPUT_DIR permite elegir otra carpeta.
Los generadores generales conservan su comportamiento documentado de salida.
Las dependencias de Python para presentaciones son el extra posters del paquete.
No ejecutar Illustrator ni generar publicaciones como parte de una revisión del código.

## Conservación

Mantener los originales, modelos, auditorías, firmas y configuraciones locales.
No subir Dataset ni artifacts, no deserializar modelos de procedencia desconocida
y no borrar cachés o históricos para ordenar carpetas.
