# GeoNormML

- Trabajar en esta copia; conservar intacto el proyecto original de Google Drive.
- `Dataset/` y `artifacts/` son locales y están excluidos de Git. No subir datos,
  muestras, modelos serializados ni credenciales como parte de cambios de código.
- La base oficial conserva las 2.755 muestras del v4 normalizado/consistente:
  `Dataset/Filtered/final/GeoNormML_training_curated.xlsx`.
  `GeoNormML_training_clean.xlsx` (2.651 filas) es un experimento descartado como base oficial.
  No excluir IDs curados por coincidencia química, balance CIPW o etiquetas en conflicto
  sin una decisión explícita: registrar observaciones en `retained_review`.
  El informe y los registros de revisión están junto al archivo. No sobrescribirlo:
  para otra depuración usar un nombre nuevo y mantener el manifiesto de hashes.
- Consultar `docs/curated_baseline_correction_20260920.md` antes de citar conteos o métricas.
- Validar con `python -m pytest -q`, `python -m ruff check src scripts tests`
  y `python -m pip check`. Dependencias comprobadas en `constraints-py311.txt`.
- Los modelos espaciales son experimentales. Agrupar réplicas entre folds no
  equivale a validación espacial independiente.
