"""
Alex & Co — IT Helpdesk & Stock (version locale "tout-en-un").
- Aucune base de données à installer : les données sont stockées dans data.json.
- Sert aussi l'interface web (dossier web/).
Lancement : py -m uvicorn app:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import io
import re
import uuid
import shutil
import threading

BASE = Path(__file__).parent
# En local : données à côté de l'application. En ligne : DATA_DIR peut pointer
# vers un volume persistant pour conserver les données entre deux déploiements.
DATA_DIR = Path(os.environ.get("DATA_DIR") or BASE)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "data.json"
WEB_DIR = BASE / "web"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


SEED_ADMINS = [
    {"id": "EMP-ALEX", "name": "Alex", "role": "admin", "title": "Technicien Support IT", "can_access_parc": True},
    {"id": "EMP-SAM", "name": "Sam", "role": "admin", "title": "Technicien Support IT", "can_access_parc": True},
    {"id": "EMP-IT", "name": "Admin IT", "role": "admin", "title": "Service IT", "can_access_parc": True},
]
SEED_NAMES = {"EMP-001": "Marie Dupont", "EMP-002": "Lucas Martin", "EMP-003": "Sophie Bernard",
              "EMP-ALEX": "Alex", "EMP-SAM": "Sam", "EMP-IT": "Admin IT"}


def find_user(uid):
    return next((u for u in DB["users"] if u["id"] == uid), None)

TICKET_CATEGORIES = ["Matériel / PC", "Réseau / Wifi", "Logiciel / Licence",
                     "Imprimante / Périphérique", "Accès / Identifiants", "Autre"]
TICKET_PRIORITIES = ["Basse", "Moyenne", "Haute", "Urgente"]
TICKET_STATUSES = ["Nouveau", "En cours", "En attente pièce", "Résolu", "Fermé"]
STOCK_CATEGORIES = ["Câbles & Adaptateurs", "Écrans & Moniteurs", "Claviers & Souris",
                    "PC Portable / Tour", "Composants / RAM / SSD", "Toners & Cartouches",
                    "Casques & Audio"]
ASSET_TYPES = ["Ordinateur", "Imprimante", "Tablette"]
ASSET_STATUSES = ["En service", "En stock", "En panne", "Réformé"]

DB = {"users": [], "tickets": [], "inventory": [], "reminders": [], "logs": [], "assets": []}


def save():
    with _lock:
        DATA_FILE.write_text(json.dumps(DB, ensure_ascii=False, indent=2), encoding="utf-8")


def seed():
    DB["users"] = [dict(a) for a in SEED_ADMINS]
    base = datetime.now(timezone.utc)
    samples = [
        ("PC ne démarre plus au bureau 204", "Écran noir au démarrage, voyant orange clignote.", "Matériel / PC", "Haute", "En cours", "EMP-001", "EMP-ALEX", 2),
        ("Wifi instable en salle de réunion", "La connexion coupe toutes les 10 min pendant les visios.", "Réseau / Wifi", "Moyenne", "Nouveau", "EMP-002", None, 1),
        ("Licence Office expirée", "Impossible d'ouvrir Excel, message de licence.", "Logiciel / Licence", "Haute", "En attente pièce", "EMP-003", "EMP-SAM", 3),
        ("Imprimante étage 2 bourrage papier", "Bourrage récurrent sur le bac 1.", "Imprimante / Périphérique", "Basse", "Résolu", "EMP-001", "EMP-ALEX", 5),
        ("Mot de passe oublié messagerie", "Compte verrouillé après plusieurs tentatives.", "Accès / Identifiants", "Urgente", "Nouveau", "EMP-002", None, 0),
        ("Casque micro ne fonctionne plus", "Le micro n'est plus détecté sur Teams.", "Casques & Audio", "Moyenne", "En cours", "EMP-003", "EMP-ALEX", 1),
        ("Nouvel écran à configurer", "Besoin d'un second écran pour le poste logistique.", "Matériel / PC", "Basse", "Fermé", "EMP-002", "EMP-SAM", 8),
        ("VPN ne se connecte pas", "Erreur d'authentification sur le client VPN en télétravail.", "Réseau / Wifi", "Haute", "Nouveau", "EMP-003", None, 0),
    ]
    for title, desc, cat, prio, st, cid, assignee, days_ago in samples:
        created = base - timedelta(days=days_ago, hours=3)
        DB["tickets"].append({
            "id": new_id(), "title": title, "description": desc, "category": cat,
            "priority": prio, "status": st, "creator_id": cid,
            "creator_name": SEED_NAMES.get(cid, cid), "assigned_to": assignee,
            "resolution_notes": "Résolu, matériel remplacé." if st == "Résolu" else "",
            "created_at": created.isoformat(), "updated_at": created.isoformat(),
        })
    items = [
        ("Câbles HDMI 2m", "Câbles & Adaptateurs", 3, 10, "Armoire A1"),
        ("Toners HP LaserJet", "Toners & Cartouches", 1, 4, "Stock imprimante"),
        ("Souris Ergonomiques", "Claviers & Souris", 2, 8, "Armoire B2"),
        ("Claviers AZERTY USB", "Claviers & Souris", 15, 5, "Armoire B2"),
        ("Écrans 24\" Dell", "Écrans & Moniteurs", 6, 3, "Réserve"),
        ("Adaptateurs USB-C / HDMI", "Câbles & Adaptateurs", 12, 6, "Armoire A1"),
        ("Barrettes RAM 16Go DDR4", "Composants / RAM / SSD", 9, 4, "Coffre composants"),
        ("SSD 500Go", "Composants / RAM / SSD", 7, 3, "Coffre composants"),
        ("PC Portables Lenovo", "PC Portable / Tour", 4, 2, "Réserve sécurisée"),
        ("Casques USB Jabra", "Casques & Audio", 10, 4, "Armoire B3"),
        ("Câbles Ethernet RJ45 3m", "Câbles & Adaptateurs", 25, 10, "Armoire A1"),
        ("Cartouches encre couleur", "Toners & Cartouches", 5, 4, "Stock imprimante"),
    ]
    for name, cat, qty, thr, loc in items:
        DB["inventory"].append({
            "id": new_id(), "name": name, "category": cat, "quantity": qty,
            "min_threshold": thr, "unit": "unité", "location": loc,
            "maintenance_date": None, "notes": "",
            "last_restock_date": (base - timedelta(days=20)).isoformat(),
        })
    for title, days, cat in [("Maintenance imprimante étage 2", 3, "Maintenance"),
                             ("Renouvellement licences Office", 12, "Licence"),
                             ("Audit matériel trimestriel", 25, "Audit"),
                             ("Fin de garantie PC portables Lenovo", 40, "Garantie")]:
        DB["reminders"].append({
            "id": new_id(), "title": title,
            "due_date": (base + timedelta(days=days)).date().isoformat(),
            "category": cat, "notes": "", "done": False, "created_at": now_iso(),
        })
    assets = [
        ("PC-BUREAU-204", "Ordinateur", "Dell", "OptiPlex 7090", "DL7090-204", "Marie Dupont", "En service", 400),
        ("PC-PORT-ALEX", "Ordinateur", "Lenovo", "ThinkPad T14", "LN-T14-001", "Alex", "En service", 180),
        ("IMP-ETAGE2", "Imprimante", "HP", "LaserJet Pro M404", "HP-M404-02", "Service commun", "En panne", 600),
        ("TAB-LOGISTIQUE", "Tablette", "Samsung", "Galaxy Tab A8", "SM-TABA8-07", "Lucas Martin", "En service", 90),
        ("PC-ACCUEIL", "Ordinateur", "HP", "ProDesk 400", "HP-PD400-11", "Accueil", "En service", 500),
        ("IMP-DIRECTION", "Imprimante", "Brother", "MFC-L2750DW", "BR-L2750-03", "Direction", "En service", 300),
        ("TAB-DEMO", "Tablette", "Apple", "iPad 9e gen", "AP-IPAD9-02", "Stock", "En stock", 60),
    ]
    DB["assets"] = [{"id": new_id(), "name": n, "type": t, "brand": b, "model": m, "serial": s,
                     "assigned_to": a, "status": st,
                     "purchase_date": (base - timedelta(days=d)).date().isoformat(),
                     "notes": "", "created_at": now_iso()} for n, t, b, m, s, a, st, d in assets]
    save()


def load():
    global DB
    if DATA_FILE.exists():
        DB = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        DB.setdefault("users", [])
        DB.setdefault("assets", [])
        DB.setdefault("files", [])
    else:
        save()


load()

app = FastAPI()
api = APIRouter(prefix="/api")


class LoginInput(BaseModel):
    employee_id: str


class UserCreate(BaseModel):
    id: str
    name: str
    role: str = "employee"
    title: str = ""
    can_access_parc: bool = False


class AssetCreate(BaseModel):
    name: str
    type: str
    brand: str = ""
    model: str = ""
    serial: str = ""
    assigned_to: str = ""
    status: str = "En service"
    purchase_date: Optional[str] = None
    notes: str = ""


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    purchase_date: Optional[str] = None
    notes: Optional[str] = None


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str
    priority: str
    creator_id: str
    attachment: Optional[dict] = None


class SetupInput(BaseModel):
    id: str
    name: str


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    priority: Optional[str] = None


class InventoryItem(BaseModel):
    name: str
    category: str
    quantity: int
    min_threshold: int
    unit: str = "unité"
    location: str = ""
    maintenance_date: Optional[str] = None
    notes: str = ""


class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    min_threshold: Optional[int] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    maintenance_date: Optional[str] = None
    notes: Optional[str] = None


class ReminderCreate(BaseModel):
    title: str
    due_date: str
    category: str = "Général"
    notes: str = ""


@api.get("/meta")
def meta():
    return {"ticket_categories": TICKET_CATEGORIES, "ticket_priorities": TICKET_PRIORITIES,
            "ticket_statuses": TICKET_STATUSES, "stock_categories": STOCK_CATEGORIES,
            "asset_types": ASSET_TYPES, "asset_statuses": ASSET_STATUSES}


@api.get("/users")
def users():
    return sorted(DB["users"], key=lambda u: u["role"])


@api.post("/users")
def create_user(p: UserCreate):
    uid = p.id.strip().upper()
    if not uid or not p.name.strip():
        raise HTTPException(status_code=400, detail="ID et nom requis")
    if p.role not in ("admin", "employee"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    if find_user(uid):
        raise HTTPException(status_code=409, detail="Cet ID existe déjà")
    doc = {"id": uid, "name": p.name.strip(), "role": p.role, "title": p.title.strip(),
           "can_access_parc": True if p.role == "admin" else bool(p.can_access_parc)}
    DB["users"].append(doc)
    save()
    return doc


@api.delete("/users/{user_id}")
def delete_user(user_id: str):
    uid = user_id.strip().upper()
    target = find_user(uid)
    if not target:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    admins = len([u for u in DB["users"] if u["role"] == "admin"])
    if target["role"] == "admin" and admins <= 1:
        raise HTTPException(status_code=400, detail="Impossible de supprimer le dernier admin")
    DB["users"] = [u for u in DB["users"] if u["id"] != uid]
    save()
    return {"ok": True}


@api.get("/setup-needed")
def setup_needed():
    return {"needed": len(DB["users"]) == 0}


@api.post("/setup")
def setup_admin(payload: SetupInput):
    if len(DB["users"]) > 0:
        raise HTTPException(status_code=400, detail="La plateforme est déjà configurée")
    uid = payload.id.strip().upper()
    if not uid or not payload.name.strip():
        raise HTTPException(status_code=400, detail="ID et nom requis")
    doc = {"id": uid, "name": payload.name.strip(), "role": "admin",
           "title": "Administrateur", "can_access_parc": True}
    DB["users"].append(doc)
    save()
    return {"user": doc}


@api.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix
    fname = f"{new_id()}{ext}"
    dest = UPLOAD_DIR / fname
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"name": file.filename, "url": f"/api/uploads/{fname}", "size": dest.stat().st_size}


@api.post("/auth/login")
def login(payload: LoginInput, request: Request):
    uid = payload.employee_id.strip().upper()
    user = find_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="ID employé introuvable")
    ua = request.headers.get("user-agent", "")
    device = "Mobile" if any(m in ua for m in ["Mobile", "Android", "iPhone"]) else "Desktop"
    ip = request.client.host if request.client else "—"
    DB["logs"].insert(0, {"id": new_id(), "employee_id": user["id"], "employee_name": user["name"],
                          "role": user["role"], "login_time": now_iso(), "ip_address": ip,
                          "device_type": device, "status": "Succès"})
    save()
    return {"user": user}


@api.get("/tickets")
def list_tickets(creator_id: Optional[str] = None, status: Optional[str] = None):
    res = DB["tickets"]
    if creator_id:
        res = [t for t in res if t["creator_id"] == creator_id]
    if status:
        res = [t for t in res if t["status"] == status]
    return sorted(res, key=lambda t: t["created_at"], reverse=True)


@api.post("/tickets")
def create_ticket(p: TicketCreate):
    creator = find_user(p.creator_id)
    doc = {"id": new_id(), "title": p.title, "description": p.description, "category": p.category,
           "priority": p.priority, "status": "Nouveau", "creator_id": p.creator_id,
           "creator_name": creator["name"] if creator else p.creator_id, "assigned_to": None,
           "resolution_notes": "", "attachment": p.attachment,
           "created_at": now_iso(), "updated_at": now_iso()}
    DB["tickets"].insert(0, doc)
    save()
    return doc


@api.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, p: TicketUpdate):
    for t in DB["tickets"]:
        if t["id"] == ticket_id:
            for k, v in p.model_dump().items():
                if v is not None:
                    t[k] = v
            t["updated_at"] = now_iso()
            save()
            return t
    raise HTTPException(status_code=404, detail="Ticket introuvable")


@api.get("/inventory")
def list_inventory():
    return sorted(DB["inventory"], key=lambda i: i["name"])


@api.post("/inventory")
def create_item(p: InventoryItem):
    doc = p.model_dump()
    doc["id"] = new_id()
    doc["last_restock_date"] = now_iso()
    DB["inventory"].append(doc)
    save()
    return doc


@api.patch("/inventory/{item_id}")
def update_item(item_id: str, p: InventoryUpdate):
    for it in DB["inventory"]:
        if it["id"] == item_id:
            for k, v in p.model_dump().items():
                if v is not None:
                    it[k] = v
            if p.quantity is not None:
                it["last_restock_date"] = now_iso()
            save()
            return it
    raise HTTPException(status_code=404, detail="Article introuvable")


@api.delete("/inventory/{item_id}")
def delete_item(item_id: str):
    before = len(DB["inventory"])
    DB["inventory"] = [i for i in DB["inventory"] if i["id"] != item_id]
    if len(DB["inventory"]) == before:
        raise HTTPException(status_code=404, detail="Article introuvable")
    save()
    return {"ok": True}


@api.get("/inventory/template")
def inventory_template():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock"
    ws.append(["Nom", "Catégorie", "Quantité", "Seuil d'alerte", "Unité", "Emplacement"])
    ws.append(["Câbles HDMI 2m", "Câbles & Adaptateurs", 10, 5, "unité", "Armoire A1"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modele-stock.xlsx"},
    )


@api.post("/inventory/import")
async def import_inventory(file: UploadFile = File(...)):
    from openpyxl import load_workbook
    try:
        wb = load_workbook(file.file, read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Fichier Excel illisible (.xlsx attendu)")
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"imported": 0}
    header = [str(c).strip().lower() if c is not None else "" for c in rows[0]]

    def col(*names):
        for n in names:
            for i, h in enumerate(header):
                if n in h:
                    return i
        return None

    ci = {"name": col("nom", "name"), "category": col("catég", "categ", "cat"),
          "quantity": col("quant", "qté", "qte"), "threshold": col("seuil", "alerte", "min"),
          "unit": col("unité", "unite", "unit"), "location": col("emplace", "lieu", "location")}
    if ci["name"] is None:
        raise HTTPException(status_code=400, detail="Colonne 'Nom' introuvable")

    def val(row, key, default=""):
        idx = ci[key]
        if idx is None or idx >= len(row) or row[idx] is None:
            return default
        return row[idx]

    def to_int(x):
        try:
            return int(float(x))
        except Exception:
            return 0

    count = 0
    for row in rows[1:]:
        name = val(row, "name")
        if not name or not str(name).strip():
            continue
        DB["inventory"].append({"id": new_id(), "name": str(name).strip(),
                                "category": str(val(row, "category", "Autre")).strip() or "Autre",
                                "quantity": to_int(val(row, "quantity", 0)),
                                "min_threshold": to_int(val(row, "threshold", 0)),
                                "unit": str(val(row, "unit", "unité")).strip() or "unité",
                                "location": str(val(row, "location", "")).strip(),
                                "maintenance_date": None, "notes": "", "last_restock_date": now_iso()})
        count += 1
    if count:
        save()
    return {"imported": count}


@api.get("/reminders")
def list_reminders():
    return sorted(DB["reminders"], key=lambda r: r["due_date"])


@api.post("/reminders")
def create_reminder(p: ReminderCreate):
    doc = p.model_dump()
    doc.update({"id": new_id(), "created_at": now_iso(), "done": False})
    DB["reminders"].append(doc)
    save()
    return doc


@api.patch("/reminders/{reminder_id}")
def toggle_reminder(reminder_id: str):
    for r in DB["reminders"]:
        if r["id"] == reminder_id:
            r["done"] = not r.get("done", False)
            save()
            return r
    raise HTTPException(status_code=404, detail="Rappel introuvable")


@api.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: str):
    before = len(DB["reminders"])
    DB["reminders"] = [r for r in DB["reminders"] if r["id"] != reminder_id]
    if len(DB["reminders"]) == before:
        raise HTTPException(status_code=404, detail="Rappel introuvable")
    save()
    return {"ok": True}


@api.get("/logs")
def list_logs():
    return sorted(DB["logs"], key=lambda l: l["login_time"], reverse=True)[:500]


@api.get("/assets")
def list_assets():
    return sorted(DB["assets"], key=lambda a: a["name"])


@api.get("/assets/export")
def export_assets():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Parc informatique"
    ws.append(["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"])
    for a in sorted(DB["assets"], key=lambda x: x.get("type", "")):
        ws.append([a.get("name", ""), a.get("type", ""), a.get("brand", ""), a.get("model", ""),
                   a.get("serial", ""), a.get("assigned_to", ""), a.get("status", ""),
                   a.get("purchase_date") or "", a.get("notes", "")])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=parc-informatique.xlsx"},
    )


@api.get("/assets/template")
def assets_template():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Parc informatique"
    ws.append(["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"])
    ws.append(["PC-BUREAU-204", "Ordinateur", "Dell", "OptiPlex 7090", "DL7090-204",
               "Marie Dupont", "En service", "2024-03-15", ""])
    ws.append(["IMP-ETAGE2", "Imprimante", "HP", "LaserJet Pro M404", "HP-M404-02",
               "Service commun", "En panne", "", ""])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modele-parc-informatique.xlsx"},
    )


def _norm(text):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def _parse_asset_rows(raw):
    """Transforme les lignes d'un classeur Excel en documents « assets »."""
    from datetime import date as _date, datetime as _datetime
    if not raw:
        return []
    header = [_norm(c) for c in raw[0]]

    def col(*names):
        for n in names:
            for i, h in enumerate(header):
                if h and n in h:
                    return i
        return None

    mapping = {
        "name": col("nom", "name", "materiel", "reference", "ref"),
        "type": col("type", "categorie"),
        "brand": col("marque", "brand", "fabricant", "constructeur"),
        "model": col("modele", "model"),
        "serial": col("serie", "serial", "sn", "num"),
        "assigned_to": col("affecte", "utilisateur", "assigned", "personne", "detenteur"),
        "status": col("statut", "status", "etat"),
        "purchase_date": col("achat", "date"),
        "notes": col("note", "commentaire", "remarque"),
    }
    if mapping["name"] is None:
        raise HTTPException(status_code=400, detail="Colonne 'Nom' introuvable dans le fichier Excel")

    def val(row, key):
        idx = mapping[key]
        if idx is None or idx >= len(row) or row[idx] is None:
            return ""
        return row[idx]

    def norm_type(x):
        t = _norm(x)
        if not t:
            return ASSET_TYPES[0]
        for at in ASSET_TYPES:
            if _norm(at) == t:
                return at
        if "imprim" in t or "print" in t:
            return "Imprimante"
        if "tablette" in t or "tablet" in t or "ipad" in t or "tab " in t:
            return "Tablette"
        if ("ordi" in t or "portable" in t or "laptop" in t or "desktop" in t
                or "unite centrale" in t or t == "pc" or t.startswith("pc ")
                or t.startswith("pc-") or re.search(r"\bpc\b", t)):
            return "Ordinateur"
        return ASSET_TYPES[0]

    def norm_status(x):
        s = _norm(x)
        if not s:
            return ASSET_STATUSES[0]
        for st in ASSET_STATUSES:
            if _norm(st) == s:
                return st
        if "panne" in s or "hs" in s:
            return "En panne"
        if "stock" in s:
            return "En stock"
        if "reform" in s:
            return "Réformé"
        return "En service"

    def norm_date(x):
        if x in (None, ""):
            return None
        if isinstance(x, (_datetime, _date)):
            return x.date().isoformat() if isinstance(x, _datetime) else x.isoformat()
        s = str(x).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(s.split(" ")[0], fmt).date().isoformat()
            except ValueError:
                continue
        return None

    docs = []
    for row in raw[1:]:
        name = val(row, "name")
        if name is None or not str(name).strip():
            continue
        docs.append({
            "name": str(name).strip(),
            "type": norm_type(val(row, "type")),
            "brand": str(val(row, "brand")).strip(),
            "model": str(val(row, "model")).strip(),
            "serial": str(val(row, "serial")).strip(),
            "assigned_to": str(val(row, "assigned_to")).strip(),
            "status": norm_status(val(row, "status")),
            "purchase_date": norm_date(val(row, "purchase_date")),
            "notes": str(val(row, "notes")).strip(),
        })
    return docs


