#target illustrator

/*
  Tótem GeoNorm para el XXIII CPG.
  Genera un .ai nativo con 10 mesas de trabajo y tipografía Arial.
*/

app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;

var W = 1080;
var H = 1920;

var PAPER = "F3EFE4";
var PAPER_LIGHT = "FAF8F2";
var INK = "17262D";
var MUTED = "5E6B70";
var NAVY = "102F3D";
var TEAL = "287C8E";
var TEAL_LIGHT = "DDECEF";
var GREEN = "4C956C";
var GREEN_LIGHT = "E3EFE7";
var COPPER = "B66A4A";
var COPPER_LIGHT = "F1E2DA";
var GOLD = "D5A63B";
var WHITE = "FFFFFF";
var LINE = "D8D4CA";
var SOFT_RED = "F4E4E0";

var ROOT = new File($.fileName).parent.parent;
var outputOverride = $.getenv("GEONORMML_POSTER_OUTPUT_DIR");
var OUTPUT = new Folder(outputOverride || (ROOT.fsName + "/artifacts/posters/illustrator"));
var PREVIEW = new Folder(OUTPUT.fsName + "/preview_ai");
var ASSETS = new Folder(OUTPUT.fsName + "/assets");
function ensureOutputFolder(folder) {
    if (folder.exists) return;
    if (!folder.parent.exists) ensureOutputFolder(folder.parent);
    if (!folder.create()) throw new Error("No se pudo crear la carpeta de salida: " + folder.fsName);
}
ensureOutputFolder(OUTPUT);
if (!PREVIEW.exists) PREVIEW.create();
if (!ASSETS.exists) ASSETS.create();

var MAP_PATH = new File(ROOT.fsName + "/docs/dataset_filtrado.jpg");
var DASH_PATH = new File(ROOT.fsName + "/artifacts/dashboard_confiabilidad_actualizado.png");
var VOL_CIPW_PATH = new File(ROOT.fsName + "/artifacts/tas_comparison/concordancia_litologia_cipw_vol.png");
var PLU_CIPW_PATH = new File(ROOT.fsName + "/artifacts/tas_comparison/concordancia_litologia_cipw_plu.png");
var QR_PATH = new File(ASSETS.fsName + "/qr_geonormpy.png");

var AI_PATH = new File(OUTPUT.fsName + "/Totem_GeoNorm_final_Arial.ai");
var PDF_PATH = new File(OUTPUT.fsName + "/Totem_GeoNorm_final_Arial.pdf");

function rgb(hex) {
    var c = new RGBColor();
    c.red = parseInt(hex.substr(0, 2), 16);
    c.green = parseInt(hex.substr(2, 2), 16);
    c.blue = parseInt(hex.substr(4, 2), 16);
    return c;
}

function artboardInfo(doc, index) {
    var r = doc.artboards[index].artboardRect;
    return { left: r[0], top: r[1], right: r[2], bottom: r[3] };
}

function rect(layer, a, x, y, w, h, fill, stroke, radius, strokeWidth) {
    var p;
    if (radius && radius > 0) {
        p = layer.pathItems.roundedRectangle(a.top - y, a.left + x, w, h, radius, radius);
    } else {
        p = layer.pathItems.rectangle(a.top - y, a.left + x, w, h);
    }
    p.filled = true;
    p.fillColor = rgb(fill);
    if (stroke) {
        p.stroked = true;
        p.strokeColor = rgb(stroke);
        p.strokeWidth = strokeWidth || 1;
    } else {
        p.stroked = false;
    }
    return p;
}

function textBox(layer, a, value, x, y, w, h, size, fill, bold, align, leading, italic) {
    var path = layer.pathItems.rectangle(a.top - y, a.left + x, w, h);
    path.stroked = false;
    path.filled = false;
    var tf = layer.textFrames.areaText(path);
    tf.contents = value;
    var range = tf.textRange;
    var fontName = italic ? "Arial-ItalicMT" : (bold ? "Arial-BoldMT" : "ArialMT");
    range.characterAttributes.textFont = app.textFonts.getByName(fontName);
    range.characterAttributes.size = size;
    range.characterAttributes.autoLeading = false;
    range.characterAttributes.leading = leading || size * 1.24;
    range.characterAttributes.fillColor = rgb(fill);
    range.paragraphAttributes.spaceAfter = 0;
    var justification = Justification.LEFT;
    if (align === "center") justification = Justification.CENTER;
    else if (align === "right") justification = Justification.RIGHT;
    for (var p = 0; p < tf.paragraphs.length; p++) {
        try { tf.paragraphs[p].paragraphAttributes.justification = justification; } catch (ignoreJustification) {}
    }
    return tf;
}

