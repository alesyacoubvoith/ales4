import io
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent / ".." / "local_package"))

from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook
import app as local_app

client = TestClient(local_app.app)


def xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# 1) Modèle Excel téléchargeable
r = client.get("/api/assets/template")
assert r.status_code == 200, r.text
assert "spreadsheetml" in r.headers["content-type"]
wb = load_workbook(io.BytesIO(r.content))
header = [c.value for c in wb.active[1]]
assert header[:4] == ["Nom", "Type", "Marque", "Modèle"], header
assert "Statut" in header and "Date d'achat" in header, header
print("OK template:", header)

before = len(client.get("/api/assets").json())

# 2) Import d'un fichier réel (types/statuts/dates saisis librement)
data = xlsx([
    ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"],
    ["PC-COMPTA-01", "pc portable", "Dell", "Latitude 5420", "DL-5420-01", "Marie Dupont", "en service", "15/03/2024", "Service compta"],
    ["IMP-RH", "imprimante", "Brother", "MFC-L2710", "BR-2710-09", "RH", "en panne", "2023-01-05", ""],
    [None, None, None, None, None, None, None, None, None],
    ["", "Ordinateur", "HP", "ProDesk", "HP-1", "", "En stock", "", ""],
])
r = client.post("/api/assets/import", files={"file": ("parc.xlsx", data, XLSX_MIME)})
assert r.status_code == 200, r.text
res = r.json()
print("OK import:", res)
assert res["created"] == 2, res
assert res["skipped"] >= 2, res

after = client.get("/api/assets").json()
assert len(after) == before + 2, (before, len(after))
pc = next(a for a in after if a["name"] == "PC-COMPTA-01")
assert pc["type"] == "Ordinateur", pc
assert pc["status"] == "En service", pc
assert pc["purchase_date"] == "2024-03-15", pc
assert pc["brand"] == "Dell" and pc["model"] == "Latitude 5420", pc
assert pc["serial"] == "DL-5420-01" and pc["assigned_to"] == "Marie Dupont", pc
imp = next(a for a in after if a["name"] == "IMP-RH")
assert imp["type"] == "Imprimante" and imp["status"] == "En panne" and imp["purchase_date"] == "2023-01-05", imp

# 3) Ré-import : mise à jour, pas de doublon
data2 = xlsx([
    ["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"],
    ["PC-COMPTA-01", "Ordinateur", "Dell", "Latitude 5420", "DL-5420-01", "Paul Martin", "En panne", "15/03/2024", ""],
])
r = client.post("/api/assets/import", files={"file": ("parc.xlsx", data2, XLSX_MIME)})
assert r.status_code == 200, r.text
res = r.json()
print("OK re-import:", res)
assert res["updated"] == 1 and res["created"] == 0, res
again = client.get("/api/assets").json()
assert len(again) == len(after), "doublon cree"
pc2 = next(a for a in again if a["name"] == "PC-COMPTA-01")
assert pc2["assigned_to"] == "Paul Martin" and pc2["status"] == "En panne", pc2

# 4) Colonne Nom absente -> 400 explicite
bad = xlsx([["Couleur", "Marque"], ["Noir", "Dell"]])
r = client.post("/api/assets/import", files={"file": ("bad.xlsx", bad, XLSX_MIME)})
assert r.status_code == 400, r.status_code
assert "Nom" in r.json()["detail"], r.json()
print("OK colonne manquante:", r.json()["detail"])

# 4b) En-tête alternatif « Réf » accepté comme nom
ref = xlsx([["Réf", "Marque"], ["SWITCH-01", "Cisco"]])
r = client.post("/api/assets/import", files={"file": ("ref.xlsx", ref, XLSX_MIME)})
assert r.status_code == 200 and r.json()["created"] >= 1, r.text
print("OK en-tete Ref:", r.json())

# 5) Fichier non Excel -> 400 explicite
r = client.post("/api/assets/import", files={"file": ("notes.xlsx", b"pas un xlsx", XLSX_MIME)})
assert r.status_code == 400, r.status_code
assert "illisible" in r.json()["detail"]
print("OK fichier invalide:", r.json()["detail"])

# 6) Aller-retour export -> import
r = client.get("/api/assets/export")
assert r.status_code == 200
r = client.post("/api/assets/import", files={"file": ("export.xlsx", r.content, XLSX_MIME)})
assert r.status_code == 200, r.text
print("OK aller-retour export/import:", r.json())

print("TOUS LES TESTS OK")
