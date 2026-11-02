# Integración versionada de GeoNormML y GeoNormPy

Revisión técnica del 2 de noviembre de 2026. Los proyectos conservan repositorios
separados. No se ejecutaron nuevos ajustes de modelos de investigación ni se
modificó la base curada.

## Cambios

GeoNormML declara geonormpy==1.1.0 en pyproject.toml y en las restricciones del
entorno. La instalación normal deja de exigir ../GeoNormPy; el archivo
requirements-local.txt mantiene explícitamente esa opción de desarrollo.

Se añade una prueba pública sintética de los tres perfiles reales hasta variables,
preprocesamiento y predicción serializada. Otra comprobación importa ambos wheels
en un proceso aislado fuera de los checkouts. La CI instala la versión publicada
y repite el recorrido con el wheel descargado de PyPI.

El entorno editable local declaraba GeoNormPy 1.0.0 aunque importaba código 1.1.0.
Se regeneró su metadata. La prueba de contrato exige ahora que la versión de
ejecución y la versión instalada coincidan con la especificación congelada.

La documentación distingue v5 operativo de los baselines y comparaciones
históricas. generation_catalog() conserva su snapshot por defecto;
include_operational=True expone la adopción v5 sin cambiar los exportadores.
Los artefactos y materiales de publicación anteriores conservan su identidad.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| Suite GeoNormML | 76 aprobadas, 13 omitidas por ser opcionales de datos privados o herramientas de investigación |
| Ruff de GeoNormML | Sin incidencias |
| pip check del entorno GeoNormML | Sin dependencias incompatibles |
| Integración de ambos wheels fuera de los checkouts | 5 aprobadas |
| Suite GeoNormPy | 385 aprobadas; 3 comprobaciones de wheel ejecutadas aparte y aprobadas |
| Suite desde el archivo fuente GeoNormPy extraído | 385 aprobadas, 3 omitidas de wheel |
| Metadata, licencia y Twine estricto | Wheel y archivo fuente aprobados |
| CI GeoNormPy | Python 3.9, 3.11 y 3.14 aprobados |

La [release GeoNormPy 1.1.0](https://github.com/jordan-zav/GeoNormPy/releases/tag/v1.1.0)
y la [versión en PyPI](https://pypi.org/project/geonormpy/1.1.0/) contienen los
mismos artefactos, comprobados mediante SHA-256. La publicación procede del
[workflow verificado](https://github.com/jordan-zav/GeoNormPy/actions/runs/41506620023).

## Límite científico

Estas comprobaciones no aportan otra evaluación externa, calibración de
probabilidades ni evidencia de transferencia geográfica. El clasificador
sintético solo comprueba conexiones de software. La evaluación independiente
requiere datos nuevos, procedencia comprobada y un protocolo fijado antes de
observar sus predicciones; véase el [plan](../EXTERNAL_VALIDATION.md).