function divider(layer, a, x, y, w, fill) {
    return rect(layer, a, x, y, w, 2, fill || LINE, null, 0);
}

function bulletList(layer, a, items, x, y, w, lineHeight, size, accent, textColor) {
    for (var i = 0; i < items.length; i++) {
        rect(layer, a, x, y + i * lineHeight + 7, 10, 10, accent, null, 3);
        textBox(layer, a, items[i], x + 25, y + i * lineHeight, w - 25, lineHeight, size, textColor || INK, false, "left", size * 1.18);
    }
}

function metricCard(layer, a, value, label, x, y, w, h, accent, dark) {
    rect(layer, a, x, y, w, h, dark ? accent : WHITE, accent, 12, 1.2);
    textBox(layer, a, value, x + 12, y + 16, w - 24, 44, 24, dark ? WHITE : accent, true, "center", 27);
    textBox(layer, a, label, x + 12, y + 70, w - 24, 28, 11, dark ? "E5EFF1" : MUTED, false, "center", 13);
}

function sectionCard(layer, a, heading, body, x, y, w, h, accent, number) {
    rect(layer, a, x, y, w, h, WHITE, accent, 8, 1.1);
    rect(layer, a, x, y, 116, h, accent, null, 0);
    if (number) textBox(layer, a, number, x + 20, y + 28, 76, 36, 18, WHITE, true, "center", 20);
    if (heading) {
        textBox(layer, a, heading.toUpperCase(), x + 146, y + 24, w - 174, 28, 12, accent, true, "left", 14);
        textBox(layer, a, body, x + 146, y + 64, w - 174, h - 80, 13, INK, false, "left", 16);
    } else {
        textBox(layer, a, body, x + 146, y + 35, w - 174, h - 58, 13, INK, true, "left", 17);
    }
}

function placedImage(layer, a, file, x, y, w, h, pad, border, background) {
    rect(layer, a, x, y, w, h, background || WHITE, border || LINE, 10, 1);
    if (!file.exists) {
        textBox(layer, a, "RECURSO NO ENCONTRADO\r" + file.fsName, x + 25, y + 60, w - 50, 90, 12, COPPER, true, "center", 15);
        return null;
    }
    var p = layer.placedItems.add();
    p.file = file;
    var maxW = w - 2 * (pad || 10);
    var maxH = h - 2 * (pad || 10);
    var factor = Math.min(maxW / p.width, maxH / p.height) * 100;
    p.resize(factor, factor);
    p.left = a.left + x + (w - p.width) / 2;
    p.top = a.top - y - (h - p.height) / 2;
    p.embed();
    return p;
}

function base(layer, a, page, section, accent, accentY, accentH) {
    rect(layer, a, 0, 0, W, H, PAPER, null, 0);
    rect(layer, a, 0, 0, 74, H, NAVY, null, 0);
    rect(layer, a, 0, accentY, 74, accentH, accent, null, 0);
    textBox(layer, a, "GEONORM", 112, 40, 240, 24, 11, NAVY, true, "left", 13);
    textBox(layer, a, "PÁGINA " + (page < 10 ? "0" + page : page) + " / 10", 820, 40, 186, 24, 9, MUTED, false, "right", 11);
    divider(layer, a, 112, 82, 894, LINE);
    textBox(layer, a, section.toUpperCase(), 112, 116, 894, 30, 10, accent, true, "left", 12);
    divider(layer, a, 112, 1848, 894, LINE);
    textBox(layer, a, "XXIII CONGRESO PERUANO DE GEOLOGÍA · 2026", 112, 1867, 520, 22, 8, MUTED, false, "left", 10);
    textBox(layer, a, "GEONORM · J. A. L. ZAVALETA REYES", 700, 1867, 306, 22, 8, MUTED, false, "right", 10);
}

