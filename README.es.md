<p align="center"><a href="README.md">English</a> · <strong>Español</strong></p>

# GeoNormML

Decisión operativa del 27 de octubre: PetroPyQAPF adopta los pesos congelados de la selección final v5, HistGradientBoosting volcánico y RandomForest plutónico. Macro F1 interno del selector: 0,635 / 0,389; evaluación externa pendiente. Se conserva Legacy. Véase la [decisión y sus límites](docs/revisiones/adopcion_petropyqapf_v5_20261027.md); no reemplaza los resultados históricos del CPG XXIII ni acredita validez externa.

Consulta el [estado vigente y los pendientes](docs/STATUS.es.md). La decisión v5
sustituye la descripción de despliegue de informes anteriores, sin modificar
sus resultados ni sus artefactos.

**Aprendizaje automático informado por petrografía para geoquímica de roca total.**

Construye experimentos trazables de clasificación a partir de análisis químicos,
minerales normativos, contexto espacial y evaluación reproducible.

> Repositorio de investigación: los datos fuente y modelos entrenados se
> mantienen fuera de Git. Clonar el código no proporciona un clasificador
> preentrenado ni permisos para redistribuir datos.

## Empieza por la documentación

- [Guía de trabajo en español](docs/GUIA_DE_TRABAJO.md).
- [Índice documental](docs/README.md).
- [Catálogo de scripts](scripts/README.md).
- [Corrección de la base curada](docs/revisiones/curated_baseline_correction_20260920.md).

La base oficial conserva **2.755 muestras**. El experimento con 2.651 filas no
es la referencia oficial. Se eliminan repeticiones de uniones espaciales, se
conservan los identificadores curados y se registran revisiones adicionales sin
descartar muestras silenciosamente.

