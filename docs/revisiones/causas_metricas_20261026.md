# Qué explica la diferencia de métricas: comparación controlada

El resumen Legacy se reproduce exactamente sobre la base curada actual usando CV estratificada por filas: VOL combined_core XGBoost da CA 0,8049886621 y MCC 0,7130564619; PLU oxides_core RandomForest da CA 0,5812310797 y MCC 0,4815212688. Esos son los valores del resumen redondeados. No fue necesario cambiar la química ni recalcular CIPW.

La explicación anterior de que las métricas bajaron principalmente por agrupar muestras era demasiado general. La comparación nueva demuestra un efecto importante en volcánicas, pero no explica así el resultado plutónico. Se corrige esa conclusión.

## Diseño y alcance

Se mantuvieron la base de 2.755 IDs, los óxidos y normas almacenadas, los preprocesadores, los algoritmos y sus hiperparámetros actuales. Se compararon cuatro protocolos para cada combinación de dominio, variables y algoritmo: CV estratificada por filas o por grupos, sobre el entrenamiento registrado o sobre todo el dominio curado. Cinco folds y semilla 42 en todos los casos. Se ajustaron 60 estimadores temporales; no se exportó ninguno.

En PLU se evaluaron las dos familias implicadas en la discrepancia histórica, oxides_core y combined_core, con RandomForest. En VOL se mantuvo combined_core con XGBoost. La imputación se ajustó únicamente dentro de cada fold de entrenamiento.

Los escenarios de base completa reutilizan el holdout histórico para reconstruir la evaluación antigua. Son diagnósticos retrospectivos, no una nueva evaluación independiente ni una autorización para seleccionar modelos por sus resultados sobre ese holdout.

## Resultados de exactitud

| Dominio / variables | Todas las muestras, CV filas | Todas, CV grupos | Entrenamiento, CV filas | Entrenamiento, CV grupos |
| --- | --- | --- | --- | --- |
| VOL combined_core, XGBoost | 80,4989 % | 76,3039 % | 80,1418 % | 76,2411 % |
| PLU combined_core, RandomForest | 56,8113 % | 57,7195 % | 54,7980 % | 55,0505 % |
| PLU oxides_core, RandomForest | 58,1231 % | 57,5177 % | 56,3131 % | 56,3131 % |

La base completa incluye 1.764 VOL y 991 PLU. El entrenamiento registrado incluye 1.410 VOL y 792 PLU. Las dos cifras de CV agrupada vigente se reprodujeron exactamente. Las métricas completas, incluidos F1 macro y MCC, están en [la evidencia JSON](metric_protocols_20261026.json).

### Volcánicas

Sobre el mismo entrenamiento, pasar de filas a grupos cambia 80,1418 % a 76,2411 %: una diferencia de menos 3,9007 puntos porcentuales. En la CV por filas hubo entre 25 y 31 grupos compartidos entre entrenamiento y validación por fold; en la agrupada no hubo ninguno.

Cambiar de toda la base a entrenamiento, manteniendo CV por filas, cambia 80,4989 % a 80,1418 %: menos 0,3570 puntos. En esta trayectoria concreta la agrupación explica la mayor parte de la diferencia respecto al resumen. No equivale a demostrar ese efecto para todas las semillas, algoritmos o poblaciones.

### Plutónicas

Sobre el mismo entrenamiento y combined_core, agrupar aumenta ligeramente la exactitud: 54,7980 % a 55,0505 %. Por tanto, no se puede atribuir su bajada a la eliminación de fuga por grupos como explicación principal en este experimento.

Una trayectoria que conecta el resumen Legacy con la evaluación vigente es:

1. Base completa, oxides_core, CV filas: 58,1231 %.
2. Base completa, combined_core, CV filas: 56,8113 %; cambio de variables, menos 1,3118 puntos.
3. Entrenamiento, combined_core, CV filas: 54,7980 %; cambio de población evaluada, menos 2,0133 puntos.
4. Entrenamiento, combined_core, CV grupos: 55,0505 %; agrupación, más 0,2525 puntos.

Son diferencias observadas bajo una trayectoria y particiones fijas. El orden de los cambios puede alterar sus aportes por interacción; no constituyen porcentajes causales universales ni estimaciones de significancia.

El control oxides_core sobre entrenamiento agrupado obtiene 56,3131 %, frente a 55,0505 % de combined_core. Su F1 macro es 0,359412 y 0,358407 respectivamente. Es una alternativa más sencilla que merece comparación de estabilidad, pero esta corrida y un holdout ya observado no bastan para declarar una mejora externa o reemplazar silenciosamente el modelo desplegado.

## Qué queda resuelto y qué no

- Se reconstruyen las cifras del resumen Legacy de ambos dominios. No se demuestra que GeoNormPy haya provocado una caída: aquí no se cambió ni recalculó la norma CIPW.
- La discrepancia del resumen con la CV vigente ya tiene un contraste controlado de variables, población y agrupación.
- Las cifras distintas del tótem, como 0,806 / 0,615 y sus variantes espaciales, pertenecen a otros materiales históricos. No se afirma haberlas reconstruido con esta auditoría.
- No se cambió la base, no se eliminaron muestras y los archivos de Dataset y artifacts conservaron sus hashes. Los productos de diagnóstico permanecen separados.
- La generación Legacy presentada en el XXIII Congreso Peruano de Geología se conserva. La referencia al trabajo técnico está en [CITATION.cff](../../CITATION.cff).

## Reproducción

Con el entorno validado, lanzador y bloqueo de trabajo pesado:

    python -m scripts.audit_metric_protocols --output CARPETA_NUEVA

La orden requiere los datos locales y la evaluación registrada. Rechaza salidas existentes, comprueba cobertura de predicciones fuera de fold, detecta grupos compartidos y comprueba que la CV vigente se reproduzca. Registra predicciones, hashes y resultados; no guarda modelos. No necesita GeoNormPy para recalcular ninguna norma.
