# GeoNormML

- Trabajar en esta copia; conservar intacto el proyecto original de Google Drive.
- `Dataset/` y `artifacts/` son locales y están excluidos de Git. No subir datos,
  muestras, modelos serializados ni credenciales como parte de cambios de código.
- El dataset depurado es `Dataset/Filtered/final/GeoNormML_training_clean.xlsx`.
  Su informe y los registros excluidos están junto al archivo. No sobrescribirlo:
  para otra depuración usar un nombre nuevo y mantener el manifiesto de hashes.
- Consultar `docs/audit_20260920.md` antes de citar conteos o métricas históricas.
- Validar con `python -m pytest -q`, `python -m ruff check src scripts tests`
  y `python -m pip check`. Dependencias comprobadas en `constraints-py311.txt`.
- Los modelos espaciales son experimentales. Agrupar réplicas entre folds no
  equivale a validación espacial independiente.
