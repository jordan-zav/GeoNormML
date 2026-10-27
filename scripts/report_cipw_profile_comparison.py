# ruff: noqa: E501
"""Render the completed profile experiment and independently check its metrics."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--output", type=Path, default=Path(r"D:\DevResources\Projects\GeoNormML\Reports\CIPWProfiles\2026-10-26")
)
OUT = parser.parse_args().output.resolve()
r = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
assert r["complete"] and r["originals_unchanged"]
pred = pd.read_csv(OUT / "holdout_predictions.csv")
source = pd.read_excel(ROOT / "Dataset/Filtered/final/GeoNormML_training_curated.xlsx")
labels = {domain: sorted(source.loc[source["ROCK TYPE"] == domain, "ROCK_NAME"].unique()) for domain in ("VOL", "PLU")}
checks = []
for item in r["primary_evaluation"]:
    selected = pred[(pred.domain == item["domain"]) & (pred.scenario == item["scenario"])]
    assert len(selected) == item["test"]
    assert selected.ID_Final.is_unique
    acc = accuracy_score(selected.actual, selected.predicted)
    f1 = f1_score(selected.actual, selected.predicted, labels=labels[item["domain"]], average="macro", zero_division=0)
    assert abs(acc - item["holdout"]["accuracy"]) < 1e-12
    assert abs(f1 - item["holdout"]["f1_macro"]) < 1e-12
    checks.append(
        {
            "domain": item["domain"],
            "scenario": item["scenario"],
            "rows": len(selected),
            "correct": int((selected.actual == selected.predicted).sum()),
        }
    )
for profile in ("extended_cipw_v3", "verma2003", "pruseth2009"):
    norm = pd.read_csv(OUT / (profile + "_norms.csv"))
    assert len(norm) == 2755 and set(norm.ID_Final) == set(source.ID_Final)
    assert not (norm.complete & (norm.status != "complete")).any()
for path, original_hash in r["source_hashes_before"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == original_hash
r["independent_metric_checks"] = checks
r["audit_driver_sha256_current"] = hashlib.sha256((ROOT / "scripts/compare_cipw_profiles.py").read_bytes()).hexdigest()
(OUT / "summary.json").write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

names = {
    "stored_reference": "Referencia almacenada",
    "oxides_only_control": "Solo oxidos (control)",
    "extended_cipw_v3": "Compatibilidad 3.1",
    "verma2003": "Verma 2003",
    "pruseth2009": "Pruseth 2009",
}
order = list(names)
colors = ["#60666d", "#bd9854", "#437b9a", "#26684b", "#835293"]
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "path",
    }
)
fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
for row, domain in enumerate(("VOL", "PLU")):
    entries = {item["scenario"]: item for item in r["primary_evaluation"] if item["domain"] == domain}
    for col, (metric, title) in enumerate((("accuracy", "Exactitud"), ("f1_macro", "F1 macro"))):
        ax = axes[row, col]
        values = [100 * entries[name]["holdout"][metric] for name in order]
        bars = ax.barh(range(len(order)), values, color=colors, height=0.62)
        ax.set_yticks(range(len(order)), [names[name] for name in order])
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xlabel("Porcentaje")
        ax.set_title(
            f"{domain} | {title} | reserva n={r['common_population'][domain]['test']}", loc="left", fontweight="bold"
        )
        ax.grid(axis="x", color="#dddddd", linewidth=0.6)
        ax.set_axisbelow(True)
        for bar, value in zip(bars, values):
            ax.text(value + 0.8, bar.get_y() + bar.get_height() / 2, f"{value:.2f}", va="center", fontsize=9)
fig.suptitle("Perfiles CIPW: comparacion controlada con modelos reajustados", fontsize=16, fontweight="bold")
fig.supxlabel(
    "Misma poblacion valida, mismos grupos y parametros. Reserva ya utilizada; no validacion externa.", fontsize=10
)
fig.savefig(OUT / "comparacion_ml.png", dpi=190)
fig.savefig(OUT / "comparacion_ml.svg")
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4), layout="constrained")
labels_profile = ["Compatibilidad 3.1", "Verma 2003", "Pruseth 2009"]
left = np.zeros(3)
for status, color, label in (
    ("complete", "#26684b", "Asignacion completa"),
    ("incomplete", "#bd9854", "Asignacion incompleta"),
    ("error", "#835293", "Componentes fuera del perfil"),
    ("missing_major", "#b7bdc2", "Mayores ausentes"),
):
    values = [
        r["norms"][name]["status_counts"].get(status, 0) for name in ("extended_cipw_v3", "verma2003", "pruseth2009")
    ]
    ax.barh(labels_profile, values, left=left, color=color, label=label)
    for index, (value, offset) in enumerate(zip(values, left)):
        if status == "complete":
            ax.text(value / 2, index, str(value), color="white", ha="center", va="center", fontweight="bold")
    left += values
ax.set_xlim(0, 2755)
ax.set_xlabel("Registros conservados (N=2755)")
ax.set_title("Cobertura de calculo con la misma quimica y Fe3+/Fe=0,15", loc="left", fontweight="bold")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.21), ncols=2, frameon=False)
ax.invert_yaxis()
fig.savefig(OUT / "cobertura_perfiles.png", dpi=190)
fig.savefig(OUT / "cobertura_perfiles.svg")
plt.close(fig)

lines = [
    "# Tres perfiles CIPW: efecto sobre GeoNormML y las afirmaciones del proyecto",
    "",
    "Fecha: 26 de octubre de 2026.",
    "",
    "## Resultado principal",
    "",
    "Los perfiles nuevos mejoran el control de masa y la trazabilidad, pero esta comparacion no demuestra una mejora general y robusta de exactitud ML. Verma es el candidato operativo mas amplio entre los probados para esta quimica; Pruseth sirve como alternativa metodologica con su propio alcance. No se cambiaron ni publicaron modelos de produccion.",
    "",
    "## Datos y metodo",
    "",
    "Se conservaron las 2755 muestras, identificadores, etiquetas y analisis originales. Se uso GeoNormPy 1.1.0 en el commit 6d3930d2a088262b88096b2edcac590125573a54, en una copia aislada de codigo en E:. No se sustituyeron paquetes de los entornos actuales. El dataset oficial mantiene SHA256 e57384afa323bebb3d18227e6071acce84699e27dd229c8b9635e62eed4b7ec9.",
    "",
    "Los tres perfiles reciben exactamente los mismos oxidos del contrato actual de integracion: SiO2, TiO2, Al2O3, FeOT, CaO, MgO, MnO, Na2O, K2O, P2O5 y, si existen, CO2, F, Cl, SO3, S, ZrO2 y Cr2O3. LOI no se trata como oxido normativo. NiO, aunque existe en pocos registros, no se agrega al contrato comun porque el perfil de compatibilidad y la integracion anterior no lo consumen. No se convirtieron ppm ni se inventaron ensayos ausentes.",
    "",
    "Politica de hierro fija Fe3+/Fe=0,15 y carbonato calcita en los tres. Son supuestos de calculo, no mediciones de redox ni identificacion modal del carbonato. La falta de un mayor requerido impide calcular esa fila en el experimento; sigue registrada con su causa.",
    "",
    "## Calculo normativo",
    "",
    "| Perfil | Completas | Incompletas | Fuera de alcance | Mayores ausentes | Maximo error de masa entre completas, puntos porcentuales |",
    "| --- | ---: | ---: | ---: | ---: | ---: |",
]
for name in ("extended_cipw_v3", "verma2003", "pruseth2009"):
    item = r["norms"][name]
    counts = item["status_counts"]
    lines.append(
        f"| {name} | {counts.get('complete', 0)} | {counts.get('incomplete', 0)} | {counts.get('error', 0)} | {counts.get('missing_major', 0)} | {item['max_mass_error_complete']:.6g} |"
    )
lines += [
    "",
    "Las 20 asignaciones incompletas del perfil de compatibilidad dejan fosforo sin asignar. Verma conserva esos componentes libres con advertencia y los contabiliza. Pruseth hace lo propio, pero rechaza 19 composiciones con SO3 no nulo, fuera de su alcance implementado. Ninguna de estas situaciones autoriza borrar una muestra o declarar que su nombre de roca es incorrecto.",
    "",
    "El balance de los perfiles nuevos incluye minerales, componentes libres y correcciones con signo. Pruseth usa fluorapatita normativa y una correccion explicita de fluor, incluso sin F medido. Por ello la suma mineral puede no ser 100; no debe renormalizarse para ocultar la contabilidad. Un cierre de masa correcto no prueba mineralogia observada ni petrogenesis.",
    "",
    "## Comparacion ML justa",
    "",
    f"La interseccion valida de los tres perfiles contiene {r['common_complete_rows']} muestras. Las otras 54 siguen en los CSV con sus motivos; solo quedan fuera de la comparacion comun, no de la base oficial. Se mantuvieron los IDs de la reserva original y los grupos de muestras. No hubo grupos compartidos entre entrenamiento y reserva ni entre pliegues.",
    "",
    "| Dominio | Entrenamiento comun | Reserva comun | Grupos de reserva | Pliegues de CV de entrenamiento |",
    "| --- | ---: | ---: | ---: | ---: |",
]
for domain, item in r["common_population"].items():
    lines.append(f"| {domain} | {item['train']} | {item['test']} | {item['test_groups']} | {item['cv_folds']} |")
lines += [
    "",
    "Se clonaron los mismos estimadores oficiales: XGBoost de 300 arboles para VOL y RandomForest de 400 para PLU, con sus parametros originales. Se hicieron 50 ajustes de CV, 10 de reserva comun y dos de reproduccion historica. Ningun ajuste experimental se serializo como modelo de produccion.",
    "",
    "La pretransformacion se ajusta dentro de cada entrenamiento; sus medianas no ven validacion ni reserva. Esta imputacion estadistica no reescribe los analisis originales. Se mantuvo el contrato de 39 predictores: oxidos y 27 fases; Ap se armonizo explicitamente como grupo total Ap+FAp. Los CSV conservan Ap y FAp originales por separado. No se anadieron otras fases nuevas ni componentes libres como predictores. Esto compara una representacion comun, no toda la capacidad posible de cada perfil.",
    "",
    "Las metricas se recalcularon independientemente desde el CSV de predicciones. Todos los IDs se conservaron en las tablas normativas y los hashes de datos, particiones, modelos y esquema originales se verificaron antes y despues.",
    "",
    "## Resultados sobre la misma poblacion",
    "",
    "| Dominio | Variables / perfil | Exactitud reserva | F1 macro reserva | Exactitud CV media | F1 macro CV media |",
    "| --- | --- | ---: | ---: | ---: | ---: |",
]
for item in r["primary_evaluation"]:
    lines.append(
        f"| {item['domain']} | {names[item['scenario']]} | {100 * item['holdout']['accuracy']:.2f}% | {item['holdout']['f1_macro']:.4f} | {100 * item['cv_mean']['accuracy']:.2f}% | {item['cv_mean']['f1_macro']:.4f} |"
    )
lines += [
    "",
    "![Comparacion controlada de modelos](comparacion_ml.png)",
    "",
    "Frente a las variables normativas almacenadas, Verma y Pruseth ganan dos aciertos netos en las 346 volcanicas de reserva: +0,58 puntos porcentuales. En plutonicas los tres perfiles recalculados ganan cuatro aciertos en 198: +2,02 puntos. La validacion cruzada no muestra una ganancia uniforme: en PLU la exactitud CV de Verma es inferior a la referencia y al control solo-oxidos. En VOL, el control solo-oxidos tambien supera ligeramente a los nuevos perfiles en exactitud de reserva. Por tanto, no procede afirmar que CIPW siempre mejora ML.",
    "",
    "Se calcularon intervalos descriptivos mediante 2000 remuestreos de grupos sobre las predicciones de reserva. En VOL la diferencia Verma frente a referencia abarca valores negativos y positivos. En PLU el intervalo condicional es positivo, pero corresponde a cuatro cambios de un solo ajuste y no incluye la incertidumbre del entrenamiento; ademas la CV no confirma una mejora uniforme. Estos intervalos no son una certificacion estadistica ni una evaluacion externa.",
    "",
    "La reserva ya se utilizo en trabajos anteriores. No se eligieron parametros ni un perfil ganador a partir de estos resultados. Para una afirmacion de superioridad hacen falta un protocolo predefinido y evaluacion adicional, preferentemente externa o geografica segun el objetivo.",
    "",
    "## Reproduccion de la referencia historica",
    "",
    "Se reajustaron los modelos sobre las 2202 muestras de entrenamiento originales y se predijeron las 553 de reserva, sin evaluar el estimador final que habia sido reajustado con toda la base.",
    "",
    "| Dominio | Reserva original | Exactitud reproducida | F1 macro reproducido |",
    "| --- | ---: | ---: | ---: |",
]
for item in r["historical_replication"]:
    lines.append(f"| {item['domain']} | {item['test']} | {100 * item['accuracy']:.2f}% | {item['f1_macro']:.4f} |")
lines += [
    "",
    "Estas cifras reproducen la referencia versionada del pipeline (77,40% VOL y 58,29% PLU). No deben compararse directamente con la reserva comun de 544 filas ni interpretarse como una mejora frente a ella: cambian la poblacion y los ajustes.",
    "",
    "## Efecto sobre lo declarado en el proyecto",
    "",
    "| Afirmacion o resultado anterior | Efecto de esta revision |",
    "| --- | --- |",
    "| 2755 muestras, 1764 VOL, 991 PLU y 19 clases | Se mantiene. No se borraron IDs ni cambiaron etiquetas. |",
    "| Integracion reproducible de quimica, CIPW y ML | Se refuerza si se registra perfil, version y politica de hierro, ademas de los hashes. No es validacion petrografica externa. |",
    "| Un resultado de masa correcto equivale a una norma valida | Debe matizarse: componentes libres y deficit firmado pueden cerrar contabilidad sin justificar una interpretacion mineralogica. |",
    "| CIPW mejora siempre la clasificacion ML | No queda respaldado como afirmacion general. El efecto depende de dominio, metrica, muestra y protocolo. |",
    "| Paper: VOL XGBoost combined_core, CA 0.804989; PLU RandomForest oxides_core, CA 0.581231 | Son estimaciones historicas de otro protocolo declarado de CV. No se sustituyen por estas cifras de reserva ni se presentan como metricas de los perfiles nuevos. No se encontro un archivo de metricas local que permitiera reproducir exactamente esos dos numeros en esta auditoria. |",
    "| Modelo plutonico elegido con oxides_core | Un cambio de fases CIPW no cambia directamente sus predictores si se conservan oxidos y preprocesamiento. El modelo PLU desplegado en el manifiesto actual de PetroPyQAPF es combined_core; no hay que confundir ambos modelos. |",
    "| Informe de agosto: 2887 muestras y cuatro modelos oficiales espaciales | No describe la base y transferencia actuales: hay 2755 IDs curados y dos modelos geoquimicos oficiales. Es una correccion previa a estos perfiles. |",
    "| La mejora numerica equivale a mayor exactitud o mejores nombres geologicos | No. La mejora demostrada aqui es de contabilidad y trazabilidad, con resultados predictivos dependientes de la evaluacion. |",
    "",
    "Los documentos examinados son docs/paper_geonormpy_geonormml_cpg_xxiii.md, su copia en docs/publicaciones, las configuraciones de poster_cpg23 y docs/Informe_GeoNormML_GeoNormPy_2026.md. No se reescribieron esas declaraciones ni se modificaron cifras del poster.",
    "",
    "## Redaccion sugerida para el proyecto",
    "",
    "La ampliacion de GeoNormPy incorpora perfiles normativos versionados y politicas de hierro explicitas. En la base curada de 2755 muestras, los perfiles revisados mejoran el cierre contable y distinguen componentes libres, entradas incompletas y restricciones del metodo, conservando la trazabilidad de todas las observaciones. Esta mejora de calculo no implica por si sola un aumento de exactitud del clasificador.",
    "",
    "En una comparacion exploratoria controlada, con los mismos grupos y parametros y una poblacion comun de 2701 muestras, se observaron cambios modestos en exactitud de reserva y cambios dependientes del dominio en validacion cruzada. Los resultados apoyan documentar el perfil normativo utilizado y evaluar su contribucion de manera especifica; no justifican afirmar superioridad predictiva general ni validacion externa.",
    "",
    "## Consecuencias para PetroPyQAPF",
    "",
    "La clasificacion modal conserva su autoridad. Adoptar los nuevos perfiles requiere seleccionar y mostrar su version, llevar metadatos de calculo a los reportes, distinguir suma mineral de cierre total y versionar la construccion de variables ML, incluida la apatita. No se deben alimentar modelos entrenados con una convencion normativa mediante otra sin evaluar y, cuando corresponda, reajustar su entrenamiento. NIM/GPKE pueden recibir contrastes distintos, pero estos indices no deben contabilizar el cambio como una confirmacion independiente adicional.",
    "",
    "Como decision operativa provisional, Verma ofrece mayor cobertura de esta quimica que Pruseth y mejor contabilidad que la compatibilidad. Es un candidato para integracion y comprobaciones posteriores, no un perfil elegido por maximizar la reserva ni una nueva configuracion ya desplegada.",
    "",
    "## Evidencias y reproduccion",
    "",
    "- 385 pruebas del codigo aprobadas y tres pruebas adicionales del wheel construido aprobadas: 388 casos distintos comprobados. Los tres casos del wheel se omitieron en la primera llamada y se ejecutaron despues; no se cuentan dos veces.",
    "- GeoNormML: 32 pruebas aprobadas, Ruff sin errores y pip check correcto. Diez conjuntos de predicciones se verificaron independientemente desde CSV y se reconstruyeron las sumas minerales y de componentes libres.",
    "- summary.json: perfiles, parametros, hashes, metricas, pliegues e intervalos.",
    "- metrics.csv, holdout_predictions.csv y matrices de confusion: resultados verificables.",
    "- Tres archivos terminados en _norms.csv: todas las filas y fases originales de cada perfil, estados y causas.",
    "- evaluation_population.csv: pertenencia a la poblacion comun y a la particion original.",
    "- comparacion_ml.svg y cobertura_perfiles.svg: figuras vectoriales; PNG para lectura rapida.",
    "- scripts/compare_cipw_profiles.py y scripts/report_cipw_profile_comparison.py: ejecutores en el repositorio local GeoNormML, sin publicacion automatica.",
    "",
    "El motor se comprobo en el commit 6d3930d2a088262b88096b2edcac590125573a54. Fuentes metodologicas del propio motor: [perfiles y convenciones](https://github.com/jordan-zav/GeoNormPy/blob/6d3930d2a088262b88096b2edcac590125573a54/docs/PERFILES_CIPW.md). Los analisis originales, modelos oficiales y recursos de produccion permanecen intactos.",
]
text = "\n".join(lines) + "\n"
assert chr(96) not in text and chr(0xB4) not in text
(OUT / "informe-impacto.md").write_text(text, encoding="utf-8")
print(
    json.dumps(
        {
            "verified_prediction_sets": len(checks),
            "source_hashes_unchanged": True,
            "report": str(OUT / "informe-impacto.md"),
        },
        ensure_ascii=False,
    )
)