@api.post("/assets/import")
async def import_assets(file: UploadFile = File(...)):
    from openpyxl import load_workbook
    try:
        wb = load_workbook(io.BytesIO(await file.read()), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Fichier Excel illisible (.xlsx attendu)")
    raw = list(wb.active.iter_rows(values_only=True))
    if not raw:
        raise HTTPException(status_code=400, detail="Fichier Excel vide : aucune ligne détectée")
    docs = _parse_asset_rows(raw)

    by_name = {str(a.get("name", "")).strip().lower(): a for a in DB["assets"]}
    created, updated = 0, 0
    for doc in docs:
        key = doc["name"].lower()
        current = by_name.get(key)
        if current:
            for k, v in doc.items():
                if k != "notes" or v:
                    current[k] = v
            updated += 1
        else:
            doc.update({"id": new_id(), "created_at": now_iso()})
            DB["assets"].append(doc)
            by_name[key] = doc
            created += 1
    if created or updated:
        save()
    skipped = max(0, len(raw) - 1 - len(docs))
    return {"imported": created + updated, "created": created, "updated": updated,
            "skipped": skipped, "total": len(docs)}


@api.post("/assets")
def create_asset(p: AssetCreate):
    doc = p.model_dump()
    doc.update({"id": new_id(), "created_at": now_iso()})
    DB["assets"].append(doc)
    save()
    return doc


@api.patch("/assets/{asset_id}")
def update_asset(asset_id: str, p: AssetUpdate):
    for a in DB["assets"]:
        if a["id"] == asset_id:
            for k, v in p.model_dump().items():
                if v is not None:
                    a[k] = v
            save()
            return a
    raise HTTPException(status_code=404, detail="Matériel introuvable")


@api.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    before = len(DB["assets"])
    DB["assets"] = [a for a in DB["assets"] if a["id"] != asset_id]
    if len(DB["assets"]) == before:
        raise HTTPException(status_code=404, detail="Matériel introuvable")
    save()
    return {"ok": True}


@api.get("/stats")
def stats():
    tickets = DB["tickets"]
    inventory = DB["inventory"]
    open_tickets = [t for t in tickets if t["status"] not in ("Résolu", "Fermé")]
    low_stock = [i for i in inventory if i["quantity"] <= i["min_threshold"]]
    today = datetime.now(timezone.utc).date().isoformat()
    logs_today = len([l for l in DB["logs"] if l["login_time"] >= today])
    return {"open_tickets": len(open_tickets), "total_tickets": len(tickets),
            "low_stock": len(low_stock), "total_items": len(inventory), "logs_today": logs_today,
            "resolved": len([t for t in tickets if t["status"] in ("Résolu", "Fermé")]),
            "by_status": {s: len([t for t in tickets if t["status"] == s]) for s in TICKET_STATUSES},
            "by_priority": {p: len([t for t in tickets if t["priority"] == p]) for p in TICKET_PRIORITIES}}


app.include_router(api)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