function title(layer, a, value, subtitle, y, h, size) {
    textBox(layer, a, value, 112, y || 172, 894, h || 132, size || 28, NAVY, true, "left", (size || 28) * 1.12);
    if (subtitle) textBox(layer, a, subtitle, 112, (y || 172) + (h || 132) + 16, 894, 80, 13, MUTED, false, "left", 16);
}

function labelBar(layer, a, value, x, y, w, accent) {
    rect(layer, a, x, y, w, 46, accent, null, 0);
    textBox(layer, a, value.toUpperCase(), x + 16, y + 13, w - 32, 22, 10, WHITE, true, "left", 12);
}

function chartBar(layer, a, label, value, x, y, w, accent) {
    textBox(layer, a, label, x, y, w, 24, 10, NAVY, true, "left", 12);
    rect(layer, a, x, y + 33, w, 26, LINE, null, 6);
    rect(layer, a, x, y + 33, w * value, 26, accent, null, 6);
    textBox(layer, a, value.toFixed(3), x + w * value - 66, y + 38, 58, 18, 9, WHITE, true, "right", 10);
}

function page1(doc, layer, a) {
    base(layer, a, 1, "Trabajo técnico científico · E-3 Geociencias digitales: IA, modelamiento y geodatos", TEAL, 250, 630);
    var approved = "GeoNormPy y GeoNormML: Un ecosistema abierto en Python e integración de algoritmos determinísticos para el cálculo normativo y clasificación de rocas ígneas en el Perú";
    textBox(layer, a, approved, 112, 175, 894, 310, 29, NAVY, true, "left", 33);
    textBox(layer, a, "Geoquímica de roca total + norma CIPW + aprendizaje supervisado bajo una cadena reproducible.", 112, 518, 894, 54, 14, INK, false, "left", 17);
    placedImage(layer, a, DASH_PATH, 112, 625, 894, 500, 12, TEAL, PAPER_LIGHT);
    metricCard(layer, a, "2 887", "muestras · dataset v5", 112, 1170, 205, 116, TEAL, true);
    metricCard(layer, a, "19", "clases litológicas", 337, 1170, 205, 116, TEAL, true);
    metricCard(layer, a, "4", "modelos productivos", 562, 1170, 205, 116, TEAL, true);
    metricCard(layer, a, "16/16", "pruebas GeoNormPy", 787, 1170, 219, 116, TEAL, true);
    textBox(layer, a, "Jordan Angel Luciano Zavaleta Reyes", 112, 1370, 680, 36, 17, NAVY, true, "left", 20);
    textBox(layer, a, "Universidad Nacional de Ingeniería\rFacultad de Ingeniería Geológica, Minera y Metalúrgica\rAv. Túpac Amaru 210, Rímac 15333, Lima, Perú\rjordan.zavaleta.r@uni.pe", 112, 1422, 650, 115, 11, MUTED, false, "left", 15);
    rect(layer, a, 112, 1615, 894, 118, NAVY, null, 0);
    textBox(layer, a, "PROPÓSITO", 140, 1640, 140, 24, 10, GOLD, true, "left", 12);
    textBox(layer, a, "Transformar composición en evidencia trazable sin reemplazar el criterio geológico.", 295, 1637, 675, 54, 14, WHITE, true, "left", 18);
}

function page2(doc, layer, a) {
    base(layer, a, 2, "Problema y objetivo", COPPER, 300, 520);
    title(layer, a, "Una cadena fragmentada no es reproducible", "El reto no era únicamente clasificar: era poder reconstruir cada decisión desde los óxidos hasta el modelo exportado.", 172, 92, 28);
    var cards = [
        ["PLANILLAS", "Limpieza manual, versiones divergentes y reglas difíciles de auditar."],
        ["CIPW EXTERNO", "Dependencia de herramientas ajenas al pipeline y trazabilidad parcial."],
        ["MODELOS", "Selección por score aislado, sin separar calidad analítica y predictores."],
        ["TRANSFERENCIA", "Artefactos sin contrato explícito de variables, dominio ni advertencias."]
    ];
    for (var i = 0; i < cards.length; i++) sectionCard(layer, a, cards[i][0], cards[i][1], 112, 455 + i * 205, 894, 156, COPPER, "0" + (i + 1));
    rect(layer, a, 112, 1360, 894, 300, NAVY, null, 12);
    textBox(layer, a, "OBJETIVO", 145, 1395, 180, 25, 10, GOLD, true, "left", 12);
    textBox(layer, a, "Construir un ecosistema abierto y auditable que integre curación, cálculo normativo CIPW, benchmarking y exportación de modelos por dominio litológico.", 145, 1448, 820, 110, 18, WHITE, true, "left", 23);
    textBox(layer, a, "Principio rector · QA/QC describe la calidad del dato; no se usa como atajo predictivo.", 145, 1588, 820, 40, 11, "CFE0E5", false, "left", 14);
}

