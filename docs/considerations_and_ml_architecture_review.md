# Revisión de `Considerations` y propuesta de arquitectura de ML

## Propósito

Este documento evalúa si las variables adicionales sugeridas en [`Considerations.docx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Considerations.docx) son convenientes para el modelado y propone una arquitectura experimental alineada con el paper, pero metodológicamente más clara y robusta.

## 1. Variables adicionales de `Considerations`

Las variables o reglas principales recuperadas de `Considerations` fueron:

- `Clase_SiO2`
- `Alc = Na2O + K2O`
- `Serie_Mag`
- `Quality_Flag`

Y, desde la etapa CIPW ya reconstruida:

- `%An en Pl`
- `SUM_QAP`
- `SUM_CIPW`
- `ITT` (todavía no trazable)

## 2. ¿Conviene usar estos cálculos nuevos?

### 2.1. `Alc`

Sí, **es una variable razonable**.

Ventajas:

- tiene significado geoquímico directo;
- resume el sistema alcalino en una sola magnitud;
- puede ayudar especialmente en clases alcalinas o transicionales;
- es interpretable y reproducible.

Riesgo:

- es totalmente derivada de `Na2O` y `K2O`, por lo que en modelos basados en árboles puede ser redundante.

Conclusión:

`Alc` sí puede probarse, pero como feature derivada opcional, no como parte obligatoria del baseline principal.

### 2.2. `Clase_SiO2`

Puede ayudar, pero **no la pondría en el baseline principal**.

Ventajas:

- introduce una discretización geoquímica intuitiva;
- puede ayudar a separar grandes dominios composicionales.

Riesgos:

- es una discretización dura de `SiO2`, por lo que pierde información;
- puede volver artificialmente más fácil la clasificación de clases que ya se ordenan por sílice;
- puede distorsionar la comparación entre “óxidos puros” y “óxidos enriquecidos”.

Conclusión:

Conviene usarla como experimento secundario, no como parte del esquema central del paper.

### 2.3. `Serie_Mag`

Es útil geológicamente, pero **debe tratarse con cuidado**.

Ventajas:

- resume información sobre alcalinidad y subsaturación;
- puede ayudar a separar grupos alcalinos de subalcalinos;
- tiene interpretación petrológica.

Riesgos:

- depende de `Ne` y `Le`, por lo que ya incorpora información CIPW;
- si se usa junto con CIPW, añade una capa resumida del mismo contenido;
- puede inflar artificialmente la ventaja del esquema “combinado” o de uno enriquecido.

Conclusión:

Conviene incluirla solo en una fase avanzada de ingeniería de variables, no en el núcleo experimental principal.

### 2.4. `Quality_Flag`

**No debería usarse como feature predictiva.**

Razón:

- no describe litología, sino calidad o rareza de la muestra;
- mezclarlo con el target puede introducir señales espurias;
- es una variable de control, no una variable geológica del fenómeno.

Uso correcto:

- exclusión de registros;
- filtro de QA/QC;
- auditoría post hoc.

### 2.5. `%An en Pl`

Sí, **es un buen descriptor derivado**.

Ventajas:

- resume una relación mineralógica útil;
- es interpretable geológicamente;
- puede ayudar a diferenciar composiciones feldespáticas.

Riesgo:

- ya está contenido indirectamente en `An` y `Ab`.

Conclusión:

Úsala en un esquema enriquecido, no en el baseline CIPW puro.

### 2.6. `SUM_QAP`

Puede ser útil como descriptor, pero **no es esencial**.

Ventajas:

- resume la contribución de minerales félsicos principales;
- tiene sentido petrológico.

Riesgo:

- ya deriva directamente de `Q + Or + Ab + An`;
- añade poca información nueva si esos minerales ya están incluidos.

Conclusión:

Variable opcional para experimentos enriquecidos.

### 2.7. `SUM_CIPW`

**No parece una buena feature principal.**

Razón:

- suele estar muy cerca de 100;
- aporta poco contraste entre clases;
- es más una métrica de consistencia que una señal litológica.

Conclusión:

No priorizarla como feature predictiva.

### 2.8. `ITT`

**No debe usarse todavía.**

Razón:

- no quedó completamente trazable;
- su definición no es suficientemente estable en los datos revisados.

Conclusión:

Excluirla hasta documentarla correctamente.

## 3. Veredicto general sobre los nuevos cálculos

Tu intuición fue buena: varios de esos cálculos sí pueden ayudar a diferenciar clases. Pero no todos deben entrar al modelo con el mismo estatus.

La mejor forma de hacerlo, respetando tu paper y mejorándolo, es separar:

1. features base del experimento principal;
2. features derivadas opcionales;
3. variables de QA/QC;
4. variables no trazables o no recomendadas.

## 4. Inconsistencias o debilidades del paper

Estas son las principales inconsistencias que veo al contrastar el paper con el dataset y `Considerations`:

### 4.1. El paper no separa con suficiente claridad los niveles de variables

Se mezclan:

- óxidos originales;
- minerales CIPW;
- variables derivadas;
- reglas de calidad.

Mejora:

Declarar explícitamente niveles de features.

### 4.2. `Quality_Flag` aparece como sistema formal, pero en la práctica no quedó activo

En los archivos revisados, el flag no operaba realmente como variable diferenciadora final.

Mejora:

Mover `Quality_Flag` fuera del conjunto de features y dejarlo solo como control de datos.

### 4.3. Algunas variables calculadas no estaban justificadas como experimento independiente

Por ejemplo, `Clase_SiO2` y `Serie_Mag` pueden ayudar, pero no estaba claro si eran parte del baseline o una extensión.

Mejora:

Comparar formalmente:

- baseline estricto;
- baseline + derivadas;
- baseline + CIPW;
- baseline + CIPW + derivadas seleccionadas.

### 4.4. `ITT` no quedó bien definido

Mejora:

Excluirlo hasta reconstruir su fórmula.

### 4.5. El paper trata bien la lógica geológica, pero no encapsula bien el orden experimental

Mejora:

Estructurar el flujo como una secuencia reproducible de experimentos.

## 5. Arquitectura de ML recomendada respetando el paper

La arquitectura debe conservar la idea central del paper:

- comparar esquemas de entrada;
- evaluar varios algoritmos supervisados;
- separar grupos litológicos;
- interpretar resultados geológicamente.

Pero conviene ordenarla en capas.

### 5.1. Nivel 1: experimento principal

Estos son los experimentos que mejor respetan tu paper:

#### A. Solo óxidos

Features:

- óxidos mayores
- `LOI`
- `Sum_Oxs`

Objetivo:

Medir cuánto puede hacer la geoquímica base por sí sola.

#### B. Solo CIPW

Features:

- minerales normativos CIPW

Objetivo:

Medir el poder discriminante del espacio normativo.

#### C. Óxidos + CIPW

Features:

- todos los óxidos del esquema A
- todos los minerales del esquema B

Objetivo:

Reproducir y mejorar el núcleo del paper.

### 5.2. Nivel 2: experimento enriquecido

Aquí entran solo algunas derivadas seleccionadas:

- `Alc`
- `%An en Pl`
- `SUM_QAP`

Y, si quieres probarla aparte:

- `Clase_SiO2`

No incluiría aquí todavía:

- `Quality_Flag`
- `ITT`
- `SUM_CIPW` como feature central

### 5.3. Nivel 3: control y auditoría

Variables para control, no para predicción:

- `Quality_Flag`
- `calc_error`
- `mass_balance_error`
- `interpretive_flag`

Estas deben servir para:

- filtrar muestras;
- auditar resultados;
- interpretar errores.

## 6. Recomendación experimental concreta

Propongo esta secuencia:

### Fase 1. Replicación del paper

Modelos:

- `RandomForest`
- `SVM`
- `XGBoost` o, si quieres arrancar sin esa dependencia, `HistGradientBoosting`

Esquemas:

- `oxides`
- `cipw`
- `combined`

Objetivo:

Recuperar el espíritu del paper en un pipeline reproducible.

### Fase 2. Extensión controlada

Agregar un cuarto esquema:

- `combined_enriched`

Con:

- óxidos
- CIPW
- `%An en Pl`
- `SUM_QAP`
- opcionalmente `Alc`

Objetivo:

Probar si esas nuevas derivadas realmente mejoran la separación de clases.

### Fase 3. Análisis de sensibilidad

Comparar:

- con y sin `Clase_SiO2`
- con y sin `Alc`
- con y sin algunas clases marginales

Objetivo:

Medir si la mejora es real o si solo refleja redundancia.

## 7. Decisión final sobre tus nuevos cálculos

Mi recomendación es esta:

- **Sí usar**: `Alc`, `%An en Pl`, `SUM_QAP` como pruebas enriquecidas.
- **Usar con cautela**: `Clase_SiO2`, solo como experimento secundario.
- **No usar como features**: `Quality_Flag`.
- **No usar todavía**: `ITT`.
- **No priorizar**: `SUM_CIPW`.

## 8. Estado actual del proyecto

El bootstrap del pipeline ya fue actualizado para contemplar un esquema adicional:

- `oxides`
- `cipw`
- `combined`
- `combined_enriched`

Esto deja al proyecto alineado con tu paper, pero preparado para evaluar si esas derivadas adicionales realmente aportan valor.
