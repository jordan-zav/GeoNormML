<p align="center"><a href="README.md">English</a> · <strong>Español</strong></p>

# GeoNormML

Decisión operativa del 27 de octubre: PetroPyQAPF adopta los pesos congelados de la selección final v5, HistGradientBoosting volcánico y RandomForest plutónico. Macro F1 interno del selector: 0,635 / 0,389; evaluación externa pendiente. Se conserva Legacy. Véase la [decisión y sus límites](docs/revisiones/adopcion_petropyqapf_v5_20261027.md); no reemplaza los resultados históricos del CPG XXIII ni acredita validez externa.

El [estudio de alternativas y sensibilidad a las particiones](docs/revisiones/estabilidad_y_alternativas_20261027.md)
compara siete familias de algoritmos, tres semillas, tres frente a cinco folds
externos y diagnósticos geográficos. ExtraTrees alcanza el mayor macro F1 medio
entre las familias probadas, con diferencias pequeñas y límites importantes al
bloquear geográficamente. Los pesos nuevos siguen experimentales; no se cambian
los modelos predeterminados de producción.

La [comparación ampliada por dominio](docs/revisiones/comparacion_ampliada_20261027.md)
ya incluye los tres algoritmos, las once familias de variables y una búsqueda
acotada de configuraciones dentro de la validación anidada. No demuestra una
mejora general ni justifica promover automáticamente pesos nuevos. Se mantienen
XGBoost como familia de referencia volcánica y RandomForest como plutónica.

La [generación candidata actualizada](docs/revisiones/generacion_candidata_v3_20261026.md)
compara los tres perfiles de GeoNormPy 1.1.0 mediante validación anidada por grupos.
Selecciona RandomForest con óxidos para volcánicas y XGBoost con Verma 2003 para
plutónicas. Sigue experimental, pendiente de validación externa; la base vigente
se conserva.

La [auditoría de candidatos](docs/revisiones/auditoria_candidatos_20261027.md)
verifica los resultados v3 y documenta que faltaron SVM_PCA y nueve familias de
variables. La comparación ampliada aborda esa cobertura pendiente sin alterar
la evidencia histórica de v3.

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
de 1.1.0 no es idéntica al motor anterior. El baseline ML vigente conserva dos
modelos combined_core, con evaluación por grupos y holdout reservado.
[Referencia al trabajo técnico y cita del software](CITATION.cff) · [CPG XXIII](https://congresosgp.org.pe/).

Consulta la [decisión de versiones y métricas](docs/revisiones/modelos_legacy_y_vigentes.md).

La [comparación controlada](docs/revisiones/causas_metricas_20261026.md) reproduce
el resumen Legacy y separa el efecto de agrupación, población y variables.

## Metodología vigente y crítica

La referencia actual es una base congelada de 2.755 IDs, con su hash y manifiesto,
dos dominios separados y CV estratificada por grupos dentro del entrenamiento.
Los grupos reúnen dependencias conocidas por identificadores de laboratorio y
química mayor idéntica. La imputación se ajusta dentro de cada fold. Ambos
baselines desplegados usan combined_core: XGBoost en VOL y RandomForest en PLU.
Son referencias reproducibles; no se ha demostrado que sean las mejores
alternativas posibles.

| Dominio | Muestras en CV / holdout histórico | Exactitud CV por grupos | F1 macro CV | Exactitud holdout histórico |
| --- | --- | --- | --- | --- |
| VOL | 1.410 / 354 | 76,24 % | 0,644 | 77,40 % |
| PLU | 792 / 199 | 55,05 % | 0,358 | 58,29 % |

La CV y el holdout son evaluaciones diferentes: no se mezclan ni se elige la
cifra mayor para representar el modelo. El holdout histórico ya se ha consultado
y se reutilizó en diagnósticos retrospectivos sobre la base completa. Sus cifras
se conservan como resultados históricos de modelos fijados; no constituyen una
prueba ciega nueva para elegir o promocionar alternativas.

**Crítica del trabajo Legacy y de las conclusiones actuales:**

- La CV por filas del resumen Legacy es reproducible, pero permite grupos
  relacionados entre entrenamiento y validación. En VOL, sobre el mismo
  entrenamiento, da 80,14 % frente a 76,24 % por grupos. Es una señal de
  optimismo bajo ese protocolo, no una prueba de que todas las cifras históricas
  sean inválidas.
- En PLU, agrupar cambia 54,80 % a 55,05 % con las mismas muestras y variables.
  La diferencia respecto al resumen incluye población y selección de variables;
  no corresponde explicarla principalmente por fuga de grupos ni por un fallo
  de GeoNormPy.
- El F1 macro plutónico de 0,358 exige revisar desempeño por clase. La exactitud
  global no demuestra reconocimiento sólido de todas las litologías ni permite
  atribuir el límite observado únicamente a una causa geológica.
- Controlar estos grupos no elimina toda dependencia espacial. Ni el mapa ni
  una mejora en CV demuestran transferencia a otra región. Los modelos espaciales
  permanecen experimentales.
- Los mejores cierres numéricos de perfiles CIPW nuevos no prueban una mejora ML.
  La procedencia del perfil de entrenamiento histórico está incompleta: debe
  registrarse antes de cambiar las normas consumidas por un clasificador.

**Protocolo para la siguiente generación, todavía pendiente de ejecución:**

1. Fijar población, grupos, clases, perfil y versión CIPW, política de hierro,
   variables, métricas y criterios de selección antes de comparar resultados.
2. Comparar oxides_core, combined_core y los perfiles candidatos sobre las mismas
   observaciones elegibles y folds; conservar todas las filas en los registros
   de cobertura y explicar cualquier exclusión de la evaluación común.
3. Realizar selección de variables e hiperparámetros en CV interna por grupos y
   estimar su rendimiento en CV externa por grupos. Mantener todo preprocesamiento
   aprendido dentro del entrenamiento de cada fold.
4. Informar exactitud, F1 macro, MCC, confusión y cobertura por clase, junto con
   estabilidad entre particiones. La corrida de semilla única existente no es
   una prueba de significancia ni una estimación completa de incertidumbre.
5. Obtener una evaluación independiente sin consultar durante la selección;
   para afirmaciones geográficas, usar regiones o bloques separados y, cuando
   sea posible, fuentes externas. No volver a llamar ciego al holdout conocido.
6. Promover un modelo solo tras esa evaluación y conservar versiones, resultados
   y contrato de entrada. Un reajuste final con toda la base no genera por sí
   mismo una nueva métrica de validación.

[Evidencia de los 60 ajustes controlados](docs/revisiones/causas_metricas_20261026.md)
· [CV con grupos](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)
· [Separación de selección y evaluación](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

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
