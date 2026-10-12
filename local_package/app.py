"""
Alex & Co — IT Helpdesk & Stock (version locale "tout-en-un").
- Aucune base de données à installer : les données sont stockées dans data.json.
- Sert aussi l'interface web (dossier web/).
Lancement : py -m uvicorn app:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import uuid
import threading

BASE = Path(__file__).parent
DATA_FILE = BASE / "data.json"
WEB_DIR = BASE / "web"
_lock = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


PRESET_USERS = [
    {"id": "EMP-ALEX", "name": "Alex", "role": "admin", "title": "Technicien Support IT Admin"},
    {"id": "EMP-SAM", "name": "Sam", "role": "admin", "title": "Technicien Support IT Admin"},
    {"id": "EMP-001", "name": "Marie Dupont", "role": "employee", "title": "Responsable Ventes"},
    {"id": "EMP-002", "name": "Lucas Martin", "role": "employee", "title": "Opérateur Logistique"},
    {"id": "EMP-003", "name": "Sophie Bernard", "role": "employee", "title": "Chargée RH"},
]
USERS_BY_ID = {u["id"]: u for u in PRESET_USERS}

TICKET_CATEGORIES = ["Matériel / PC", "Réseau / Wifi", "Logiciel / Licence",
                     "Imprimante / Périphérique", "Accès / Identifiants", "Autre"]
TICKET_PRIORITIES = ["Basse", "Moyenne", "Haute", "Urgente"]
TICKET_STATUSES = ["Nouveau", "En cours", "En attente pièce", "Résolu", "Fermé"]
STOCK_CATEGORIES = ["Câbles & Adaptateurs", "Écrans & Moniteurs", "Claviers & Souris",
                    "PC Portable / Tour", "Composants / RAM / SSD", "Toners & Cartouches",
                    "Casques & Audio"]

DB = {"tickets": [], "inventory": [], "reminders": [], "logs": []}


def save():
    with _lock:
        DATA_FILE.write_text(json.dumps(DB, ensure_ascii=False, indent=2), encoding="utf-8")


def seed():
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
            "creator_name": USERS_BY_ID[cid]["name"], "assigned_to": assignee,
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
    save()


def load():
    global DB
    if DATA_FILE.exists():
        DB = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    else:
        seed()


load()

app = FastAPI()
api = APIRouter(prefix="/api")


class LoginInput(BaseModel):
    employee_id: str


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


@api.get("/meta")
def meta():
    return {"ticket_categories": TICKET_CATEGORIES, "ticket_priorities": TICKET_PRIORITIES,
            "ticket_statuses": TICKET_STATUSES, "stock_categories": STOCK_CATEGORIES}


@api.get("/users")
def users():
    return PRESET_USERS


@api.post("/auth/login")
def login(payload: LoginInput, request: Request):
    uid = payload.employee_id.strip().upper()
    user = USERS_BY_ID.get(uid)
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
    creator = USERS_BY_ID.get(p.creator_id)
    doc = {"id": new_id(), "title": p.title, "description": p.description, "category": p.category,
           "priority": p.priority, "status": "Nouveau", "creator_id": p.creator_id,
           "creator_name": creator["name"] if creator else p.creator_id, "assigned_to": None,
           "resolution_notes": "", "created_at": now_iso(), "updated_at": now_iso()}
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
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
