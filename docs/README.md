# Documentación de GeoNormML

La [revisión controlada de las métricas](revisiones/causas_metricas_20261026.md)
reconstruye el resumen Legacy y separa el efecto de grupos, población y variables.

La [decisión Legacy y baseline vigente](revisiones/modelos_legacy_y_vigentes.md)
es la referencia actual para modelos, métricas y alcance. El trabajo técnico
presentado en el XXIII Congreso Peruano de Geología se conserva como
GeoNormPy / GeoNormML Legacy.

Empieza por la [guía de trabajo](GUIA_DE_TRABAJO.md) y la
[rectificación de la base oficial](revisiones/curated_baseline_correction_20260920.md).
La base vigente conserva 2.755 muestras; las cifras de informes anteriores
deben leerse junto con esa rectificación.

La [revisión del 25 de octubre](revisiones/organizacion_y_revision_20261025.md)
registra la organización, la corrección de Windows y las verificaciones locales.

| Carpeta | Contenido |
| --- | --- |
| [metodologia](metodologia/) | Trazabilidad, preparación, variables y uso de cartografía |
| [revisiones](revisiones/) | Auditorías, correcciones y decisiones experimentales |
| [informes](informes/) | Informes históricos en Markdown; Word y PDF se conservan localmente |
| [publicaciones](publicaciones/) | Borradores Markdown para el congreso; documentos binarios locales |
| docs/*.jpg | Ilustraciones fuente ya versionadas |

## Lectura recomendada

1. [Corrección de la base oficial](revisiones/curated_baseline_correction_20260920.md).
2. [Trazabilidad del dataset](metodologia/dataset_traceability.md).
3. [Preparación del modelado](metodologia/modeling_pipeline_bootstrap.md).
4. [Variables petrológicas](metodologia/implemented_petrological_features.md).
5. [Variables espaciales y SHAP](metodologia/implemented_spatial_features_and_shap.md).
6. [Decisiones sobre modelos](revisiones/feature_context_experiment_and_final_model_decision.md).
7. [Catálogo de scripts](../scripts/README.md).

## Documentos históricos

El informe de agosto de 2026 describe 2.887 filas procedentes de un cruce
espacial. No representa 2.887 muestras independientes. La revisión posterior
restauró 2.755 IDs y conservó las advertencias de calidad sin excluir muestras.
El experimento de 2.651 filas también es histórico.

Los borradores y materiales de congreso conservan sus cifras originales.
Revisar su población, partición y fecha antes de reutilizarlos. El archivo
paper_geonormpy_geonormml_cpg.md está vacío; el borrador con contenido es
[paper_geonormpy_geonormml_cpg_xxiii.md](publicaciones/paper_geonormpy_geonormml_cpg_xxiii.md).

Los enlaces absolutos antiguos a Google Drive documentan fuentes históricas;
su disponibilidad en esta PC no está garantizada. No se trasladaron ni
modificaron sus originales.

## Integración entre equipos

[Registro y comprobaciones](revisiones/integracion_dos_pc_20261026.md).
