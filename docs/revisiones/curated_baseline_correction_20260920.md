# Rectificación: base curada oficial de 2.755 muestras

La base oficial es la versión v4 normalizada/consistente de **2.755 muestras**:
1.764 volcánicas y 991 plutónicas, distribuidas en 19 clases. La depuración a
2.651 fue un criterio adicional introducido durante la revisión del código;
no correspondía sustituir con ella la base previamente curada. Se revierte
esa decisión sin modificar los originales ni borrar el experimento anterior.

## Reconstrucción y controles

| Etapa | Filas | IDs únicos |
| --- | ---: | ---: |
| v3 tras el filtro de calidad original | 2.755 | 2.755 |
| v4 consistente | 2.755 | 2.755 |
| v5 tras el cruce espacial defectuoso | 2.887 | 2.755 |
| Base oficial restaurada | **2.755** | **2.755** |

Se colapsan únicamente las 132 repeticiones de `ID_Final` añadidas por el
cruce espacial. Para las 132 muestras con varias franjas posibles, el atributo
ambiguo queda vacío y las alternativas se registran en `Metal_Belt_Candidates`.

Antes de escribir la base nueva, se verificó que todos sus IDs y las 73
columnas originales restantes coinciden con v4: química, coordenadas, nombres
de roca, minerales normativos y metadatos. No se renormalizaron análisis,
recalcularon normas, cambiaron etiquetas ni descartaron muestras originales.
Los hashes y la lista de columnas verificadas están en el manifiesto local.

Las **104 observaciones adicionales permanecen dentro de la base**:

- 80 coincidencias de análisis con IDs curados distintos.
- 14 advertencias por error de balance CIPW superior a 0,10.
- 10 registros con química coincidente y etiquetas contradictorias.

Se muestran en `QC_Review` y en la hoja `retained_review`, sin exclusión.
Coincidir en química no autoriza por sí solo a eliminar un ID ya curado.
Las réplicas siguen agrupadas para evitar que crucen entrenamiento/validación.
Latita vuelve a sus 22 muestras; todas las clases conservan el conteo de v4.

## Archivos locales vigentes

Dentro de `Dataset/Filtered/final/`:

- `GeoNormML_training_curated.xlsx`: base oficial, frecuencias y hojas de auditoría.
- `GeoNormML_training_curated.csv`: las 2.755 muestras.
- `GeoNormML_training_curated_review.csv`: 104 registros conservados para revisión.
- `GeoNormML_training_curated_excluded.csv`: solo las 132 filas espaciales repetidas.
- `GeoNormML_training_curated.audit.json`: política, hashes y comparación con v4.
- `Merge_Filtered_training_ready_v4_consistent.xlsx`: copia intacta de referencia.

El archivo anterior `GeoNormML_training_clean.xlsx` (2.651) se conserva como
experimento restrictivo histórico. Sus modelos, métricas, particiones y figuras
se trasladaron a `artifacts/archive/restricted_2651_20260920/`; no se mezclan
con la evaluación actual. Los datos y modelos continúan excluidos de Git.

## Política del código

`preserve_curated_v1` es el comportamiento predeterminado: una fila por ID,
conservar todas las muestras y emitir advertencias. El filtro anterior solo
se puede ejecutar mediante `--policy restricted_experiment` y requiere otra
ruta de salida. El pipeline rechaza la reutilización accidental de datasets
con la política antigua o restrictiva. `--reference` bloquea la escritura si
faltan IDs o cambian valores de la base de referencia.

Se regeneran particiones, evaluación, modelos, esquema de transferencia,
gráficas SHAP y dashboard con la base restaurada. Las métricas del informe
anterior corresponden únicamente a las 2.651 muestras y quedan deprecadas
como descripción de esta base. Los resultados vigentes se guardan en
`artifacts/validation/baseline_validation.json`, con el hash del dataset.
La evaluación sigue siendo por grupos de muestras, no validación geográfica
externa. No se sustituyen los modelos instalados de PetroPyQAPF.

## Comprobación final

30 pruebas automáticas correctas, Ruff sin errores y dependencias compatibles.
Se verificaron nuevamente los IDs, valores originales, hashes y separación
de grupos entre entrenamiento y holdout. Las particiones guardadas coinciden
con las utilizadas al calcular las métricas.

La validación reserva 553 muestras y usa 2.202 para CV por grupos de cinco
pliegues. Los resultados de la base restaurada son:

| Modelo / dominio | Exactitud CV | Exactitud holdout | F1 macro holdout |
| --- | ---: | ---: | ---: |
| XGBoost / volcánico | 76,24 % | 77,40 % | 0,7092 |
| RandomForest / plutónico | 55,05 % | 58,29 % | 0,3914 |

Los resultados no son directamente comparables con el experimento de 2.651:
la población y su partición son diferentes. El desempeño plutónico continúa
siendo limitado. Los modelos finales se reajustaron sobre toda la base curada;
las cifras anteriores corresponden a modelos separados de evaluación.
