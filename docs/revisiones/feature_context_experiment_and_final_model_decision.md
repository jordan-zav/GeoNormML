> **Legacy — GeoNormPy / GeoNormML.** Documento histórico conservado. El trabajo fue presentado como trabajo técnico en el XXIII Congreso Peruano de Geología. Las decisiones y métricas vigentes se describen en [Legacy y baseline vigente](../revisiones/modelos_legacy_y_vigentes.md); no deben mezclarse con las cifras de este documento.

# Experimento con Clase_SiO2 y Serie_Mag y decision final de modelo

## Objetivo

Evaluar si las variables derivadas Clase_SiO2 y Serie_Mag mejoran el desempeno del modelo de clasificacion litologica y decidir si deben incorporarse al esquema oficial de entrenamiento.

## Contexto metodologico

Durante la reconstruccion reproducible del proyecto en Python se decidio que:

- Quality_Flag no debe usarse como predictor.
- Clase_SiO2 y Serie_Mag no debian entrar al benchmark principal sin una prueba explicita, porque ambas variables resumen informacion petroquimica ya contenida en los oxidos y/o en CIPW.
- El baseline oficial recomendado hasta ese momento era:
  - oxides_core
  - cipw
  - combined_core

Posteriormente se ejecuto un experimento controlado para integrar:

- oxides_contextual = oxides_core + Clase_SiO2 + Serie_Mag
- combined_contextual = oxides_core + cipw + Clase_SiO2 + Serie_Mag

El objetivo fue verificar si estas variables contextuales aportaban mejora real o si solo introducian una forma de suavizamiento del problema de machine learning.

## Implementacion del experimento

Se realizaron los siguientes cambios:

- Se calculo Serie_Mag a partir de:
  - Ne >= 1
  - Le >= 1
  - SiO2 < 52 y Alc >= 5
- Se mantuvo Clase_SiO2 como categoria derivada de SiO2.
- Se excluyo Quality_Flag del conjunto predictivo.
- Se adapto el pipeline para manejar variables mixtas:
  - imputacion numerica por mediana
  - imputacion categorica por moda
  - codificacion one-hot para variables categoricas
- Se repitio el benchmark con:
  - RandomForest
  - SVM_PCA
  - XGBoost
  - 5-fold stratified CV
  - entrenamiento separado para VOL y PLU

Resultados guardados en:

- artifacts/ml_benchmark/metrics_summary.csv
- artifacts/ml_benchmark/metrics_summary.txt

## Resultados principales

### Volcanicas

Comparacion mas importante:

- oxides_core + RandomForest
  - CA = 0.8061
  - MCC = 0.7111
- oxides_contextual + RandomForest
  - CA = 0.8084
  - MCC = 0.7152

Esto representa una mejora pequena pero real.

Sin embargo, en el esquema combinado:

- combined_core + XGBoost
  - CA = 0.8050
  - MCC = 0.7131
- combined_contextual + XGBoost
  - CA = 0.8016
  - MCC = 0.7083

En este caso, agregar Clase_SiO2 y Serie_Mag empeora ligeramente el mejor esquema combinado.

### Plutonicas

Comparacion principal:

- oxides_core + RandomForest
  - CA = 0.5812
  - MCC = 0.4815
- oxides_contextual + RandomForest
  - CA = 0.5812
  - MCC = 0.4815 aproximadamente igual, pero sin mejora real

La diferencia es practicamente nula. En otros modelos y esquemas, las variantes contextuales tampoco muestran una ventaja consistente.

## Lectura de matrices de confusion

La inspeccion de las matrices de confusion mostro que en volcanicas la mejora de oxides_contextual proviene sobre todo de pequenos reajustes entre:

- basalto
- andesita basaltica
- andesita
- dacita

Es decir, hay una redistribucion leve de errores en clases geoquimicamente cercanas, no una transformacion importante del comportamiento del modelo.

En plutonicas, las diferencias entre core y contextual son pequenas y dispersas, sin un patron de mejora robusto.

## Interpretacion metodologica

La evidencia sugiere que Clase_SiO2 y Serie_Mag pueden aportar una ayuda marginal en algunos escenarios, especialmente en volcanicas con un esquema basado solo en oxidos. Sin embargo:

- no mejoran de manera consistente todos los modelos
- no mejoran el mejor esquema combinado
- no producen una ganancia clara en plutonicas
- siguen siendo variables derivadas que resumen informacion petroquimica ya presente

