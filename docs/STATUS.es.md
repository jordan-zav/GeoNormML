# GeoNormML: estado vigente y pendientes

[English](STATUS.md) · [Índice documental](README.md)

Actualizado el 2 de noviembre de 2026.

## Qué está operativo

PetroPyQAPF adoptó los pesos congelados de la selección final v5 el 27 de octubre:
HistGradientBoosting balanced15 para VOL, con 12 variables y 1.725 observaciones
elegibles; RandomForest reference_leaf3 para PLU, con 41 variables y 976
observaciones elegibles. La fuente conserva sus 2.755 IDs; los otros 54 registros
siguen en la base y en los informes de cobertura.

PLU utiliza GeoNormPy 1.1.0, perfil Verma2003 1.0, fracción férrica fija 0,15,
calcita como supuesto y Ap más FAp. El macro F1 interno del selector es
0,635 / 0,389: describe el procedimiento de selección, no una evaluación externa
de los pesos finales. Véase la [decisión operativa](revisiones/adopcion_petropyqapf_v5_20261027.md).

## Qué se cerró técnicamente

La CLI y la API Python incorporan rutas portables, manifiestos JSON, comprobación
de hash/entorno, carga explícita de modelos de confianza, selección del contrato
de entrada, rechazos por fila y salida CSV. El ejemplo sintético se genera solo
en una carpeta solicitada. Véase la [guía de uso](USAGE.es.md).

La [versión 0.1.0 está publicada en PyPI](https://pypi.org/project/geonormml/0.1.0/)
desde el 2 de noviembre de 2026. Trusted Publishing funcionó desde v0.1.0 y los
hashes del wheel y archivo fuente coinciden con los artefactos verificados.
También se comprobó la instalación y el comando descargados de PyPI. No se
incluyen datos ni pesos privados. Para futuras versiones, la publicación sigue
siendo explícita; preparar artefactos no los sube. Véase el [procedimiento](PUBLISHING.md).

- Dependencia exacta geonormpy==1.1.0 en metadata y restricciones del entorno.
- Instalación normal sin carpeta vecina; requirements-local.txt queda para
  desarrollo con ambos checkouts editables.
- Pruebas sintéticas de los tres perfiles CIPW hasta variables, preprocesamiento,
  predicción y recuperación del pipeline serializado.
- Comprobación de coherencia entre versión de ejecución y metadata instalada.
- CI con el motor publicado, sin necesitar dataset ni pesos privados.
- Verificación de ambos wheels fuera de los checkouts mediante
  scripts/check_installed_pair.py, incluida en CI con el wheel descargado de PyPI.

El clasificador ficticio de las pruebas comprueba conexiones de software; no
aporta una métrica geológica ni sustituye los modelos de investigación.

## Qué se conserva

Los exportadores históricos y CURRENT_GENERATION mantienen curated_grouped_v2.
generation_catalog() conserva el snapshot de publicación. La opción
include_operational=True añade la información de adopción v5 sin sobrescribirlo.
No se cambian silenciosamente perfiles, pesos ni valores de entrada históricos.

Legacy del congreso, v2, v3, v4 y v5 tienen identidades y evidencias distintas.
Las comparaciones anidadas y los diagnósticos de estabilidad ya se ejecutaron.
El holdout histórico se consultó y reutilizó: no vuelve a ser una prueba ciega.

## Qué falta

La evaluación externa independiente, la calibración externa de probabilidades y
la demostración de transferencia regional siguen pendientes. El rendimiento
plutónico requiere atención por clase y límites visibles. Conseguir otra base
independiente y ejecutar un protocolo fijado antes de observar sus resultados es
prioritario frente a repetir ajustes sobre los mismos datos.

El [plan de evaluación externa](EXTERNAL_VALIDATION.md) establece los requisitos.
Los modelos, la base curada y las métricas congeladas no se modificaron durante
esta integración.