function page3(doc, layer, a) {
    base(layer, a, 3, "Arquitectura reproducible", TEAL, 390, 790);
    title(layer, a, "De óxidos a modelos transferibles, sin saltos opacos", "Cinco etapas enlazadas conservan datos, criterios y artefactos de evaluación.", 172, 100, 28);
    var stages = [
        ["01", "ENTRADA", "Óxidos mayores · metadatos · coordenadas", COPPER],
        ["02", "CURACIÓN", "Nombres · QA/QC · dominios", GOLD],
        ["03", "GEONORMPY", "CIPW · balance · diagnósticos", TEAL],
        ["04", "GEONORMML", "Features · CV 5-fold · benchmark", GREEN],
        ["05", "SALIDA", "Modelos · métricas · contrato", NAVY]
    ];
    for (var i = 0; i < stages.length; i++) {
        sectionCard(layer, a, stages[i][1], stages[i][2], 160, 420 + i * 220, 798, 158, stages[i][3], stages[i][0]);
        if (i < stages.length - 1) textBox(layer, a, "↓", 500, 585 + i * 220, 100, 36, 20, stages[i][3], true, "center", 22);
    }
    rect(layer, a, 112, 1590, 894, 110, TEAL_LIGHT, null, 10);
    textBox(layer, a, "Cada predicción conserva dominio, variables, algoritmo, métricas y columnas requeridas.", 140, 1621, 838, 42, 13, NAVY, true, "center", 17);
}

function page4(doc, layer, a) {
    base(layer, a, 4, "Datos y trazabilidad", TEAL, 520, 850);
    title(layer, a, "Dataset v5: 2 887 muestras y 19 clases", "El corte espacial actualizado conserva la separación operativa entre rocas volcánicas y plutónicas.", 172, 92, 28);
    placedImage(layer, a, MAP_PATH, 112, 410, 540, 1110, 10, TEAL, WHITE);
    metricCard(layer, a, "1 821", "volcánicas · 9 clases", 690, 455, 282, 126, TEAL, true);
    metricCard(layer, a, "1 066", "plutónicas · 10 clases", 690, 610, 282, 126, COPPER, true);
    metricCard(layer, a, "100 %", "CIPW calculado", 690, 765, 282, 126, GREEN, true);
    rect(layer, a, 690, 935, 282, 355, WHITE, LINE, 9, 1);
    labelBar(layer, a, "Criterios", 690, 935, 282, NAVY);
    bulletList(layer, a, ["Nombres estandarizados.", "Clases raras consolidadas.", "QA/QC separado del ML.", "ID final estable."], 716, 1010, 230, 60, 12, TEAL, INK);
    rect(layer, a, 690, 1335, 282, 185, COPPER_LIGHT, null, 9);
    textBox(layer, a, "FUENTES", 714, 1365, 230, 25, 10, COPPER, true, "left", 12);
    textBox(layer, a, "INGEMMET · GEOROC · USGS", 714, 1410, 230, 45, 13, NAVY, true, "left", 16);
    textBox(layer, a, "Cobertura regional del Perú", 714, 1475, 230, 24, 10, MUTED, false, "left", 12);
    rect(layer, a, 112, 1570, 860, 112, NAVY, null, 8);
    textBox(layer, a, "TRAZABILIDAD", 140, 1600, 150, 24, 9, GOLD, true, "left", 11);
    textBox(layer, a, "dataset → split → benchmark → modelo → catálogo", 305, 1596, 630, 34, 15, WHITE, true, "left", 18);
    textBox(layer, a, "La versión y el dominio acompañan cada artefacto.", 305, 1641, 630, 24, 10, "D5E5E9", false, "left", 12);
}

