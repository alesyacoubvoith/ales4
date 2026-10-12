from fastapi import FastAPI, APIRouter, HTTPException, Request
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
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


# ---------------- Preset accounts ----------------
SEED_ADMINS = [
    {"id": "EMP-ALEX", "name": "Alex", "role": "admin", "title": "Technicien Support IT"},
    {"id": "EMP-SAM", "name": "Sam", "role": "admin", "title": "Technicien Support IT"},
    {"id": "EMP-IT", "name": "Admin IT", "role": "admin", "title": "Service IT"},
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


# ---------------- Models ----------------
class LoginInput(BaseModel):
    employee_id: str


class UserCreate(BaseModel):
    id: str
    name: str
    role: str = "employee"
    title: str = ""


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str
    priority: str
    creator_id: str


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
    doc = {"id": uid, "name": payload.name.strip(), "role": payload.role, "title": payload.title.strip()}
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
    await seed()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
