"""Import Excel du parc informatique — version locale (local_package/app.py, stockage data.json)."""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "local_package"))

import app as local_app  # noqa: E402

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MODELE = ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"]


def xlsx(rows):
    wb = Workbook()
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def upload(client, data, name="parc.xlsx"):
    return client.post("/api/assets/import", files={"file": (name, data, XLSX_MIME)})


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(local_app, "DATA_FILE", tmp_path / "data.json")
    local_app.DB.update({k: [] for k in local_app.DB})
    yield TestClient(local_app.app)


def test_template_has_import_columns(client):
    r = client.get("/api/assets/template")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    header = [c.value for c in load_workbook(io.BytesIO(r.content)).active[1]]
    assert header == MODELE, header


def test_import_creates_assets(client):
    before = len(client.get("/api/assets").json())
    data = xlsx([
        MODELE,
        ["PC-COMPTA-01", "pc portable", "Dell", "Latitude 5420", "DL-5420-01", "Marie Dupont",
         "en service", "15/03/2024", "Service compta"],
        ["IMP-RH", "imprimante", "Brother", "MFC-L2710", "BR-2710-09", "RH", "en panne", "2023-01-05", ""],
        [None] * 9,
        ["", "Ordinateur", "HP", "ProDesk", "HP-1", "", "En stock", "", ""],
    ])
    r = upload(client, data)
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["created"] == 2 and res["imported"] == 2, res
    assert res["skipped"] == 2, res

    assets = client.get("/api/assets").json()
    assert len(assets) == before + 2
    pc = next(a for a in assets if a["name"] == "PC-COMPTA-01")
    assert pc["type"] == "Ordinateur", pc          # « pc portable » n'est pas une tablette
    assert pc["status"] == "En service" and pc["purchase_date"] == "2024-03-15", pc
    assert (pc["brand"], pc["model"], pc["serial"], pc["assigned_to"]) == (
        "Dell", "Latitude 5420", "DL-5420-01", "Marie Dupont"), pc
    imp = next(a for a in assets if a["name"] == "IMP-RH")
    assert (imp["type"], imp["status"], imp["purchase_date"]) == (
        "Imprimante", "En panne", "2023-01-05"), imp


def test_reimport_updates_without_duplicates(client):
    upload(client, xlsx([MODELE, ["PC-COMPTA-01", "Ordinateur", "Dell", "Latitude 5420", "DL-5420-01",
                                  "Marie Dupont", "En service", "15/03/2024", ""]]))
    total = len(client.get("/api/assets").json())
    r = upload(client, xlsx([["Nom", "Statut", "Affecté à"], ["PC-COMPTA-01", "En panne", "Paul Martin"]]))
    assert r.status_code == 200, r.text
    assert r.json()["updated"] == 1 and r.json()["created"] == 0, r.json()
    assets = client.get("/api/assets").json()
    assert len(assets) == total, "doublon créé au ré-import"
    pc = next(a for a in assets if a["name"] == "PC-COMPTA-01")
    assert pc["status"] == "En panne" and pc["assigned_to"] == "Paul Martin", pc


@pytest.mark.parametrize("rows,fragment", [
    ([["Couleur", "Marque"], ["Noir", "Dell"]], "Nom"),
    ([], "Nom"),
])
def test_missing_name_column_is_rejected(client, rows, fragment):
    r = upload(client, xlsx(rows))
    assert r.status_code == 400, r.text
    assert fragment in r.json()["detail"]


def test_unreadable_file_is_rejected(client):
    r = upload(client, b"pas un xlsx", "notes.xlsx")
    assert r.status_code == 400
    assert "illisible" in r.json()["detail"]


def test_ref_header_is_accepted_as_name(client):
    r = upload(client, xlsx([["Réf", "Marque"], ["SWITCH-01", "Cisco"]]))
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 1


def test_export_roundtrip(client):
    upload(client, xlsx([MODELE, ["PC-A", "Ordinateur", "Dell", "X", "S1", "Ann", "En service", "2024-01-02", ""]]))
    export = client.get("/api/assets/export")
    assert export.status_code == 200
    r = upload(client, export.content, "export.xlsx")
    assert r.status_code == 200, r.text
    assert r.json()["updated"] == 1 and r.json()["created"] == 0, r.json()
