#!/usr/bin/env python3
"""Genera js/portales.generated.js desde el Excel maestro.

No requiere dependencias externas: lee el .xlsx como contenedor ZIP/XML usando
únicamente la biblioteca estándar de Python.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = ROOT / "datos" / "portal_investigacion_unphu.xlsx"
OUTPUT_PATH = ROOT / "js" / "portales.generated.js"
ICONS_DIR = ROOT / "assets" / "icons"
SHEET_NAME = "PORTALES"

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS}

REQUIRED_COLUMNS = [
    "ID",
    "Nombre",
    "Descripcion",
    "URL",
    "Icono",
    "Categoria",
    "Orden",
    "Estado",
    "Destacado",
]


def normalize(text: object) -> str:
    value = "" if text is None else str(text)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
    value = 0
    for ch in letters:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value - 1


def read_shared_strings(book: zipfile.ZipFile) -> list[str]:
    try:
        xml = book.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml)
    values: list[str] = []
    for si in root.findall(f"{{{MAIN_NS}}}si"):
        parts = [node.text or "" for node in si.iter(f"{{{MAIN_NS}}}t")]
        values.append("".join(parts))
    return values


def worksheet_path(book: zipfile.ZipFile, sheet_name: str) -> str:
    workbook_root = ET.fromstring(book.read("xl/workbook.xml"))
    rel_id = None
    for sheet in workbook_root.findall("m:sheets/m:sheet", NS):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{REL_NS}}}id")
            break
    if not rel_id:
        raise ValueError(f"No se encontró la hoja '{sheet_name}' en el Excel maestro.")

    rels_root = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
    target = None
    for rel in rels_root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        if rel.attrib.get("Id") == rel_id:
            target = rel.attrib.get("Target")
            break
    if not target:
        raise ValueError(f"No se pudo resolver la hoja '{sheet_name}'.")

    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return "xl/" + target.lstrip("/")


def cell_value(cell: ET.Element, shared: list[str]) -> object:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))

    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return ""

    raw = value_node.text
    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return raw
    if cell_type == "b":
        return raw == "1"
    if cell_type in {"str", "e"}:
        return raw

    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def read_rows(path: Path) -> list[list[object]]:
    with zipfile.ZipFile(path) as book:
        shared = read_shared_strings(book)
        sheet_xml = book.read(worksheet_path(book, SHEET_NAME))

    root = ET.fromstring(sheet_xml)
    rows: list[list[object]] = []
    for row in root.findall(".//m:sheetData/m:row", NS):
        cells = row.findall("m:c", NS)
        if not cells:
            continue
        max_col = max(col_index(c.attrib.get("r", "A1")) for c in cells)
        values: list[object] = [""] * (max_col + 1)
        for cell in cells:
            values[col_index(cell.attrib.get("r", "A1"))] = cell_value(cell, shared)
        rows.append(values)
    return rows


def canonical_headers(headers: list[object]) -> dict[int, str]:
    required = {normalize(name): name for name in REQUIRED_COLUMNS}
    result: dict[int, str] = {}
    for idx, header in enumerate(headers):
        key = normalize(header)
        if key in required:
            result[idx] = required[key]

    missing = [name for name in REQUIRED_COLUMNS if name not in result.values()]
    if missing:
        raise ValueError("Faltan columnas requeridas: " + ", ".join(missing))
    return result


def validate_and_transform(rows: list[list[object]]) -> list[dict[str, object]]:
    if not rows:
        raise ValueError("El Excel maestro está vacío.")

    header_map = canonical_headers(rows[0])
    portals: list[dict[str, object]] = []
    ids: set[str] = set()

    for excel_row_number, row in enumerate(rows[1:], start=2):
        record = {
            canonical: row[idx] if idx < len(row) else ""
            for idx, canonical in header_map.items()
        }

        if not any(str(value).strip() for value in record.values()):
            continue

        portal_id = str(record["ID"]).strip()
        if not portal_id:
            raise ValueError(f"Fila {excel_row_number}: ID vacío.")
        if portal_id in ids:
            raise ValueError(f"Fila {excel_row_number}: ID duplicado '{portal_id}'.")
        ids.add(portal_id)

        for key in ["ID", "Nombre", "Descripcion", "URL", "Icono", "Categoria", "Estado", "Destacado"]:
            record[key] = str(record.get(key, "") or "").strip()

        try:
            record["Orden"] = int(float(record.get("Orden", 9999) or 9999))
        except (TypeError, ValueError):
            raise ValueError(f"Fila {excel_row_number}: Orden debe ser numérico.")

        if normalize(record["Estado"]) == "activo":
            if not record["URL"]:
                raise ValueError(f"Fila {excel_row_number}: un portal Activo necesita URL.")
            if not record["Icono"]:
                raise ValueError(f"Fila {excel_row_number}: un portal Activo necesita Icono.")
            if Path(record["Icono"]).name != record["Icono"]:
                raise ValueError(f"Fila {excel_row_number}: Icono debe ser solo un nombre de archivo.")
            icon_path = ICONS_DIR / record["Icono"]
            if not icon_path.is_file():
                raise ValueError(f"Fila {excel_row_number}: no existe assets/icons/{record['Icono']}.")

        portals.append(record)

    return portals


def main() -> int:
    if not EXCEL_PATH.is_file():
        print(f"ERROR: no existe {EXCEL_PATH}", file=sys.stderr)
        return 1

    try:
        rows = read_rows(EXCEL_PATH)
        portals = validate_and_transform(rows)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "fuente": EXCEL_PATH.name,
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "portales": portals,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(
        "// ARCHIVO GENERADO AUTOMÁTICAMENTE. NO EDITAR A MANO.\n"
        "// Fuente: datos/portal_investigacion_unphu.xlsx\n"
        f"window.PORTALES_DATA = {body};\n",
        encoding="utf-8",
    )

    active = sum(1 for portal in portals if normalize(portal.get("Estado")) == "activo")
    print(f"Generado: {OUTPUT_PATH.relative_to(ROOT)} | registros={len(portals)} | activos={active}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
