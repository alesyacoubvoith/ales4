from fastapi import FastAPI, APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from pydantic import BeforeValidator
import uuid
import io
import requests
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "helpdesk"
storage_key = None


def init_storage(force=False):
    global storage_key
    if storage_key and not force:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key


def put_object(path, data, content_type):
    key = init_storage()
    url = f"{STORAGE_URL}/objects/{path}"
    headers = {"X-Storage-Key": key, "Content-Type": content_type}
    resp = requests.put(url, headers=headers, data=data, timeout=120)
    if resp.status_code == 404:
        headers["X-Storage-Key"] = init_storage(force=True)
        resp = requests.put(url, headers=headers, data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()


def get_object(path):
    key = init_storage()
    url = f"{STORAGE_URL}/objects/{path}"
    resp = requests.get(url, headers={"X-Storage-Key": key}, timeout=60)
    if resp.status_code == 404:
        resp = requests.get(url, headers={"X-Storage-Key": init_storage(force=True)}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


def assets_xlsx(assets):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Parc informatique"
    ws.append(["Nom", "Type", "Marque", "Modèle", "N° série", "Affecté à", "Statut", "Date d'achat", "Notes"])
    for a in assets:
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


# ---------------- Preset accounts ----------------
SEED_ADMINS = [
    {"id": "EMP-ALEX", "name": "Alex", "role": "admin", "title": "Technicien Support IT", "can_access_parc": True},
    {"id": "EMP-SAM", "name": "Sam", "role": "admin", "title": "Technicien Support IT", "can_access_parc": True},
    {"id": "EMP-IT", "name": "Admin IT", "role": "admin", "title": "Service IT", "can_access_parc": True},
]
# Noms utilisés uniquement pour les tickets de démonstration.
SEED_NAMES = {"EMP-001": "Marie Dupont", "EMP-002": "Lucas Martin", "EMP-003": "Sophie Bernard",
              "EMP-ALEX": "Alex", "EMP-SAM": "Sam", "EMP-IT": "Admin IT"}


async def get_user(uid):
    return await db.users.find_one({"id": uid}, {"_id": 0})

TICKET_CATEGORIES = ["Matériel / PC", "Réseau / Wifi", "Logiciel / Licence",
                     "Imprimante / Périphérique", "Accès / Identifiants", "Autre"]
TICKET_PRIORITIES = ["Basse", "Moyenne", "Haute", "Urgente"]
TICKET_STATUSES = ["Nouveau", "En cours", "En attente pièce", "Résolu", "Fermé"]
STOCK_CATEGORIES = ["Câbles & Adaptateurs", "Écrans & Moniteurs", "Claviers & Souris",
                    "PC Portable / Tour", "Composants / RAM / SSD", "Toners & Cartouches",
                    "Casques & Audio"]
ASSET_TYPES = ["Ordinateur", "Imprimante", "Tablette"]
ASSET_STATUSES = ["En service", "En stock", "En panne", "Réformé"]


# ---------------- Models ----------------
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


# ---------------- Meta ----------------
@api_router.get("/")
async def root():
    return {"message": "IT Helpdesk API"}


@api_router.get("/meta")
async def meta():
    return {
        "ticket_categories": TICKET_CATEGORIES,
        "ticket_priorities": TICKET_PRIORITIES,
        "ticket_statuses": TICKET_STATUSES,
        "stock_categories": STOCK_CATEGORIES,
        "asset_types": ASSET_TYPES,
        "asset_statuses": ASSET_STATUSES,
    }


@api_router.get("/users")
async def get_users():
    return await db.users.find({}, {"_id": 0}).sort("role", 1).to_list(1000)


@api_router.post("/users")
async def create_user(payload: UserCreate):
    uid = payload.id.strip().upper()
    if not uid or not payload.name.strip():
        raise HTTPException(status_code=400, detail="ID et nom requis")
    if payload.role not in ("admin", "employee"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    if await db.users.find_one({"id": uid}):
        raise HTTPException(status_code=409, detail="Cet ID existe déjà")
    parc = True if payload.role == "admin" else bool(payload.can_access_parc)
    doc = {"id": uid, "name": payload.name.strip(), "role": payload.role,
           "title": payload.title.strip(), "can_access_parc": parc}
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    uid = user_id.strip().upper()
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    admins = await db.users.count_documents({"role": "admin"})
    if target["role"] == "admin" and admins <= 1:
        raise HTTPException(status_code=400, detail="Impossible de supprimer le dernier admin")
    await db.users.delete_one({"id": uid})
    return {"ok": True}


# ---------------- First-run setup ----------------
@api_router.get("/setup-needed")
async def setup_needed():
    return {"needed": await db.users.count_documents({}) == 0}


@api_router.post("/setup")
async def setup_admin(payload: SetupInput):
    if await db.users.count_documents({}) > 0:
        raise HTTPException(status_code=400, detail="La plateforme est déjà configurée")
    uid = payload.id.strip().upper()
    if not uid or not payload.name.strip():
        raise HTTPException(status_code=400, detail="ID et nom requis")
    doc = {"id": uid, "name": payload.name.strip(), "role": "admin",
           "title": "Administrateur", "can_access_parc": True}
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    return {"user": doc}


# ---------------- Upload (Emergent Object Storage) ----------------
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
    path = f"{APP_NAME}/uploads/{new_id()}.{ext}"
    data = await file.read()
    result = put_object(path, data, file.content_type or "application/octet-stream")
    size = result.get("size", len(data))
    await db.files.insert_one({
        "id": new_id(), "storage_path": result["path"], "original_filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size": size, "created_at": now_iso(),
    })
    return {"name": file.filename, "url": f"/api/files/{result['path']}", "size": size}


@api_router.get("/files/{path:path}")
async def download_file(path: str):
    record = await db.files.find_one({"storage_path": path}, {"_id": 0})
    data, content_type = get_object(path)
    fname = record.get("original_filename") if record else path.split("/")[-1]
    ctype = record.get("content_type", content_type) if record else content_type
    return Response(content=data, media_type=ctype,
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ---------------- Auth (ID only) ----------------
@api_router.post("/auth/login")
async def login(payload: LoginInput, request: Request):
    uid = payload.employee_id.strip().upper()
    user = await get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="ID employé introuvable")
    ua = request.headers.get("user-agent", "")
    device = "Mobile" if any(m in ua for m in ["Mobile", "Android", "iPhone"]) else "Desktop"
    ip = request.client.host if request.client else "—"
    log = {
        "id": new_id(),
        "employee_id": user["id"],
        "employee_name": user["name"],
        "role": user["role"],
        "login_time": now_iso(),
        "ip_address": ip,
        "device_type": device,
        "status": "Succès",
    }
    await db.logs.insert_one(log)
    return {"user": user}


# ---------------- Tickets ----------------
@api_router.get("/tickets")
async def list_tickets(creator_id: Optional[str] = None, status: Optional[str] = None):
    q = {}
    if creator_id:
        q["creator_id"] = creator_id
    if status:
        q["status"] = status
    tickets = await db.tickets.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return tickets


@api_router.post("/tickets")
async def create_ticket(payload: TicketCreate):
    creator = await get_user(payload.creator_id)
    doc = {
        "id": new_id(),
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "priority": payload.priority,
        "status": "Nouveau",
        "creator_id": payload.creator_id,
        "creator_name": creator["name"] if creator else payload.creator_id,
        "assigned_to": None,
        "resolution_notes": "",
        "attachment": payload.attachment,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.tickets.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, payload: TicketUpdate):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Aucune donnée")
    update["updated_at"] = now_iso()
    res = await db.tickets.update_one({"id": ticket_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    doc = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    return doc


# ---------------- Inventory ----------------
@api_router.get("/inventory")
async def list_inventory():
    items = await db.inventory.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return items


@api_router.post("/inventory")
async def create_inventory(payload: InventoryItem):
    doc = payload.model_dump()
    doc["id"] = new_id()
    doc["last_restock_date"] = now_iso()
    await db.inventory.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/inventory/{item_id}")
async def update_inventory(item_id: str, payload: InventoryUpdate):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Aucune donnée")
    if "quantity" in update:
        update["last_restock_date"] = now_iso()
    res = await db.inventory.update_one({"id": item_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article introuvable")
    doc = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    return doc


@api_router.delete("/inventory/{item_id}")
async def delete_inventory(item_id: str):
    res = await db.inventory.delete_one({"id": item_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return {"ok": True}


@api_router.get("/inventory/template")
async def inventory_template():
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


@api_router.post("/inventory/import")
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

    docs = []
    for row in rows[1:]:
        name = val(row, "name")
        if not name or not str(name).strip():
            continue
        docs.append({"id": new_id(), "name": str(name).strip(),
                     "category": str(val(row, "category", "Autre")).strip() or "Autre",
                     "quantity": to_int(val(row, "quantity", 0)),
                     "min_threshold": to_int(val(row, "threshold", 0)),
                     "unit": str(val(row, "unit", "unité")).strip() or "unité",
                     "location": str(val(row, "location", "")).strip(),
                     "maintenance_date": None, "notes": "", "last_restock_date": now_iso()})
    if docs:
        await db.inventory.insert_many(docs)
    return {"imported": len(docs)}


# ---------------- Parc informatique (assets) ----------------
@api_router.get("/assets")
async def list_assets():
    return await db.assets.find({}, {"_id": 0}).sort("name", 1).to_list(1000)


@api_router.get("/assets/export")
async def export_assets():
    assets = await db.assets.find({}, {"_id": 0}).sort("type", 1).to_list(1000)
    return assets_xlsx(assets)


@api_router.get("/assets/template")
async def assets_template():
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
    """Transforme les lignes d'un classeur Excel en documents « assets ».

    Les en-têtes sont détectés de façon souple (Nom, Type, Marque, Modèle, N° série,
    Affecté à, Statut, Date d'achat, Notes) et les lignes sans nom sont ignorées.
    """
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
        raise HTTPException(status_code=400,
                            detail="Colonne 'Nom' introuvable dans le fichier Excel")

    def val(row, key):
        idx = mapping[key]
        if idx is None or idx >= len(row) or row[idx] is None:
            return ""
        return row[idx]

    def norm_type(x):
        t = _norm(x)
        if not t:
            return ASSET_TYPES[0]
        if "imprim" in t or "print" in t:
            return "Imprimante"
        if "tabl" in t or "ipad" in t:
            return "Tablette"
        if "ordi" in t or t in ("pc", "laptop", "portable") or "pc" in t:
            return "Ordinateur"
        for at in ASSET_TYPES:
            if _norm(at) == t:
                return at
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


@api_router.post("/assets/import")
async def import_assets(file: UploadFile = File(...)):
    from openpyxl import load_workbook
    try:
        wb = load_workbook(io.BytesIO(await file.read()), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Fichier Excel illisible (.xlsx attendu)")
    raw = list(wb.active.iter_rows(values_only=True))
    docs = _parse_asset_rows(raw)

    existing = await db.assets.find({}, {"_id": 0}).to_list(5000)
    by_name = {str(a.get("name", "")).strip().lower(): a for a in existing}
    created, updated, skipped = 0, 0, 0
    for doc in docs:
        key = doc["name"].lower()
        current = by_name.get(key)
        if current:
            patch = {k: v for k, v in doc.items() if k != "notes" or v}
            await db.assets.update_one({"id": current["id"]}, {"$set": patch})
            updated += 1
        else:
            doc["id"] = new_id()
            doc["created_at"] = now_iso()
            await db.assets.insert_one(dict(doc))
            by_name[key] = doc
            created += 1
    skipped = max(0, len(raw) - 1 - len(docs))
    return {"imported": created + updated, "created": created, "updated": updated,
            "skipped": skipped, "total": len(docs)}


@api_router.post("/assets")
async def create_asset(payload: AssetCreate):
    doc = payload.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    await db.assets.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/assets/{asset_id}")
async def update_asset(asset_id: str, payload: AssetUpdate):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Aucune donnée")
    res = await db.assets.update_one({"id": asset_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Matériel introuvable")
    return await db.assets.find_one({"id": asset_id}, {"_id": 0})


@api_router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    res = await db.assets.delete_one({"id": asset_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Matériel introuvable")
    return {"ok": True}


# ---------------- Reminders ----------------
@api_router.get("/reminders")
async def list_reminders():
    items = await db.reminders.find({}, {"_id": 0}).sort("due_date", 1).to_list(1000)
    return items


@api_router.post("/reminders")
async def create_reminder(payload: ReminderCreate):
    doc = payload.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["done"] = False
    await db.reminders.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/reminders/{reminder_id}")
async def toggle_reminder(reminder_id: str):
    doc = await db.reminders.find_one({"id": reminder_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Rappel introuvable")
    await db.reminders.update_one({"id": reminder_id}, {"$set": {"done": not doc.get("done", False)}})
    doc["done"] = not doc.get("done", False)
    return doc


@api_router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    res = await db.reminders.delete_one({"id": reminder_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rappel introuvable")
    return {"ok": True}


# ---------------- Logs ----------------
@api_router.get("/logs")
async def list_logs():
    logs = await db.logs.find({}, {"_id": 0}).sort("login_time", -1).to_list(500)
    return logs


# ---------------- Stats ----------------
@api_router.get("/stats")
async def stats():
    tickets = await db.tickets.find({}, {"_id": 0}).to_list(1000)
    inventory = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    open_tickets = [t for t in tickets if t["status"] not in ("Résolu", "Fermé")]
    low_stock = [i for i in inventory if i["quantity"] <= i["min_threshold"]]
    today = datetime.now(timezone.utc).date().isoformat()
    logs_today = await db.logs.count_documents({"login_time": {"$gte": today}})
    by_status = {s: len([t for t in tickets if t["status"] == s]) for s in TICKET_STATUSES}
    by_priority = {p: len([t for t in tickets if t["priority"] == p]) for p in TICKET_PRIORITIES}
    return {
        "open_tickets": len(open_tickets),
        "total_tickets": len(tickets),
        "low_stock": len(low_stock),
        "total_items": len(inventory),
        "logs_today": logs_today,
        "resolved": len([t for t in tickets if t["status"] in ("Résolu", "Fermé")]),
        "by_status": by_status,
        "by_priority": by_priority,
    }


# ---------------- Seed ----------------
async def seed():
    if await db.users.count_documents({}) == 0:
        await db.users.insert_many([dict(a) for a in SEED_ADMINS])
    if await db.tickets.count_documents({}) == 0:
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
        docs = []
        for t in samples:
            title, desc, cat, prio, st, cid, assignee, days_ago = t
            created = base - timedelta(days=days_ago, hours=3)
            docs.append({
                "id": new_id(), "title": title, "description": desc, "category": cat,
                "priority": prio, "status": st, "creator_id": cid,
                "creator_name": SEED_NAMES.get(cid, cid), "assigned_to": assignee,
                "resolution_notes": "Résolu, matériel remplacé." if st == "Résolu" else "",
                "created_at": created.isoformat(), "updated_at": created.isoformat(),
            })
        await db.tickets.insert_many(docs)

    if await db.inventory.count_documents({}) == 0:
        base = datetime.now(timezone.utc)
        items = [
            ("Câbles HDMI 2m", "Câbles & Adaptateurs", 3, 10, "unité", "Armoire A1", None),
            ("Toners HP LaserJet", "Toners & Cartouches", 1, 4, "unité", "Stock imprimante", None),
            ("Souris Ergonomiques", "Claviers & Souris", 2, 8, "unité", "Armoire B2", None),
            ("Claviers AZERTY USB", "Claviers & Souris", 15, 5, "unité", "Armoire B2", None),
            ("Écrans 24\" Dell", "Écrans & Moniteurs", 6, 3, "unité", "Réserve", None),
            ("Adaptateurs USB-C / HDMI", "Câbles & Adaptateurs", 12, 6, "unité", "Armoire A1", None),
            ("Barrettes RAM 16Go DDR4", "Composants / RAM / SSD", 9, 4, "unité", "Coffre composants", None),
            ("SSD 500Go", "Composants / RAM / SSD", 7, 3, "unité", "Coffre composants", None),
            ("PC Portables Lenovo", "PC Portable / Tour", 4, 2, "unité", "Réserve sécurisée", None),
            ("Casques USB Jabra", "Casques & Audio", 10, 4, "unité", "Armoire B3", None),
            ("Câbles Ethernet RJ45 3m", "Câbles & Adaptateurs", 25, 10, "unité", "Armoire A1", None),
            ("Cartouches encre couleur", "Toners & Cartouches", 5, 4, "unité", "Stock imprimante", None),
        ]
        docs = []
        for name, cat, qty, thr, unit, loc, mdate in items:
            docs.append({
                "id": new_id(), "name": name, "category": cat, "quantity": qty,
                "min_threshold": thr, "unit": unit, "location": loc,
                "maintenance_date": mdate, "notes": "",
                "last_restock_date": (base - timedelta(days=20)).isoformat(),
            })
        await db.inventory.insert_many(docs)

    if await db.reminders.count_documents({}) == 0:
        base = datetime.now(timezone.utc)
        rems = [
            ("Maintenance imprimante étage 2", 3, "Maintenance"),
            ("Renouvellement licences Office", 12, "Licence"),
            ("Audit matériel trimestriel", 25, "Audit"),
            ("Fin de garantie PC portables Lenovo", 40, "Garantie"),
        ]
        docs = []
        for title, days, cat in rems:
            docs.append({
                "id": new_id(), "title": title,
                "due_date": (base + timedelta(days=days)).date().isoformat(),
                "category": cat, "notes": "", "done": False,
                "created_at": now_iso(),
            })
        await db.reminders.insert_many(docs)

    if await db.assets.count_documents({}) == 0:
        base = datetime.now(timezone.utc)
        assets = [
            ("PC-BUREAU-204", "Ordinateur", "Dell", "OptiPlex 7090", "DL7090-204", "Marie Dupont", "En service", 400),
            ("PC-PORT-ALEX", "Ordinateur", "Lenovo", "ThinkPad T14", "LN-T14-001", "Alex", "En service", 180),
            ("IMP-ETAGE2", "Imprimante", "HP", "LaserJet Pro M404", "HP-M404-02", "Service commun", "En panne", 600),
            ("TAB-LOGISTIQUE", "Tablette", "Samsung", "Galaxy Tab A8", "SM-TABA8-07", "Lucas Martin", "En service", 90),
            ("PC-ACCUEIL", "Ordinateur", "HP", "ProDesk 400", "HP-PD400-11", "Accueil", "En service", 500),
            ("IMP-DIRECTION", "Imprimante", "Brother", "MFC-L2750DW", "BR-L2750-03", "Direction", "En service", 300),
            ("TAB-DEMO", "Tablette", "Apple", "iPad 9e gen", "AP-IPAD9-02", "Stock", "En stock", 60),
        ]
        docs = [{"id": new_id(), "name": n, "type": t, "brand": b, "model": m, "serial": s,
                 "assigned_to": a, "status": st,
                 "purchase_date": (base - timedelta(days=d)).date().isoformat(),
                 "notes": "", "created_at": now_iso()} for n, t, b, m, s, a, st, d in assets]
        await db.assets.insert_many(docs)


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup():
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
