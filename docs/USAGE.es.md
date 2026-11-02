# Uso del paquete instalado

[English](USAGE.md) · [Preparación para PyPI](PUBLISHING.md)

La interfaz instalada es una CLI y una API Python. GeoNormML sigue como candidato
preparado, todavía sin publicar. Instala el wheel verificado mientras tanto:

    python -m pip install RUTA/geonormml-0.1.0-py3-none-any.whl
    geonormml --version
    geonormml --help

Si ya instalaste otro candidato 0.1.0 anterior a la publicación, utiliza
pip install --force-reinstall con el wheel nuevo para sustituir ese candidato.

GeoNormPy 1.1.0 se instala desde PyPI. No se descargan datos ni pesos privados.
El entorno comprobado usa Python 3.11; las versiones registradas por cada modelo
también deben coincidir para cargarlo.

## Ejemplo completo

Elige una carpeta nueva, incluso con espacios:

    geonormml example --output "D:/mi trabajo/modelo ejemplo"
    geonormml inspect "D:/mi trabajo/modelo ejemplo/manifest.json"
    geonormml predict --model "D:/mi trabajo/modelo ejemplo/manifest.json" --input "D:/mi trabajo/modelo ejemplo/input.csv" --output "D:/mi trabajo/predicciones.csv" --id-column Sample_ID --trust-model

El ejemplo usa química inventada, clases Synthetic_A / Synthetic_B y un
DummyClassifier. Comprueba CIPW, variables e inferencia; no clasifica rocas con
validez científica. Solo crea la carpeta solicitada y no sobrescribe destinos.

Los comandos devuelven JSON por stdout. Los diagnósticos van a stderr; un error
devuelve código 2 y JSON por stderr. También funciona python -m geonormml.

## Rutas y modelos

    geonormml paths
    geonormml models

Estos comandos no crean carpetas ni cargan pesos. El wheel instalado utiliza
almacenamiento del usuario: LOCALAPPDATA/geonormml en Windows,
~/Library/Application Support/geonormml en macOS y XDG_DATA_HOME/geonormml o
~/.local/share/geonormml en Linux. No usa la carpeta de instalación de Python
como proyecto de datos o salidas.

| Variable | Función |
| --- | --- |
| GEONORMML_HOME | Directorio de aplicación del usuario |
| GEONORMML_MODELS_DIR | Registro de manifiestos de modelos |
| GEONORMML_ARTIFACTS_DIR | Salidas de investigación explícitas |
| GEONORMML_DATASET_PATH | Libro de entrenamiento para scripts; la inferencia no lo lee |
| GEONORMML_PROJECT_ROOT | Raíz de investigación explícita, con su layout histórico |

Un checkout real se reconoce para conservar el pipeline histórico. Allí las
salidas de investigación mantienen artifacts bajo el proyecto salvo override.
Las rutas del registro de modelos siguen bajo el usuario. En esta PC conserva
código en O:/0. Projects y recursos en D:/DevResources; usa los lanzadores locales.

Un modelo puede estar en cualquier directorio autorizado, con manifest.json y
model.joblib. Para seleccionarlo por nombre, colócalo en una subcarpeta de
GEONORMML_MODELS_DIR; también se admite su ruta completa. inspect verifica hash
y entorno sin deserializar. --metadata-only muestra únicamente metadata.

Joblib puede ejecutar código al cargar un archivo. Usa exclusivamente una fuente
de confianza y trusted=True o --trust-model. El hash comprueba integridad, no
confianza en el autor. La API no instala ni cambia dependencias automáticamente.

## Modelos existentes y contrato

El manifiesto registra generación, dominio VOL/PLU, orden de variables y clases,
Python major.minor, versiones exactas de scikit-learn, numpy, scipy y joblib,
y otras bibliotecas necesarias. Las clases pueden estar en classes o en un
label_encoder del bundle. Se comprueban también las columnas guardadas en el
estimador o en selected.columns.

Para adjuntar un contrato conocido sin cargar ni modificar el archivo:

    geonormml manifest --model-file "D:/modelos/mi modelo/model.joblib" --metadata "D:/modelos/mi modelo/contrato registrado.json"

El JSON de entrada debe contener los campos anteriores, input_mode y la
codificación de clases. El comando añade el hash y escribe un manifest.json
nuevo. create_model_manifest ofrece lo mismo desde Python. Para un modelo viejo,
usa sus versiones de entrenamiento registradas; no las deduzcas del entorno actual.

prepared_features recibe las columnas ya calculadas en el orden del modelo y
no recalcula CIPW. Declara categorical_columns para columnas de texto. Es la vía
compatible para pesos históricos sin procedencia normativa completa.
Los modelos espaciales experimentales requieren columnas ya preparadas y
conservan sus límites de transferencia geográfica y científica.

oxide_chemistry admite oxides_core, combined_core, combined_contextual y
combined_enriched. Exige diez mayores medidos: SiO2, TiO2, Al2O3, FeOT, CaO,
MgO, MnO, Na2O, K2O y P2O5, en porcentaje en peso. LOI y Sum_Oxs ausentes se
conservan para el imputador entrenado; LOI negativo medido sigue siendo válido.
No se recalcula el total analítico. Las normas y categorías antiguas de la
tabla se ignoran y recalculan. El adaptador de química no deriva ni aporta
predictores espaciales.

Si utiliza normas, el contrato declara GeoNormPy 1.1.0, perfil y versión,
iron_policy fixed, fe3_fraction explícita, carbonate_mode calcite y
apatite_feature Ap + FAp. La convención actual se limita al reparto fijo de
FeOT y calcita; otros contratos deben utilizar variables ya preparadas.
Consulta el [detalle y ejemplo JSON](USAGE.md).

El artifact raw debe contener ese mismo input_mode, feature_set y contrato
normativo. Cambiar únicamente el JSON no sustituye el contrato guardado.
Los exports históricos v2/v5 sin esos campos completos se pueden consumir como
prepared_features. Preparar otro adaptador exige verificar la procedencia del
entrenamiento y conservar el binario histórico; no hay conversión automática.

## API Python y resultados

    import pandas as pd
    from geonormml import load_model, predict

    model = load_model("D:/modelos/mi modelo/manifest.json", trusted=True)
    table = pd.read_csv("D:/mis datos/entrada.csv", dtype={"Sample_ID": str})
    result = predict(table, model, id_column="Sample_ID")
    print(result[["sample_id", "prediction", "status", "error_code"]])

La tabla original se conserva. Cada fila aparece en el resultado, incluso si se
rechaza; input_row identifica su posición y la API conserva índices repetidos.
El CSV conserva IDs como 001 o NA. Campos numéricos vacíos son ausencias, no ceros.
Si existe ROCK TYPE, se rechazan filas de otro dominio; sin esa columna, elegir
el modelo es la selección explícita del dominio. No hay enrutamiento automático.

Se informan errores por fila para valores inválidos, mayores ausentes, óxidos
negativos, dominio incompatible y normas incompletas. Las filas válidas continúan.
Faltas de columnas o discrepancias de hash, entorno y contrato detienen la
solicitud antes de escribir resultados. No se sobrescriben entrada, modelo ni
salidas existentes. Un fallo del estimador no genera un resultado parcial.

prediction contiene la etiqueta y probability::<clase> los valores del modelo;
si el estimador no calcula probabilidades, quedan ausentes. No son una confianza
individual certificada ni calibración externa demostrada. La CLI lee el CSV en
memoria. Ni este ejemplo ni las pruebas sustituyen una evaluación independiente.
