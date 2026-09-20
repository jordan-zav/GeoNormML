from __future__ import annotations

import re
import unicodedata

import pandas as pd

from geonormml.config import PROJECT_ROOT

INPUT_PATH = PROJECT_ROOT / "Dataset" / "Filtered" / "Merge_Filtered.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "Dataset" / "Filtered" / "processed"
OUTPUT_XLSX = OUTPUT_DIR / "Merge_Filtered_name_normalized.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "name_normalization_review.csv"
SUMMARY_PATH = OUTPUT_DIR / "name_normalization_summary.txt"


TEXTURE_TERMS = {
    "ignimbritic tuff": "toba ignimbritica",
    "tuff": "toba",
    "toba": "toba",
    "toba cristalina": "toba cristalina",
    "toba litica": "toba litica",
    "toba vitrea": "toba vitrea",
    "tufo": "tufo",
    "tufo de cristales": "tufo de cristales",
    "porfido": "porfido",
    "pitchstone": "pitchstone",
}

ROCK_TRANSLATIONS = {
    "alkali basalt": "basalto alcalino",
    "calc-alkali basalt": "basalto calcoalcalino",
    "basalt": "basalto",
    "basaltic-andesite": "andesita basaltica",
    "basaltic trachyandesite": "traquiandesita basaltica",
    "basaltic-trachyandesite": "traquiandesita basaltica",
    "basanite": "basanita",
    "benmoreite": "benmoreita",
    "dacite": "dacita",
    "diorite": "diorita",
    "dolerite": "dolerita",
    "gabbro": "gabro",
    "gabbrodiorite": "gabrodiorita",
    "granite": "granito",
    "granodiorite": "granodiorita",
    "latite": "latita",
    "lamproite": "lamproita",
    "lamprophyre": "lamprofiro",
    "monzodiorite": "monzodiorita",
    "monzogabbro": "monzogabro",
    "monzogranite": "monzogranito",
    "monzonite": "monzonita",
    "mugearite": "mugearita",
    "rhyodacite": "riodacita",
    "rhyolite": "riolita",
    "shoshonite": "shoshonita",
    "syenite": "sienita",
    "syenogranite": "sienogranito",
    "tonalite": "tonalita",
    "trachyandesite": "traquiandesita",
    "trachybasalt": "traquibasalto",
    "trachydacite": "traquidacita",
    "trachyte": "traquita",
    "adamelita": "adamelita",
    "andesite": "andesita",
    "aplita": "aplita",
    "arenisca tobacea": "arenisca tobacea",
    "gabro": "gabro",
    "gabrodiorita": "gabrodiorita",
    "gneis": "gneis",
    "esquisto": "esquisto",
    "anfibolita": "anfibolita",
    "granito": "granito",
    "granodiorita": "granodiorita",
    "metamonzogranito": "metamonzogranito",
    "metatonalita": "metatonalita",
    "monzodiorita": "monzodiorita",
    "monzogabro": "monzogabro",
    "monzogranito": "monzogranito",
    "monzonita": "monzonita",
    "ortogranito": "ortogranito",
    "porfido dacita": "dacita",
    "porfido diorita": "diorita",
    "porfido riolita": "riolita",
    "porfido riodacita": "riodacita",
    "porfido": "porfido",
    "riodacita": "riodacita",
    "riolita": "riolita",
    "sienita": "sienita",
    "sienogranito": "sienogranito",
    "tonalita": "tonalita",
    "traquita": "traquita",
    "andesita basaltica": "andesita basaltica",
    "basalto andesita": "andesita basaltica",
}

