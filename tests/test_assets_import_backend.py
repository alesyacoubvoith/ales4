"""Vérifie /api/assets/import et /api/assets/template du backend Mongo (faux client Mongo en mémoire)."""
import io
import os
import sys

os.environ["MONGO_URL"] = "mongodb://fake"
os.environ["DB_NAME"] = "test"
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent / ".." / "backend"))

import motor.motor_asyncio as motor_asyncio
from openpyxl import Workbook, load_workbook


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, *a, **k):
        key = a[0] if a else None
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

                class R:
                    matched_count = 1
                return R()

        class R:
            matched_count = 0
        return R()

    async def count_documents(self, q):
        return len(self.docs)

    async def delete_one(self, q):
        class R:
            deleted_count = 0
        return R()


class FakeDB:
    def __init__(self):
        self.cols = {}

    def __getattr__(self, name):
        return self.cols.setdefault(name, FakeCollection())


fake_db = FakeDB()


class FakeClient:
    def __init__(self, *a, **k):
        pass

    def __getitem__(self, name):
        return fake_db


motor_asyncio.AsyncIOMotorClient = FakeClient

from fastapi.testclient import TestClient  # noqa: E402
import server  # noqa: E402

client = TestClient(server.app)
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def xlsx(rows):
    wb = Workbook()
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


r = client.get("/api/assets/template")
assert r.status_code == 200, r.text
header = [c.value for c in load_workbook(io.BytesIO(r.content)).active[1]]
assert header == ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"], header
print("OK template back:", header)

data = xlsx([
    ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"],
    ["PC-RH-01", "poste de travail", "Dell", "OptiPlex 3000", "DL-3000-01", "Sophie Bernard", "en service", "01/02/2025", "RH"],
    ["TAB-CHANTIER", "iPad", "Apple", "iPad 10", "AP-10-04", "Lucas", "En stock", "", ""],
])
r = client.post("/api/assets/import", files={"file": ("p.xlsx", data, XLSX_MIME)})
assert r.status_code == 200, r.text
print("OK import back:", r.json())
assert r.json()["created"] == 2

assets = client.get("/api/assets").json()
assert len(assets) == 2, assets
pc = next(a for a in assets if a["name"] == "PC-RH-01")
assert pc["type"] == "Ordinateur" and pc["purchase_date"] == "2025-02-01" and pc["status"] == "En service", pc
tab = next(a for a in assets if a["name"] == "TAB-CHANTIER")
assert tab["type"] == "Tablette" and tab["status"] == "En stock", tab

# ré-import : mise à jour
data2 = xlsx([["Nom", "Statut", "Affecté à"], ["PC-RH-01", "En panne", "Paul"]])
r = client.post("/api/assets/import", files={"file": ("p2.xlsx", data2, XLSX_MIME)})
assert r.status_code == 200 and r.json()["updated"] == 1, r.text
pc = next(a for a in client.get("/api/assets").json() if a["name"] == "PC-RH-01")
assert pc["status"] == "En panne" and pc["assigned_to"] == "Paul", pc

# fichier invalide
r = client.post("/api/assets/import", files={"file": ("x.xlsx", b"nope", XLSX_MIME)})
assert r.status_code == 400 and "illisible" in r.json()["detail"], r.text
print("TOUS LES TESTS BACKEND MONGO OK")
