# 🪟 Installer la plateforme sur Windows — Guide super simple

> Objectif : faire tourner l'appli sur ton PC et la partager à tes collègues via ton IP.
> Prends ton temps, fais les étapes DANS L'ORDRE. ✅

---

## ÉTAPE 0 — Installer 3 logiciels (une seule fois)

Télécharge et installe ces 3 programmes (clique "Suivant / Next" partout) :

1. **Python** → https://www.python.org/downloads/
   - ⚠️ TRÈS IMPORTANT : sur le 1er écran, coche la case **"Add Python to PATH"** avant de cliquer Install.
2. **Node.js** (version LTS) → https://nodejs.org/
3. **MongoDB Community Server** → https://www.mongodb.com/try/download/community
   - Laisse l'option "Install as a Service" cochée (la base démarre toute seule avec Windows).

Puis installe **Yarn** : ouvre le menu Démarrer, tape `cmd`, ouvre "Invite de commandes", colle ceci et appuie sur Entrée :
```
npm install -g yarn
```

---

## ÉTAPE 1 — Récupérer le code

- Télécharge le code depuis Emergent (bouton **Save → Save to GitHub**, ou bouton **Code**).
- Mets le dossier sur ton Bureau. Exemple : `C:\Users\Alex\Desktop\helpdesk`

---

## ÉTAPE 2 — Vérifier les fichiers .env

1. Dans le dossier `backend`, il doit y avoir un fichier **.env** contenant :
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="helpdesk"
CORS_ORIGINS="*"
```

2. Trouve ton adresse IP : ouvre `cmd`, tape `ipconfig`, appuie Entrée.
   Note la ligne **"Adresse IPv4"** (ex: `192.168.1.42`).

3. Dans le dossier `frontend`, ouvre le fichier **.env** et mets TON IP :
```
REACT_APP_BACKEND_URL=http://192.168.1.42:8001
```
(remplace 192.168.1.42 par la tienne)

---

## ÉTAPE 3 — Lancer l'appli

Le plus simple : **double-clique sur le fichier `start-windows.bat`** (à la racine du dossier).
Deux fenêtres noires vont s'ouvrir (backend + frontend) → c'est NORMAL, ne les ferme pas.

Attends ~1 minute, puis ouvre ton navigateur sur :
```
http://localhost:3000
```

---

## ÉTAPE 4 — Partager à tes collègues

Tes collègues (sur le même Wi-Fi/réseau que toi) ouvrent dans leur navigateur :
```
http://192.168.1.42:3000
```
(ton IP, port 3000)

Si ça ne s'ouvre pas chez eux : autorise les ports dans le pare-feu Windows
(Windows va souvent te demander "Autoriser l'accès ?" au 1er lancement → clique **Autoriser**).

---

## 🔑 Connexion
Pas de mot de passe. On se connecte avec un ID employé :
- **EMP-ALEX** / **EMP-SAM** → toi et ton collègue (admin, voient tout)
- **EMP-001 / EMP-002 / EMP-003** → employés

---

## ❓ Ça marche pas ?
- "python n'est pas reconnu" → tu as oublié de cocher "Add Python to PATH". Réinstalle Python en cochant la case.
- Page blanche → attends 1 min de plus, puis rafraîchis (F5).
- Les collègues n'y arrivent pas → ils doivent être sur le MÊME réseau, et le pare-feu doit être autorisé.
- Toujours bloqué ? Envoie-moi une photo de la fenêtre noire avec l'erreur. 📸
