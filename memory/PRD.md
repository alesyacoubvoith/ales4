# PRD — Plateforme IT Helpdesk & Stock (Alex & Co)

## Problème initial
Alex, technicien support IT en alternance, veut une plateforme web interne (FR) où chaque employé se connecte par ID (sans mot de passe) et lance un ticket de support. Lui et son collègue (admins/support) voient tous les tickets. Suivi du stock avec petite BDD, alertes stock bas, rappels par date. Logs de connexion par ID. Listes déroulantes. Lancement simple.

## Architecture
- Backend: FastAPI + MongoDB (motor). Endpoints sous /api. Seed auto au démarrage (8 tickets, 12 articles dont 3 en alerte, 4 rappels).
- Frontend: React 19 + Tailwind v4 + shadcn/ui. Thème corporate bleu clair. Auth par ID via localStorage (AuthContext).
- Login par ID uniquement (pas de mdp). Admins = EMP-ALEX, EMP-SAM. Employés = EMP-001/002/003.

## Personas
- Employé: crée et suit ses propres tickets.
- Admin/Support (Alex, Sam): dashboard, tous les tickets, gestion stock, rappels, logs.

## Core requirements (statique)
- Connexion par ID sans mot de passe + logs de connexion.
- Tickets: titre, description, catégorie (dropdown), priorité, statut; vue admin = tous, vue employé = les siens.
- Stock: nom, catégorie, quantité, seuil d'alerte, emplacement; +/- rapide, CRUD, alerte stock bas.
- Rappels/alertes par date (maintenance, licence, garantie).

## Implémenté (2026-06-12)
- Backend complet (auth/tickets/inventory/reminders/logs/stats/meta) + seed.
- Login (accès rapide + saisie manuelle, case-insensitive).
- Dashboard admin (KPIs, tickets récents, répartition statut, prochains rappels).
- Tous les tickets: recherche, filtre statut, détail, maj statut/assignation/notes.
- Mes tickets + Nouveau ticket (employé).
- Gestion du stock: CRUD, +/- quantité, toggle stock bas, bannière alerte.
- Alertes & rappels: liste triée par échéance, ajout, toggle fait, suppression.
- Logs de connexion.
- Testé end-to-end: 100% backend + frontend.

## Backlog (P1/P2)
- P1: Export CSV des logs/tickets, assignation auto, notifications email sur rappel échu.
- P2: Historique/commentaires par ticket, pièces jointes, graphiques recharts avancés, gestion des comptes employés depuis l'UI.

## Credentials
Voir /app/memory/test_credentials.md (login par ID, pas de mdp).
