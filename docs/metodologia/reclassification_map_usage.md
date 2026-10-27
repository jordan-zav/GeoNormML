# Uso de la tabla `reclassification_map`

## Archivo

- [`reclassification_map_template.csv`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/processed/reclassification_map_template.csv)

## Propósito

Esta tabla está diseñada para registrar de forma explícita y auditable las decisiones de reclasificación de clases raras antes de aplicarlas al dataset.

No es todavía una tabla de ejecución automática. Es una tabla de decisión.

## Columnas

- `current_class`: clase actual en el dataset normalizado.
- `count`: frecuencia actual en el dataset.
- `below_minimum_20`: indica si la clase está por debajo del umbral mínimo de `20` muestras.
- `proposed_class`: clase sugerida si se decide fusionar.
- `decision_status`: estado de decisión. Sugeridos:
  - `pending`
  - `approved`
  - `rejected`
- `decision_type`: tipo de acción sugerida:
  - `merge`
  - `manual_review`
  - `exclude`
- `confidence`: confianza relativa de la propuesta.
- `review_needed`: si aún conviene revisión manual.
- `justification`: motivo petrográfico o metodológico.
- `source_basis`: base conceptual o fuente de apoyo.
- `notes`: campo libre para tu decisión final.

## Flujo recomendado

1. Revisar fila por fila las clases raras.
2. Marcar `approved` solo cuando estés conforme con la fusión o exclusión.
3. Dejar en `manual_review` las clases donde la química o el contexto importan más que el nombre.
4. Aplicar cambios al dataset únicamente a partir de filas con:
   - `decision_status = approved`
   - `decision_type = merge` o `exclude`
5. Usar `below_minimum_20 = yes` como criterio duro de priorización, ya que tu regla actual exige al menos `20` muestras por clase litológica.

## Ventaja metodológica

Este enfoque separa claramente:

- normalización semántica del nombre;
- reclasificación del target;
- exclusión litológica;
- decisiones pragmáticas por baja frecuencia.

Eso ayuda a que el proyecto no dependa de cambios manuales implícitos y a que cada modificación del target quede trazable.
