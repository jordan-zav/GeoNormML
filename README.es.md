<p align="center"><a href="README.md">English</a> · <strong>Español</strong></p>

# GeoNormML

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

GeoNormML y GeoNormPy son repositorios hermanos. Python 3.11 es el entorno
comprobado; prepara un entorno aislado usando los recursos existentes. El
archivo requirements.txt instala el proyecto y resuelve GeoNormPy desde
../GeoNormPy. constraints-py311.txt registra las dependencias científicas.

~~~powershell
python -m pip install -r requirements.txt
~~~

Para desarrollo del núcleo ML sin calcular CIPW:

~~~powershell
python -m pip install -c constraints-py311.txt -e ".[dev]"
~~~

Con los datos locales autorizados y las rutas correctas:

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
