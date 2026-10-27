# GeoNormML

- Trabajar en esta copia; conservar intacto el proyecto original de Google Drive.
- Dataset/ y artifacts/ son locales y están excluidos de Git. No subir datos,
  muestras, modelos serializados ni credenciales como parte de cambios de código.
- La base oficial conserva las 2.755 muestras del v4 normalizado/consistente:
  Dataset/Filtered/final/GeoNormML_training_curated.xlsx.
  GeoNormML_training_clean.xlsx (2.651 filas) es un experimento descartado como base oficial.
  No excluir IDs curados por coincidencia química, balance CIPW o etiquetas en conflicto
  sin una decisión explícita: registrar observaciones en retained_review.
  El informe y los registros de revisión están junto al archivo. No sobrescribirlo:
  para otra depuración usar un nombre nuevo y mantener el manifiesto de hashes.
- Consultar docs/revisiones/curated_baseline_correction_20260920.md antes de citar conteos o métricas.
- Validar con python -m pytest -q, python -m ruff check src scripts tests
  y python -m pip check. Dependencias comprobadas en constraints-py311.txt.
- Los modelos espaciales son experimentales. Agrupar réplicas entre folds no
  equivale a validación espacial independiente.

## Recursos locales y conservacion


Antes de cambiar recursos comprueba unidades, instrucciones, remotos, ramas y cambios locales. Actualiza mediante pull con avance rapido y conserva cambios; informa divergencias sin reset ni cambio de rama.
Usa la raiz local D:\DevResources cuando sea valida; si no lo es, solicita elegir otra raiz. Reutiliza SDK y caches compatibles en Shared, separa estado mutable por proyecto y usa Sessions unicas por ejecucion.
Usa DEVRESOURCES_RUN.cmd para comandos de desarrollo; las configuraciones .devresources son locales y no deben subirse. TEMP y TMP se cambian solo para la sesion y sus hijos. Coordina bloqueos por workspace y maximo dos compilaciones pesadas.
No detengas procesos ajenos. No modifiques DriveFS, datos ni sincronizacion de Google Drive. Conserva codigo, datos, autenticacion, claves y enlaces de compatibilidad.
Comprueba rutas y lanzadores antes de consolidar. Antes de cualquier eliminacion presenta candidatos y espera autorizacion expresa; verifica referencias, copias, destinos fisicos e inactividad. No ejecutes limpiezas automaticas durante esta auditoria.
No afirmes compilaciones que no ejecutaste. Los informes Markdown y Word no deben contener backticks.