function page5(doc, layer, a) {
    base(layer, a, 5, "Metodología · GeoNormPy", GREEN, 350, 820);
    title(layer, a, "CIPW determinístico, diagnosticable y reproducible", "GeoNormPy reemplaza la etapa externa y devuelve minerales normativos junto con controles interpretativos.", 172, 100, 28);
    var steps = [
        ["01", "NORMALIZACIÓN ANHIDRA", "Reescala los óxidos disponibles."],
        ["02", "ESPECIACIÓN DEL HIERRO", "Maneja FeO, Fe₂O₃ y FeOT."],
        ["03", "ASIGNACIÓN NORMATIVA", "Distribuye fases en secuencia CIPW."],
        ["04", "SATURACIÓN", "Reporta sílice y estado de alúmina."],
        ["05", "BALANCE DE MASA", "Cuantifica el error de reconstrucción."]
    ];
    for (var i = 0; i < steps.length; i++) sectionCard(layer, a, steps[i][1], steps[i][2], 112, 420 + i * 166, 630, 126, GREEN, steps[i][0]);
    metricCard(layer, a, "16/16", "pruebas aprobadas", 778, 445, 208, 122, GREEN, true);
    metricCard(layer, a, "99.45 %", "balance ≤ 0.10", 778, 595, 208, 122, GREEN, true);
    metricCard(layer, a, "2 887", "cálculos sin error", 778, 745, 208, 122, GREEN, true);
    rect(layer, a, 778, 910, 208, 360, GREEN_LIGHT, GREEN, 9, 1);
    textBox(layer, a, "SALIDAS", 800, 940, 164, 24, 10, GREEN, true, "left", 12);
    bulletList(layer, a, ["Minerales normativos", "Saturación en sílice", "Estado de alúmina", "Modo de hierro", "Advertencias", "Error de balance"], 802, 995, 160, 47, 10, GREEN, INK);
    rect(layer, a, 112, 1330, 874, 320, NAVY, null, 12);
    textBox(layer, a, "ALCANCE CORRECTO", 145, 1365, 260, 25, 10, GOLD, true, "left", 12);
    textBox(layer, a, "La norma CIPW es una mineralogía ideal calculada desde química de roca total. Sirve como contraste composicional y descriptor reproducible; no sustituye una medición modal ni una clasificación QAPF formal.", 145, 1420, 810, 132, 17, WHITE, true, "left", 22);
    textBox(layer, a, "Umbral operativo de balance: error ≤ 0.10.", 145, 1580, 810, 28, 10, "D5E5E9", false, "left", 12);
}

function page6(doc, layer, a) {
    base(layer, a, 6, "Metodología · GeoNormML", TEAL, 400, 860);
    title(layer, a, "Comparar modelos sin confundir contexto con fuga de información", "La selección combina desempeño, disponibilidad, estabilidad y coherencia petrológica.", 172, 112, 27);
    var sets = [
        ["OXIDES_CORE", "Óxidos mayores, LOI y suma de óxidos", COPPER],
        ["CIPW", "Minerales normativos calculados por GeoNormPy", GREEN],
        ["COMBINED_CORE", "Óxidos + CIPW · baseline transferible", TEAL],
        ["ENRICHED_SPATIAL", "Core + índices + latitud + distancia a la fosa", NAVY]
    ];
    for (var i = 0; i < sets.length; i++) sectionCard(layer, a, sets[i][0], sets[i][1], 112, 420 + i * 166, 894, 126, sets[i][2], null);
    var xvals = [112, 420, 728];
    var heads = ["VALIDACIÓN", "ALGORITMOS", "VARIABLES EXCLUIDAS"];
    var accents = [TEAL, GREEN, COPPER];
    var lists = [
        ["CV estratificada", "5 pliegues", "Métricas multiclase", "Semilla fija"],
        ["Random Forest", "XGBoost", "SVM + PCA", "Imputación por mediana"],
        ["Quality_Flag", "Geol_Unit", "Metal_Belt", "UTM_Zone"]
    ];
    for (var j = 0; j < 3; j++) {
        rect(layer, a, xvals[j], 1125, 278, 340, WHITE, LINE, 8, 1);
        labelBar(layer, a, heads[j], xvals[j], 1125, 278, accents[j]);
        bulletList(layer, a, lists[j], xvals[j] + 24, 1205, 230, 57, 11, accents[j], INK);
    }
    rect(layer, a, 112, 1525, 894, 150, COPPER_LIGHT, null, 9);
    textBox(layer, a, "REGLA", 140, 1558, 90, 24, 9, COPPER, true, "left", 11);
    textBox(layer, a, "Una variable no se acepta solo porque eleva la exactitud: debe ser disponible, auditable y geológicamente defendible.", 250, 1552, 720, 70, 14, NAVY, true, "left", 18);
}

