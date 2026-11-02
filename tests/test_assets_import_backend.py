"""Import Excel du parc informatique — backend principal (backend/server.py + MongoDB simulé)."""
import io
import os
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

os.environ.setdefault("MONGO_URL", "mongodb://fake")
os.environ.setdefault("DB_NAME", "test")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import motor.motor_asyncio as motor_asyncio  # noqa: E402

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MODELE = ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"]


class _Result:
    def __init__(self, matched_count=0, deleted_count=0):
        self.matched_count = matched_count
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key=None, *a, **k):
        if key:
            self.docs.sort(key=lambda d: str(d.get(key, "")))
        return self

    async def to_list(self, n):
        return self.docs[:n]


class FakeCollection:
    def __init__(self):
        self.docs = []

    def find(self, q=None, proj=None):
        return FakeCursor([{k: v for k, v in d.items() if k != "_id"} for d in self.docs])

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def update_one(self, q, update):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(update["$set"])
                return _Result(matched_count=1)
        return _Result()

    async def count_documents(self, q):
        return len(self.docs)

    async def delete_one(self, q):
        return _Result()


class FakeDB:
    def __init__(self):
        self.cols = {}

    def __getattr__(self, name):
        return self.cols.setdefault(name, FakeCollection())

    def __getitem__(self, name):
        return self


@pytest.fixture(scope="module")
def client():
    db = FakeDB()
    motor_asyncio.AsyncIOMotorClient = lambda *a, **k: db
    from fastapi.testclient import TestClient
    import server
    return TestClient(server.app)


def xlsx(rows):
    wb = Workbook()
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def upload(client, data, name="parc.xlsx"):
    return client.post("/api/assets/import", files={"file": (name, data, XLSX_MIME)})


def test_template_has_import_columns(client):
    r = client.get("/api/assets/template")
    assert r.status_code == 200, r.text
    header = [c.value for c in load_workbook(io.BytesIO(r.content)).active[1]]
    assert header == MODELE, header


def test_import_then_update(client):
    data = xlsx([
        MODELE,
        ["PC-RH-01", "poste de travail", "Dell", "OptiPlex 3000", "DL-3000-01", "Sophie Bernard",
         "en service", "01/02/2025", "RH"],
        ["TAB-CHANTIER", "iPad", "Apple", "iPad 10", "AP-10-04", "Lucas", "En stock", "", ""],
    ])
    r = upload(client, data)
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 2, r.json()

    assets = client.get("/api/assets").json()
    pc = next(a for a in assets if a["name"] == "PC-RH-01")
    assert (pc["type"], pc["status"], pc["purchase_date"]) == ("Ordinateur", "En service", "2025-02-01"), pc
    tab = next(a for a in assets if a["name"] == "TAB-CHANTIER")
    assert (tab["type"], tab["status"]) == ("Tablette", "En stock"), tab

    r = upload(client, xlsx([["Nom", "Statut", "Affecté à"], ["PC-RH-01", "En panne", "Paul"]]))
    assert r.status_code == 200 and r.json()["updated"] == 1, r.text
    pc = next(a for a in client.get("/api/assets").json() if a["name"] == "PC-RH-01")
    assert (pc["status"], pc["assigned_to"]) == ("En panne", "Paul"), pc


def test_unreadable_file_is_rejected(client):
    r = upload(client, b"nope", "x.xlsx")
    assert r.status_code == 400
    assert "illisible" in r.json()["detail"]