Por tanto, incluirlas como parte del baseline oficial no aporta suficiente beneficio metodologico para justificar el cambio.

## Decision final

### Sobre Clase_SiO2 y Serie_Mag

Se decide:

- mantenerlas como variables derivadas disponibles en el proyecto
- permitir su uso en experimentos contextuales o analisis secundarios
- no incorporarlas al benchmark principal ni al baseline oficial

En consecuencia, los esquemas contextuales:

- oxides_contextual
- combined_contextual

quedan como experimentos auxiliares, no como arquitectura principal del proyecto.

### Sobre Quality_Flag

Se confirma que:

- Quality_Flag debe mantenerse solo para QA/QC y filtrado
- no debe utilizarse como feature predictiva

### Sobre el baseline oficial

Se mantiene como recomendacion oficial:

- oxides_core
- cipw
- combined_core

### Tabla resumen de pipelines

| Pipeline | Contenido | Estado metodologico | Motivo |
|---|---|---|---|
| oxides_core | SiO2, TiO2, Al2O3, FeOT, CaO, MgO, MnO, Na2O, K2O, P2O5, LOI, Sum_Oxs | Oficial | Baseline geoquimico mas limpio, realista y defendible |
| oxides | oxides_core + CO2, F, Cl, SO3, S | Secundario | Incluye variables casi vacias o muy incompletas; no mejora consistentemente |
| cipw | Minerales normativos CIPW calculados con GeoNormPy | Oficial | Evalua el aporte de la mineralogia normativa por si sola |
| combined_core | oxides_core + cipw | Oficial | Esquema combinado principal: quimica confiable + informacion normativa |
| combined | oxides + cipw | Secundario | Agrega variables raras al combinado sin ganancia robusta |
| oxides_contextual | oxides_core + Clase_SiO2 + Serie_Mag | Experimental | Puede introducir suavizamiento o preclasificacion artificial |
| combined_contextual | oxides_core + cipw + Clase_SiO2 + Serie_Mag | Experimental | Agrega contexto derivado y no mejora de forma consistente |
| combined_enriched | oxides_core + cipw + %An en Pl + SUM_QAP + SUM_CIPW | Futuro experimento | Requiere evaluacion aparte antes de considerarse baseline |

## Recomendacion final de modelos

### Volcanicas

Hay dos opciones defendibles, segun el criterio de seleccion:

- Si se prioriza el mejor desempeno global multiclase:
  - combined_core + XGBoost
- Si se prioriza simplicidad, interpretabilidad y desempeno muy cercano:
  - oxides_core + RandomForest

Como recomendacion principal del proyecto, se propone declarar:

- **Modelo oficial volcanicas: combined_core + XGBoost**

porque mantiene el mejor MCC del benchmark y representa mejor la integracion entre geoquimica de oxidos y mineralogia normativa.

### Plutonicas

La mejor opcion sigue siendo:

- **Modelo oficial plutonicas: oxides_core + RandomForest**

porque obtuvo el mejor CA y MCC dentro de los esquemas evaluados y no fue superado por las variantes contextuales.

## Sobre ponderar features manualmente

No se recomienda introducir pesos manuales por feature como siguiente paso metodologico principal. La razon es que:

- RandomForest y XGBoost ya ajustan de forma implicita la relevancia de las variables
- asignar pesos manuales a features seria mas arbitrario y menos defendible academicamente
- no resolveria necesariamente el problema central, que es distinguir senales utiles de senales redundantes

Si se busca mejorar el modelo, las prioridades mas razonables serian:

- analisis de importancia de variables
- analisis de errores por clase
- ajuste de pesos por clase si el desbalance lo justifica
- evaluacion de variables enriquecidas como %An en Pl y SUM_QAP

## Conclusiones

1. Clase_SiO2 y Serie_Mag no producen una mejora suficientemente fuerte ni consistente para entrar al baseline oficial.
2. En volcanicas pueden ofrecer una ventaja pequena en un esquema basado solo en oxidos, pero esa ventaja no se mantiene en el mejor esquema combinado.
3. En plutonicas no muestran mejora real.
4. El baseline oficial del proyecto se mantiene como:
   - oxides_core
   - cipw
   - combined_core
5. La recomendacion final de modelos es:
   - volcanicas: combined_core + XGBoost
   - plutonicas: oxides_core + RandomForest