function page7(doc, layer, a) {
    base(layer, a, 7, "Resultados · baselines", TEAL, 410, 800);
    title(layer, a, "Sin coordenadas: dos baselines transferibles", "Los modelos core son la referencia principal cuando no existe contexto espacial válido.", 172, 92, 28);
    var xs = [112, 574];
    var domains = ["VOLCÁNICAS", "PLUTÓNICAS"];
    var models = ["XGBoost", "Random Forest"];
    var colors = [TEAL, COPPER];
    var vals = [["0.806", "0.956", "0.718", "0.803"], ["0.615", "0.870", "0.523", "0.586"]];
    var labs = ["CA", "AUC macro", "MCC", "F1 ponderado"];
    for (var i = 0; i < 2; i++) {
        rect(layer, a, xs[i], 420, 432, 550, WHITE, colors[i], 10, 1.2);
        labelBar(layer, a, domains[i], xs[i], 420, 432, colors[i]);
        textBox(layer, a, models[i], xs[i] + 28, 520, 376, 42, 23, NAVY, true, "left", 27);
        textBox(layer, a, "combined_core", xs[i] + 28, 578, 376, 24, 11, colors[i], true, "left", 13);
        for (var j = 0; j < 4; j++) {
            var mx = xs[i] + 28 + (j % 2) * 188;
            var my = 650 + Math.floor(j / 2) * 120;
            metricCard(layer, a, vals[i][j], labs[j], mx, my, 164, 96, colors[i], false);
        }
        rect(layer, a, xs[i] + 28, 895, 376, 50, PAPER_LIGHT, colors[i], 6, 1);
        textBox(layer, a, i === 0 ? "Mayor separabilidad geoquímica." : "Mayor continuidad composicional.", xs[i] + 40, 910, 352, 22, 10, colors[i], true, "center", 12);
    }
    rect(layer, a, 112, 1020, 894, 465, PAPER_LIGHT, LINE, 10, 1);
    rect(layer, a, 140, 1060, 38, 14, TEAL, null, 3);
    textBox(layer, a, "BASELINE", 190, 1057, 120, 20, 9, MUTED, true, "left", 11);
    rect(layer, a, 350, 1060, 38, 14, GREEN, null, 3);
    textBox(layer, a, "CON CONTEXTO ESPACIAL", 400, 1057, 230, 20, 9, MUTED, true, "left", 11);
    chartBar(layer, a, "Exactitud · VOL", 0.8056, 140, 1120, 810, TEAL);
    chartBar(layer, a, "Exactitud espacial · VOL", 0.8281, 140, 1205, 810, GREEN);
    chartBar(layer, a, "Exactitud · PLU", 0.6154, 140, 1290, 810, COPPER);
    chartBar(layer, a, "Exactitud espacial · PLU", 0.6567, 140, 1375, 810, GREEN);
    rect(layer, a, 112, 1535, 894, 150, NAVY, null, 10);
    textBox(layer, a, "LECTURA", 142, 1567, 110, 24, 9, GOLD, true, "left", 11);
    textBox(layer, a, "La menor exactitud plutónica es coherente con fronteras que dependen de proporciones modales y textura, no solo de química total.", 270, 1562, 700, 72, 14, WHITE, true, "left", 18);
}

