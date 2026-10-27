# GeoNormPy y GeoNormML: Legacy y baseline vigente

La [comparación controlada de protocolos](causas_metricas_20261026.md) reproduce
las métricas del resumen Legacy y precisa las causas: la agrupación explica una
parte importante en VOL; en PLU deben distinguirse población y variables.

Esta decisión resuelve las diferencias entre el trabajo del congreso y los modelos del repositorio. La generación anterior se conserva como **GeoNormPy / GeoNormML Legacy**, presentada como trabajo técnico en el **XXIII Congreso Peruano de Geología**. Sus resultados permanecen históricos, sin atribuirlos a un modelo posterior.

Presented as a technical paper at the XXIII Peruvian Geological Congress.

## Generaciones y decisiones adoptadas

| Identidad | Estado y uso |
| --- | --- |
| GeoNormPy / GeoNormML Legacy — CPG XXIII | Trabajo técnico presentado. Conserva las selecciones y evaluaciones de sus documentos originales. |
| GeoNormPy 1.0.0 Legacy | Versión anterior publicada del motor. Se conserva su identidad; no se declara equivalente exacta a 1.1.0. El tótem histórico anunciaba 0.1.1, otro corte temporal que también se conserva. |
| Compatibilidad Legacy corregida, extended_cipw_v3 3.1 | Perfil de 1.1.0 con corrección numérica de piroxenos. No es una reproducción bit a bit de GeoNormPy 1.0.0. |
| Verma 2003 y Pruseth 2009 | Perfiles determinísticos nuevos. Su mejor contabilidad de componentes no demuestra mayor precisión de un clasificador ML. |
| GeoNormML curated_grouped_v2 | Baseline vigente con 2.755 IDs, validación por grupos y holdout reservado. Dos modelos oficiales, ambos combined_core: VOL XGBoost y PLU RandomForest. |
| Modelos espaciales y otras combinaciones | Comparaciones secundarias o experimentales. No se convierten en oficiales por usar una familia de variables permitida. |

El resumen Legacy seleccionó oxides_core para plutónicas, mientras que el tótem incluyó otro experimento con combined_core y contexto espacial. Ambos documentos son históricos: no constituyen una sola corrida. La generación vigente se identifica por sus artefactos y evaluación por grupos. Se conserva su selección actual sin presentar la diferencia de cifras como mejora del mismo experimento.

Los estimadores exactos del resumen del congreso no se localizaron entre los artefactos actuales. Su entrada Legacy es documental y no se ofrece como inferencia disponible: no se cambia el nombre de un estimador reciente para aparentar que es el original. Los modelos archivados del experimento restrictivo de 2.651 filas tampoco son los modelos del congreso ni la base oficial.

## Cifras que deben usarse para la generación vigente

La fuente es artifacts/validation/baseline_validation.json, contrastada con las predicciones reservadas, su partición y el hash de la base curada. El snapshot público sin datos ni modelos está en [current_baseline.evidence.json](../../poster_cpg23/configs/current_baseline.evidence.json). Los exportadores comparten la definición de modelos de src/geonormml/catalog.py.

| Dominio | Entrenamiento CV | CA CV por grupos | AUC macro CV | MCC CV | Holdout | Exactitud holdout |
| --- | --- | --- | --- | --- | --- | --- |
| VOL | 1.410 | 0,762411 | 0,937558 | 0,645398 | 354 | 0,774011 |
| PLU | 792 | 0,550505 | 0,832846 | 0,441484 | 199 | 0,582915 |

La CV se calcula solo dentro del entrenamiento. La evaluación reservada contiene 553 muestras, sin grupos compartidos con entrenamiento. Los estimadores finales exportados se reajustan con todas las muestras y no se validan contra sus propios datos de ajuste. Estas métricas no acreditan transferencia geográfica externa.

El número de muestras vigente es 2.755: 1.764 VOL y 991 PLU, con 19 clases. Las 2.887 filas de una versión espacial incluían 132 repeticiones. La base de 2.651 filas permanece como experimento restrictivo archivado. No se descartan muestras adicionales para igualar narrativas antiguas.

La presentación histórica no describe el filtro actual al declarar aceptación estricta de Sum_Oxs entre 98,5 y 101: 1.962 filas actuales quedan fuera de ese intervalo; 1.220 carecen de LOI. Esos hechos se publican como completitud y revisión, sin inferir que todo dato fuera del intervalo sea inválido o que todas las exclusiones históricas se debieran al mismo criterio. Tampoco se afirma transferencia universal ni un mecanismo de Benioff demostrado por el aumento de una métrica.

## Contrato CIPW y modelos posteriores

Los modelos vigentes contienen normas históricas cuyo perfil y versión de motor no quedaron registrados al entrenar. El catálogo expone explícitamente esa ausencia; no inventa una procedencia. Hasta una reevaluación controlada, no deben sustituirse sus entradas normativas por otro perfil CIPW.

La comparación nueva conserva todas las filas: compatibilidad produce 2.720 asignaciones completas, 20 incompletas y 15 entradas con mayores incompletos; Verma produce 2.740 completas y 15 con mayores incompletos; Pruseth produce 2.721 completas, 19 fuera de alcance y 15 con mayores incompletos. Es el contrato común documentado, sin NiO ni LOI como entradas normativas. Los componentes libres y las correcciones firmadas de F y oxígeno deben conservarse al interpretar el balance.

La migración siguiente debe registrar perfil y versión del motor, política de hierro, carbonato, unidades, tratamiento de apatita, hash de la base, grupos, columnas y dependencias. Comparará las mismas particiones sin sobrescribir los modelos actuales; solo después podrá promoverse una nueva generación.

## Publicación y reproducción

Las configuraciones JSON de póster vigentes usan cifras del snapshot verificado y figuras de artifacts/validation. Los generadores antiguos Python e Illustrator se conservan para reproducción Legacy y exigen GEONORMML_ALLOW_LEGACY_POSTER=1. No son la ruta para anunciar resultados vigentes. No se alteraron los originales del congreso en Google Drive.

Para crear evidencia nueva, desde el lanzador y el entorno del proyecto:

    python -m scripts.reconcile_publication --output RUTA_NUEVA/snapshot.json

Este comando verifica los hashes, las etiquetas, la población reservada y sus métricas antes de producir el JSON. No carga, entrena ni reemplaza estimadores y rechaza una salida existente. Las cifras futuras deben generar una nueva evidencia, no editarse a mano para mejorar un resultado.

El visor geoespacial será un explorador de muestras, particiones, QA/QC y predicciones. Dibujar un mapa no modifica los predictores del baseline ni valida un modelo espacial. PetroPyQAPF conservará la autoridad modal y el cifrado de recursos y modelos al incorporar estas identidades.