**GeoNormPy / GeoNormML Legacy** identifica el trabajo técnico presentado en el
**XXIII Congreso Peruano de Geología**. Se conservan sus resultados históricos.
GeoNormPy 1.0.0 también se identifica como Legacy; la compatibilidad corregida
de 1.1.0 no es idéntica al motor anterior. El baseline histórico curated_grouped_v2 conserva dos modelos combined_core.
La adopción operativa actual corresponde a v5, descrita arriba.
[Referencia al trabajo técnico y cita del software](CITATION.cff) · [CPG XXIII](https://congresosgp.org.pe/).

Consulta la [decisión de versiones y métricas](docs/revisiones/modelos_legacy_y_vigentes.md).

La [comparación controlada](docs/revisiones/causas_metricas_20261026.md) reproduce
el resumen Legacy y separa el efecto de agrupación, población y variables.

## Estado operativo y alcance

| Aspecto | Volcánicas | Plutónicas |
| --- | --- | --- |
| Modelo adoptado v5 | HistGradientBoosting balanced15 | RandomForest reference_leaf3 |
| Variables | 12 | 41 |
| Muestras elegibles | 1.725 | 976 |
| Macro F1 medio interno del selector | 0,635 | 0,389 |
| Evaluación externa independiente | Pendiente | Pendiente |

Las métricas describen el procedimiento interno de selección; no una evaluación
externa de los pesos reajustados. Las probabilidades no tienen calibración externa
demostrada. El desempeño plutónico exige límites visibles y revisión por clase.
La clasificación modal QAPF conserva su función formal.

PLU utiliza GeoNormPy 1.1.0, Verma2003 versión 1.0, fracción férrica fija 0,15,
calcita como supuesto y Ap más FAp. No se utilizan coordenadas como predictores.
La población fuente conserva 2.755 IDs; los 54 registros fuera de la población
común se mantienen en la fuente y en los informes de cobertura.

Las comparaciones anidadas v3/v4 y los diagnósticos de estabilidad v5 ya se
realizaron. No deben seguir apareciendo como trabajo sin ejecutar. El holdout
histórico se consultó y participó en reajustes posteriores: no es una nueva prueba
ciega. La validación por grupos no demuestra transferencia geográfica.

Los exportadores históricos y CURRENT_GENERATION conservan su identidad previa
por compatibilidad. generation_catalog(include_operational=True) añade
operational_adoption para identificar v5 sin modificar el snapshot histórico.

El siguiente paso científico es una evaluación con datos nuevos e independientes.
El [plan de evaluación externa](docs/EXTERNAL_VALIDATION.md) distingue ese trabajo
pendiente de las comprobaciones técnicas que ya se pueden ejecutar.

## Flujo de trabajo

1. Reúne química, etiquetas petrográficas, coordenadas y procedencia.
2. Revisa calidad, nombres e identificadores estables.
3. Calcula variables CIPW con GeoNormPy y, cuando corresponda, contexto espacial.
4. Separa grupos de muestras antes de comparar modelos.
5. Exporta modelos seleccionados, métricas y diagnósticos SHAP reproducibles.

Los productos incluyen tablas limpias, matrices de confusión, métricas, figuras
de importancia y paquetes de modelos. Las variables CIPW y las uniones
espaciales son derivadas; no constituyen observaciones geológicas independientes.

## Fuentes de datos

Las bases originales, tablas intermedias y modelos serializados no se distribuyen
aquí. Obtén los datos de sus proveedores y conserva consultas, fechas y fuentes.

- [GEOROC](https://georoc.eu): las compilaciones de consultas utilizan CC BY-SA
  4.0 y requieren atribución a GEOROC y las referencias originales de muestras.
  Los conjuntos del Data Repository pueden tener condiciones propias de su
  proveedor. Consulta la [guía oficial](https://georoc.eu/georoc/cite.asp).
- [INGEMMET / GEOCATMIN](https://geocatmin.ingemmet.gob.pe): consulta los
  servicios institucionales y las condiciones de cada conjunto; cita INGEMMET.
  Este repositorio no redistribuye la base ni concede derechos sobre datos ajenos.

Usa Dataset local, excluido de Git, o GEONORMML_DATASET_PATH. Regenerar tablas
y entrenar son operaciones explícitas, no parte de esta integración.

## Preparación y ejecución

GeoNormML y GeoNormPy son repositorios separados. Python 3.11 es el entorno
comprobado; prepara un entorno aislado usando los recursos existentes. El
archivo requirements.txt instala el proyecto y GeoNormPy 1.1.0 publicado.
constraints-py311.txt registra las dependencias científicas. No se necesita
una carpeta vecina; requirements-local.txt permite ese desarrollo opcional.

~~~powershell
python -m pip install -r requirements.txt
~~~

Para instalar directamente el paquete y las herramientas de desarrollo:

~~~powershell
python -m pip install -c constraints-py311.txt -e ".[dev]"
~~~

Para reproducir el pipeline histórico, con datos autorizados y rutas correctas:

~~~powershell
python -m scripts.clean_dataset --input "<spatial v5.xlsx>" --reference "<curated v4.xlsx>"
python -m scripts.build_modeling_artifacts
python -m scripts.validate_models
python -m scripts.export_official_models
python -m scripts.generate_shap_plots
~~~

La limpieza produce el libro curado, CSV, auditoría de repeticiones, tabla de
revisión y manifiesto SHA-256. No sobrescribe entradas ni salidas existentes.
GEONORMML_DATASET_PATH selecciona otro libro auditado y GEONORMML_ARTIFACTS_DIR
redirige productos. La política restricted_experiment exige una salida separada.
La exportación normal incluye los dos modelos geoquímicos; --include-spatial
añade modelos experimentales que requieren validación geográfica independiente.

## Documentación y organización

- [Trazabilidad](docs/metodologia/dataset_traceability.md).
- [Pipeline](docs/metodologia/modeling_pipeline_bootstrap.md).
- [Variables petrológicas](docs/metodologia/implemented_petrological_features.md).
- [Variables espaciales y SHAP](docs/metodologia/implemented_spatial_features_and_shap.md).
- [Decisión de modelos](docs/revisiones/feature_context_experiment_and_final_model_decision.md).

src/geonormml contiene los módulos reutilizables; scripts organiza las etapas;
docs separa metodología, revisiones, informes, publicaciones y figuras.
poster_cpg23 conserva material de congreso. Dataset, artifacts, entornos,
cachés y credenciales quedan fuera del control de versiones.

## Estado y límites

La versión 0.1.0 es una base de investigación activa. El rendimiento depende
del conjunto, las etiquetas y la partición documentados. Separar réplicas entre
folds no acredita transferencia espacial. Las pruebas de limpieza, exportación
y serialización no sustituyen validación geológica externa.

## Licencia y contacto

[GNU GPL v3](LICENSE). Jordan Zavaleta — GisGeo Dev.
[Correo](mailto:jordanzav@gisgeo.dev) · [Sitio web](https://gisgeo.dev).

## Comparación CIPW e integración entre equipos

La laptop aporta compare_cipw_profiles.py y report_cipw_profile_comparison.py.
El primero ajusta modelos experimentales: no es un verificador de solo lectura.
El segundo verifica predicciones guardadas y genera el informe fechado del
26 de octubre, no un informe genérico para experimentos futuros.
Ambos admiten --help y requieren datos y artefactos locales de procedencia fiable.
No se ejecutaron experimentos ni se sustituyeron modelos durante esta integración.
[Registro de integración](docs/revisiones/integracion_dos_pc_20261026.md).