function page8(doc, layer, a) {
    base(layer, a, 8, "Resultados · contexto espacial", GREEN, 470, 880);
    title(layer, a, "El contexto espacial mejora el desempeño dentro del dominio muestreado", "Latitud y distancia a la fosa aportan estructura regional sin incorporar unidad geológica ni cinturón metalogenético.", 172, 126, 27);
    placedImage(layer, a, DASH_PATH, 112, 455, 894, 610, 10, GREEN, WHITE);
    metricCard(layer, a, "+2.25 pp", "exactitud VOL", 112, 1110, 266, 120, GREEN, true);
    metricCard(layer, a, "+4.13 pp", "exactitud PLU", 406, 1110, 266, 120, GREEN, true);
    metricCard(layer, a, "0.751", "MCC espacial VOL", 700, 1110, 306, 120, GREEN, true);
    rect(layer, a, 112, 1270, 430, 310, GREEN_LIGHT, GREEN, 9, 1);
    labelBar(layer, a, "Qué aporta", 112, 1270, 430, GREEN);
    bulletList(layer, a, ["Posición longitudinal del arco.", "Distancia transversal a la fosa.", "Índices petrológicos derivados."], 142, 1350, 370, 68, 12, GREEN, INK);
    rect(layer, a, 576, 1270, 430, 310, SOFT_RED, COPPER, 9, 1);
    labelBar(layer, a, "Límite", 576, 1270, 430, COPPER);
    bulletList(layer, a, ["CV estratificada, no espacial.", "Puede captar autocorrelación regional.", "Requiere validación por bloques."], 606, 1350, 370, 68, 12, COPPER, INK);
    rect(layer, a, 112, 1620, 894, 86, NAVY, null, 8);
    textBox(layer, a, "Uso recomendado: coordenadas válidas y contexto compatible con los Andes peruanos.", 140, 1643, 838, 34, 12, WHITE, true, "center", 15);
}

function page9(doc, layer, a) {
    base(layer, a, 9, "Discusión y límites", COPPER, 500, 830);
    title(layer, a, "CIPW describe composición; la litología conserva su autoridad geológica", "Estas matrices muestran saturación normativa por clase reportada. No validan moda ni sustituyen QAPF.", 172, 126, 27);
    placedImage(layer, a, VOL_CIPW_PATH, 112, 455, 894, 470, 8, TEAL, WHITE);
    placedImage(layer, a, PLU_CIPW_PATH, 112, 970, 894, 470, 8, COPPER, WHITE);
    rect(layer, a, 112, 1490, 894, 210, NAVY, null, 10);
    textBox(layer, a, "TRES LÍMITES EXPLÍCITOS", 140, 1522, 310, 24, 9, GOLD, true, "left", 11);
    bulletList(layer, a, ["La litología reportada no es una nueva medición modal.", "Las probabilidades ML apoyan la revisión; no asignan autoridad petrográfica.", "La generalización espacial externa aún debe demostrarse."], 142, 1570, 820, 43, 11, GOLD, WHITE);
}

function page10(doc, layer, a) {
    base(layer, a, 10, "Conclusiones y acceso", TEAL, 380, 930);
    title(layer, a, "GeoNorm convierte una cadena dispersa en evidencia auditable", "El aporte central es separar cálculo determinístico, aprendizaje probabilístico y decisión geológica.", 172, 112, 27);
    var statements = [
        "GeoNormPy integra CIPW, diagnósticos y balance de masa en Python.",
        "GeoNormML selecciona modelos por dominio y conserva contratos de entrada.",
        "Los baselines operan sin coordenadas; los modelos espaciales añaden contexto regional.",
        "La suite apoya —no reemplaza— el criterio petrológico y la autoridad modal QAPF."
    ];
    for (var i = 0; i < statements.length; i++) sectionCard(layer, a, "", statements[i], 112, 420 + i * 174, 894, 132, TEAL, "0" + (i + 1));
    rect(layer, a, 112, 1180, 560, 430, NAVY, null, 12);
    textBox(layer, a, "CÓDIGO ABIERTO", 146, 1217, 260, 24, 10, GOLD, true, "left", 12);
    textBox(layer, a, "GeoNormPy", 146, 1265, 400, 48, 26, WHITE, true, "left", 30);
    textBox(layer, a, "pip install geonormpy", 146, 1335, 460, 34, 16, "BFE3E6", true, "left", 19);
    textBox(layer, a, "github.com/jordan-zav/GeoNormPy", 146, 1405, 460, 28, 11, WHITE, true, "left", 13);
    textBox(layer, a, "Motor CIPW bajo licencia abierta. GeoNormML se transfiere mediante artefactos versionados para uso académico.", 146, 1470, 470, 90, 11, "D4E4E8", false, "left", 15);
    placedImage(layer, a, QR_PATH, 710, 1180, 296, 296, 28, TEAL, WHITE);
    textBox(layer, a, "REPOSITORIO GEONORMPY", 710, 1502, 296, 24, 10, TEAL, true, "center", 12);
    textBox(layer, a, "jordan.zavaleta.r@uni.pe", 690, 1582, 336, 26, 10, NAVY, true, "center", 12);
    rect(layer, a, 112, 1665, 894, 82, TEAL_LIGHT, null, 8);
    textBox(layer, a, "Siguiente etapa · validación externa y evaluación por bloques espaciales.", 136, 1688, 846, 32, 12, NAVY, true, "center", 15);
}

