"""Backend regression tests for Support IT (helpdesk + stock + parc) new features."""
import io
import os
import pytest
import requests
from openpyxl import Workbook, load_workbook

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://helpdesk-stock.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    return s


def test_setup_needed(session):
    r = session.get(f"{API}/setup-needed", timeout=30)
    assert r.status_code == 200
    assert r.json() == {"needed": False}


def test_login_admin(session):
    r = session.post(f"{API}/auth/login", json={"employee_id": "ADMIN"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["id"] == "ADMIN"
    assert data["user"]["role"] == "admin"
    assert data["user"]["can_access_parc"] is True


def test_login_invalid(session):
    r = session.post(f"{API}/auth/login", json={"employee_id": "NOPE_ZZZ"}, timeout=30)
    assert r.status_code == 404


def test_meta(session):
    r = session.get(f"{API}/meta", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "Ordinateur" in j["asset_types"]


# --- Users create with parc flag ---
def test_create_employee_with_parc(session):
    uid = "TEST_PARC1"
    session.delete(f"{API}/users/{uid}")
    r = session.post(f"{API}/users", json={"id": uid, "name": "Test Parc", "role": "employee", "can_access_parc": True})
    assert r.status_code == 200, r.text
    assert r.json()["can_access_parc"] is True
    # verify in GET
    users = session.get(f"{API}/users").json()
    me = [u for u in users if u["id"] == uid][0]
    assert me["can_access_parc"] is True
    session.delete(f"{API}/users/{uid}")


def test_create_employee_without_parc(session):
    uid = "TEST_PARC0"
    session.delete(f"{API}/users/{uid}")
    r = session.post(f"{API}/users", json={"id": uid, "name": "Test NoParc", "role": "employee", "can_access_parc": False})
    assert r.status_code == 200
    assert r.json()["can_access_parc"] is False
    session.delete(f"{API}/users/{uid}")


# --- Upload / Download ---
def test_upload_and_download(session):
    files = {"file": ("hello.txt", b"attachment-content-xyz", "text/plain")}
    r = session.post(f"{API}/upload", files=files, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "hello.txt"
    assert data["url"].startswith("/api/files/")
    # download
    r2 = session.get(f"{BASE_URL}{data['url']}", timeout=60)
    assert r2.status_code == 200
    assert r2.content == b"attachment-content-xyz"


# --- Inventory template & import ---
def test_inventory_template(session):
    r = session.get(f"{API}/inventory/template", timeout=30)
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers.get("content-type", "")
    wb = load_workbook(io.BytesIO(r.content))
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert "Nom" in headers


def test_inventory_import(session):
    # Build an xlsx in memory
    wb = Workbook()
    ws = wb.active
    ws.append(["Nom", "Catégorie", "Quantité", "Seuil d'alerte", "Unité", "Emplacement"])
    ws.append(["TEST_IMPORT_A", "Câbles & Adaptateurs", 7, 3, "unité", "Zone-Z"])
    ws.append(["TEST_IMPORT_B", "Toners & Cartouches", 2, 5, "unité", "Zone-Z"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    r = session.post(f"{API}/inventory/import", files={"file": ("stock.xlsx", buf.getvalue(),
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}, timeout=60)
    assert r.status_code == 200, r.text
    assert r.json()["imported"] == 2
    # verify presence
    inv = session.get(f"{API}/inventory").json()
    names = [i["name"] for i in inv]
    assert "TEST_IMPORT_A" in names and "TEST_IMPORT_B" in names
    # cleanup
    for i in inv:
        if i["name"].startswith("TEST_IMPORT_"):
            session.delete(f"{API}/inventory/{i['id']}")


# --- Assets ---
def test_assets_crud_and_export(session):
    r = session.post(f"{API}/assets", json={"name": "TEST_ASSET_X", "type": "Ordinateur", "brand": "Dell"})
    assert r.status_code == 200
    aid = r.json()["id"]
    # export
    exp = session.get(f"{API}/assets/export", timeout=30)
    assert exp.status_code == 200
    assert "spreadsheetml" in exp.headers.get("content-type", "")
    # delete
    assert session.delete(f"{API}/assets/{aid}").status_code == 200


# --- Ticket with attachment ---
def test_ticket_with_attachment(session):
    files = {"file": ("note.txt", b"attached-ticket", "text/plain")}
    up = session.post(f"{API}/upload", files=files).json()
    r = session.post(f"{API}/tickets", json={
        "title": "TEST_TICKET_ATTACH", "description": "with file", "category": "Autre",
        "priority": "Basse", "creator_id": "ADMIN",
        "attachment": {"name": up["name"], "url": up["url"], "size": up["size"]}
    })
    assert r.status_code == 200
    tid = r.json()["id"]
    assert r.json()["attachment"]["url"].startswith("/api/files/")
    # retrieve
    all_t = session.get(f"{API}/tickets").json()
    me = [t for t in all_t if t["id"] == tid][0]
    assert me["attachment"] is not None