MINERAL_TRANSLATIONS = {
    "augite": "augita",
    "biotite": "biotita",
    "clinopyroxene": "clinopiroxeno",
    "hornblende": "hornblenda",
    "hypersthene": "hiperstena",
    "olivine": "olivino",
    "orthopyroxene": "ortopiroxeno",
    "plagioclase": "plagioclasa",
    "pyroxene": "piroxeno",
    "quartz": "cuarzo",
    "tourmaline": "turmalina",
    "alkali feldspar": "feldespato alcalino",
    "alkalifeldspar": "feldespato alcalino",
    "amphibole": "anfibol",
    "mineralizacion": "mineralizacion",
}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def clean_text(text: str) -> str:
    text = strip_accents(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def translate_mineral_phrase(text: str) -> str:
    cleaned = clean_text(text).replace("-", " ")
    for eng, es in sorted(MINERAL_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        cleaned = cleaned.replace(eng, es)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_single_label(text: str) -> tuple[str | None, str | None, str | None]:
    raw = clean_text(text)

    if raw in {"", "not given"}:
        return None, None, None

    if raw in {"ocoita"}:
        return "andesita", "ocoita", None

    if raw in TEXTURE_TERMS:
        return TEXTURE_TERMS[raw], None, None

    sec_name = None
    minerals: list[str] = []

    if raw.startswith("porfido "):
        remainder = raw.replace("porfido ", "", 1).strip()
        normalized = ROCK_TRANSLATIONS.get(remainder, remainder)
        return normalized, "porfido", None

    if raw.startswith("toba "):
        normalized = TEXTURE_TERMS.get(raw, "toba")
        return normalized, None, None

    if raw.startswith("tufo"):
        normalized = TEXTURE_TERMS.get(raw, raw)
        return normalized, None, None

    if raw == "pitchstone":
        return "riolita", "vidrio volcanico", None

    if raw.endswith(" con cuarzo"):
        base = raw.replace(" con cuarzo", "")
        normalized = ROCK_TRANSLATIONS.get(base, base)
        minerals.append("cuarzo")
        return normalized, None, "; ".join(dict.fromkeys(minerals))

    if raw.endswith(" con mineralizacion"):
        base = raw.replace(" con mineralizacion", "")
        normalized = ROCK_TRANSLATIONS.get(base, base)
        return normalized, "mineralizacion", None

    if raw == "granito rojo":
        return "granito", "rojo", None

    if raw == "andesita (ocoita)":
        return "andesita", "ocoita", None

    if raw == "andesitas con esferulitos":
        return "andesita", "esferulitica", None

    if raw == "basalto esquistoceados":
        return "basalto", "esquistoso", None

    if "," in raw:
        main_part, descriptor = [part.strip() for part in raw.split(",", 1)]
        normalized_main = ROCK_TRANSLATIONS.get(main_part, main_part)
        descriptor_clean = translate_mineral_phrase(descriptor)
        if descriptor_clean:
            minerals.append(descriptor_clean)
        return normalized_main, sec_name, "; ".join(dict.fromkeys(minerals)) if minerals else None

    normalized = ROCK_TRANSLATIONS.get(raw, raw)
    return normalized, sec_name, "; ".join(dict.fromkeys(minerals)) if minerals else None


def normalize_rock_name(raw_value: object) -> tuple[str | None, str | None, str | None, str]:
    if pd.isna(raw_value):
        return None, None, None, "missing_original"

    raw_text = str(raw_value).strip()
    if not raw_text:
        return None, None, None, "missing_original"

    slash_parts = [part.strip() for part in raw_text.split("/") if part.strip()]
    normalized_parts: list[tuple[str | None, str | None, str | None]] = []
    for part in slash_parts if slash_parts else [raw_text]:
        normalized_parts.append(normalize_single_label(part))

    main_candidates = [part for part in normalized_parts if part[0]]
    if not main_candidates:
        return None, None, None, "no_valid_label"

    main_name, main_sec, main_min = main_candidates[0]

    secondary_names: list[str] = []
    minerals: list[str] = []

    if main_sec:
        secondary_names.append(main_sec)
    if main_min:
        minerals.extend([m.strip() for m in main_min.split(";") if m.strip()])

    for other_name, other_sec, other_min in main_candidates[1:]:
        if other_name and other_name != main_name and other_name not in secondary_names:
            secondary_names.append(other_name)
        if other_sec and other_sec not in secondary_names:
            secondary_names.append(other_sec)
        if other_min:
            minerals.extend([m.strip() for m in other_min.split(";") if m.strip()])

    review_flags: list[str] = []
    if "/" in raw_text:
        review_flags.append("had_slash")
    if "," in raw_text:
        review_flags.append("had_minerals_in_name")
    if "not given" in clean_text(raw_text):
        review_flags.append("had_not_given")
    if main_name in {"toba", "toba cristalina", "toba litica", "toba vitrea", "tufo", "tufo de cristales", "porfido"}:
        review_flags.append("textural_name")
    if main_name in {"gneis", "esquisto", "anfibolita", "arenisca tobacea"}:
        review_flags.append("non_igneous_or_metamorphic")
    if main_name in {"metamonzogranito", "metatonalita", "ortogranito"}:
        review_flags.append("meta_or_ortho_prefix")
    if main_name not in {
        "adamelita",
        "andesita",
        "andesita basaltica",
        "aplita",
        "arenisca tobacea",
        "basalto",
        "basalto alcalino",
        "basalto calcoalcalino",
        "basanita",
        "benmoreita",
        "dacita",
        "diorita",
        "dolerita",
        "gabro",
        "gabrodiorita",
        "gneis",
        "granito",
        "granodiorita",
        "lamprofiro",
        "lamproita",
        "latita",
        "metamonzogranito",
        "metatonalita",
        "monzodiorita",
        "monzogabro",
        "monzogranito",
        "monzonita",
        "mugearita",
        "ortogranito",
        "porfido",
        "riodacita",
        "riolita",
        "shoshonita",
        "sienita",
        "sienogranito",
        "toba",
        "toba cristalina",
        "toba ignimbritica",
        "toba litica",
        "toba vitrea",
        "tonalita",
        "traquibasalto",
        "traquidacita",
        "traquiandesita",
        "traquiandesita basaltica",
        "traquita",
        "tufo",
        "tufo de cristales",
    }:
        review_flags.append("check_main_label")

    sec_name = "; ".join(dict.fromkeys([name for name in secondary_names if name])) or None
    mineral_text = "; ".join(dict.fromkeys(minerals)) or None
    return main_name, sec_name, mineral_text, "; ".join(review_flags) if review_flags else "ok"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(INPUT_PATH, sheet_name="merge")
    original_rows = len(df)

    # Remove rows without a rock name before normalization.
    df = df[df["ROCK_NAME"].notna()].copy()
    df["ROCK_NAME_RAW"] = df["ROCK_NAME"]

    normalized = df["ROCK_NAME_RAW"].apply(normalize_rock_name)
    normalized_df = pd.DataFrame(
        normalized.tolist(),
        columns=["ROCK_NAME", "SEC_ROCK_NAME", "MIN", "NAME_REVIEW_FLAG"],
        index=df.index,
    )

    df["ROCK_NAME"] = normalized_df["ROCK_NAME"]
    df["SEC_ROCK_NAME"] = normalized_df["SEC_ROCK_NAME"]
    df["MIN"] = normalized_df["MIN"]
    df["NAME_REVIEW_FLAG"] = normalized_df["NAME_REVIEW_FLAG"]

    rows_after_drop_missing = len(df)
    df = df[df["ROCK_NAME"].notna()].copy()

    freq = (
        df["ROCK_NAME"]
        .fillna("<<NULL_AFTER_NORMALIZATION>>")
        .value_counts()
        .rename_axis("ROCK_NAME")
        .reset_index(name="count")
    )
    freq.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="merge_normalized", index=False)
        freq.to_excel(writer, sheet_name="rock_name_frequency", index=False)

    summary_lines = [
        f"original_rows: {original_rows}",
        f"rows_after_drop_missing_rock_name: {rows_after_drop_missing}",
        f"dropped_missing_rock_name: {original_rows - rows_after_drop_missing}",
        f"rows_after_drop_invalid_normalized_name: {len(df)}",
        f"dropped_invalid_normalized_name: {rows_after_drop_missing - len(df)}",
        f"unique_rock_name_after_normalization: {df['ROCK_NAME'].nunique(dropna=True)}",
        "",
        "review_flag_counts:",
        df["NAME_REVIEW_FLAG"].value_counts(dropna=False).to_string(),
        "",
        "top_40_rock_names_after_normalization:",
        df["ROCK_NAME"].value_counts().head(40).to_string(),
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    print(OUTPUT_XLSX)
    print(OUTPUT_CSV)
    print(SUMMARY_PATH)
    print("\n" + "\n".join(summary_lines))


if __name__ == "__main__":
    main()