function auditFonts(doc) {
    var counts = {};
    var nonArial = [];
    for (var i = 0; i < doc.textFrames.length; i++) {
        try {
            var name = doc.textFrames[i].textRange.characterAttributes.textFont.name;
            counts[name] = (counts[name] || 0) + 1;
            if (name.indexOf("Arial") !== 0) nonArial.push(name);
        } catch (e) {
            nonArial.push("<mixed-or-missing>");
        }
    }
    var result = "";
    for (var key in counts) result += key + ":" + counts[key] + ";";
    return { summary: result, nonArial: nonArial };
}

function main() {
    var required = [MAP_PATH, DASH_PATH, VOL_CIPW_PATH, PLU_CIPW_PATH, QR_PATH];
    for (var i = 0; i < required.length; i++) {
        if (!required[i].exists) throw new Error("Falta el recurso: " + required[i].fsName);
    }

    var doc = app.documents.add(DocumentColorSpace.RGB, W, H, 10, DocumentArtboardLayout.GridByRow, 100, 5);
    doc.rulerUnits = RulerUnits.Points;
    var names = ["01_PORTADA", "02_PROBLEMA", "03_ARQUITECTURA", "04_DATOS", "05_GEONORMPY", "06_GEONORMML", "07_BASELINES", "08_ESPACIAL", "09_LIMITES", "10_CONCLUSIONES"];
    var builders = [page1, page2, page3, page4, page5, page6, page7, page8, page9, page10];

    var initial = doc.layers[0];
    initial.name = names[0];
    for (var p = 0; p < 10; p++) {
        var layer = p === 0 ? initial : doc.layers.add();
        layer.name = names[p];
        builders[p](doc, layer, artboardInfo(doc, p));
        doc.artboards[p].name = names[p];
    }

    var audit = auditFonts(doc);
    if (audit.nonArial.length > 0) throw new Error("Se detectaron fuentes no Arial: " + audit.nonArial.join(", "));

    var aiOptions = new IllustratorSaveOptions();
    aiOptions.pdfCompatible = true;
    aiOptions.compressed = true;
    aiOptions.embedICCProfile = true;
    doc.saveAs(AI_PATH, aiOptions);

    var pngOptions = new ExportOptionsPNG24();
    pngOptions.antiAliasing = true;
    pngOptions.transparency = false;
    pngOptions.artBoardClipping = true;
    pngOptions.horizontalScale = 100;
    pngOptions.verticalScale = 100;
    for (var n = 0; n < 10; n++) {
        doc.artboards.setActiveArtboardIndex(n);
        var number = (n + 1 < 10 ? "0" : "") + (n + 1);
        doc.exportFile(new File(PREVIEW.fsName + "/GeoNorm_" + number + ".png"), ExportType.PNG24, pngOptions);
    }

    var pdfOptions = new PDFSaveOptions();
    pdfOptions.preserveEditability = true;
    pdfOptions.viewAfterSaving = false;
    pdfOptions.artboardRange = "1-10";
    try { pdfOptions.pDFPreset = "[High Quality Print]"; } catch (ignorePreset) {}
    doc.saveAs(PDF_PATH, pdfOptions);
    doc.close(SaveOptions.DONOTSAVECHANGES);

    return "AI=" + AI_PATH.fsName + "\nPDF=" + PDF_PATH.fsName + "\nfonts=" + audit.summary;
}

main();
