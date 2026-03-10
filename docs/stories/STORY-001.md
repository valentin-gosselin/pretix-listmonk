# STORY-001 : Inscription automatique à la newsletter Listmonk depuis le checkout Pretix

**Epic :** Intégration Newsletter
**Priorité :** Must Have
**Story Points :** 8
**Statut :** Not Started
**Assigné à :** Non assigné
**Créé le :** 2026-03-10
**Sprint :** 1

---

## User Story

En tant qu'**organisateur d'événements**,
je veux que les acheteurs puissent s'inscrire à ma newsletter Listmonk directement lors de leur commande Pretix,
afin de **ne plus gérer manuellement les inscriptions et d'enrichir ma liste automatiquement**.

---

## Description

### Contexte et problème actuel

Actuellement, une question "Souhaitez-vous recevoir notre newsletter ?" est posée manuellement dans Pretix. Lorsqu'un acheteur répond "oui", l'organisateur doit :
1. Exporter les réponses depuis Pretix
2. Se connecter à Listmonk
3. Ajouter manuellement chaque email à la liste

Ce processus est chronophage, sujet aux oublis, et la question se **répète à chaque commande** même si l'acheteur est déjà abonné.

### Objectif

Un plugin Pretix qui :
- Injecte une case à cocher de consentement newsletter au checkout
- Abonne automatiquement l'acheteur à une liste Listmonk configurée via l'API REST
- Gère les cas limites (doublon, erreur API, déclencheur configurable)
- Se configure par événement depuis le panneau d'administration Pretix

### Périmètre

**Inclus :**
- Case à cocher opt-in dans le formulaire de contact checkout
- Appel API Listmonk asynchrone (Celery) au moment de la commande
- Gestion des doublons (email déjà dans Listmonk)
- Configuration par événement (URL, credentials, liste cible, wording)
- Choix du déclencheur : `order_placed` ou `order_paid`
- Enrichissement des attributs Listmonk (event slug, order code)
- Lien de configuration dans le menu de l'événement Pretix

**Hors périmètre (V2) :**
- Pré-cocher la case si l'email est déjà abonné
- Gestion de la désinscription via webhook
- Support multi-listes par événement
- Interface d'export / reporting dans Pretix

---

## Flux utilisateur

### Côté acheteur (checkout)
1. L'acheteur arrive sur le formulaire de contact du checkout Pretix
2. Une case à cocher apparaît : *"Je souhaite recevoir la newsletter"* (texte configurable)
3. L'acheteur coche ou non la case — elle est **décochée par défaut** (opt-in explicite)
4. L'acheteur finalise sa commande normalement
5. Si la case était cochée → le plugin déclenche l'inscription en arrière-plan

### Côté organisateur (admin)
1. L'organisateur active le plugin sur son événement
2. Il accède à **Paramètres → Listmonk Newsletter** dans le menu de l'événement
3. Il renseigne : URL Listmonk, identifiants API, ID de liste, texte de la case, déclencheur
4. Il sauvegarde → le plugin est opérationnel

### Flux technique (backend)
```
checkout → contact_form_fields injecte la case
         → order_placed / order_paid signal reçu
         → lecture order.meta_info['contact_form_data']['listmonk_newsletter_consent']
         → si True → tâche Celery lancée async
                   → POST /api/subscribers (Listmonk)
                   → si 200 : abonné créé ✓
                   → si 400/409 (email existe) : GET subscribers?query=email
                                               → PUT /api/subscribers/lists (ajout à la liste)
                   → si erreur réseau : retry automatique (3x, délai 60s)
```

---

## Critères d'acceptation

- [ ] **CA-01** : La case à cocher newsletter apparaît dans le formulaire de contact du checkout pour tout événement ayant le plugin activé
- [ ] **CA-02** : La case est décochée par défaut (opt-in explicite, conforme RGPD)
- [ ] **CA-03** : Le texte de la case est configurable par événement depuis l'admin Pretix
- [ ] **CA-04** : Si la case est cochée → l'email de l'acheteur est ajouté à la liste Listmonk configurée dans les 60 secondes
- [ ] **CA-05** : Si la case n'est pas cochée → aucun appel n'est fait à l'API Listmonk
- [ ] **CA-06** : Si l'email existe déjà dans Listmonk → l'abonné est ajouté à la liste sans créer de doublon ni générer d'erreur
- [ ] **CA-07** : L'abonnement créé dans Listmonk est en statut `confirmed` (pas de double opt-in superflu, `preconfirm_subscriptions: true`)
- [ ] **CA-08** : Les attributs Listmonk contiennent `source: pretix`, `event: <slug>`, `order_code: <code>`
- [ ] **CA-09** : L'appel API échoue → Celery réessaie automatiquement 3 fois (délai 60s entre tentatives), l'erreur est loggée
- [ ] **CA-10** : L'organisateur peut choisir entre déclencheur `order_placed` (recommandé) ou `order_paid`
- [ ] **CA-11** : La page de configuration est accessible via **Paramètres → Listmonk Newsletter** dans le menu de l'événement Pretix
- [ ] **CA-12** : Si la configuration est incomplète (URL / credentials / list_id manquants) → le plugin loggue un warning et ne lève pas d'exception

---

## Notes techniques

### Structure du plugin (scaffold existant)

```
/docker/pretix/plugins/listmonk/
├── pretix_listmonk/
│   ├── __init__.py         # expose PretixPluginMeta
│   ├── apps.py             # ListmonkPluginConfig + url_namespace + urls
│   ├── signals.py          # contact_form_fields, order_placed, order_paid, nav_event
│   ├── tasks.py            # subscribe_to_listmonk (Celery shared_task)
│   ├── forms.py            # ListmonkSettingsForm
│   ├── views.py            # ListmonkSettingsView (EventSettingsViewMixin)
│   ├── urls.py             # /control/event/<org>/<event>/settings/listmonk/
│   └── templates/
│       └── pretix_listmonk/
│           └── settings.html
├── docs/stories/STORY-001.md
├── setup.py
├── README.md
└── .gitignore
```

### Signaux Pretix utilisés

| Signal | Module | Usage |
|--------|--------|-------|
| `contact_form_fields` | `pretix.presale.signals` | Injection de la case à cocher |
| `order_placed` | `pretix.base.signals` | Déclenchement si trigger = order_placed |
| `order_paid` | `pretix.base.signals` | Déclenchement si trigger = order_paid |
| `nav_event` | `pretix.control.signals` | Lien de config dans le menu événement |

### Clés de settings événement (stockées via `event.settings`)

| Clé | Type | Obligatoire |
|-----|------|-------------|
| `listmonk_url` | URL | Oui |
| `listmonk_api_user` | str | Oui |
| `listmonk_api_password` | str | Oui |
| `listmonk_list_id` | int | Oui |
| `listmonk_checkbox_label` | str | Non (défaut fourni) |
| `listmonk_trigger` | `order_placed` \| `order_paid` | Non (défaut: `order_placed`) |

### API Listmonk

```
POST /api/subscribers
  body: { email, name, status: "enabled", lists: [list_id],
          preconfirm_subscriptions: true,
          attribs: { source, event, order_code } }
  → 200 OK : abonné créé
  → 400/409 : email existe déjà → fallback GET + PUT

GET /api/subscribers?query=subscribers.email='<email>'
  → récupère l'ID de l'abonné existant

PUT /api/subscribers/lists
  body: { ids: [subscriber_id], action: "add",
          target_list_ids: [list_id], status: "confirmed" }
```

### Stockage du consentement dans Pretix

Les champs `contact_form_fields` sont stockés dans :
```python
json.loads(order.meta_info or '{}')
    .get('contact_form_data', {})
    .get('listmonk_newsletter_consent')  # bool
```

### Points d'attention

- L'appel API **doit être async** (Celery) pour ne pas bloquer la confirmation de commande
- Le `dispatch_uid` de chaque `@receiver` doit être unique globalement
- `preconfirm_subscriptions: true` → valide RGPD si le consentement est recueilli explicitement dans Pretix (checkbox décochée par défaut + wording clair)
- Listmonk accessible depuis le container Docker via son URL publique (`https://newsletter.gosselico.fr`)
- Authentification Listmonk : HTTP Basic Auth `(api_user, api_password)`

### Installation du plugin

```bash
# Dans le container Pretix
pip install -e /pretix/plugins/listmonk

# Redémarrage nécessaire pour charger le nouveau plugin
docker restart guichet-pretix-web-1
```

---

## Dépendances

### Prérequis techniques
- Pretix ≥ 4.0.0 avec Celery configuré et opérationnel
- Instance Listmonk accessible depuis le réseau du container Pretix
- Un compte API Listmonk créé (Admin → Users → API credentials)
- Une liste Listmonk créée avec son ID numérique connu

### Dépendances de stories
- Aucune story préalable requise (plugin autonome)

### Pas de migration de base de données
- Aucun modèle Django custom — tout est stocké dans `event.settings` (clé-valeur Pretix natif)

---

## Définition de Done

- [ ] Tous les critères d'acceptation validés (CA-01 à CA-12)
- [ ] Plugin installé et chargé dans le container Pretix (`pip install -e`)
- [ ] Activé sur au moins un événement de test
- [ ] Test end-to-end réalisé : commande avec opt-in → vérification dans Listmonk
- [ ] Test doublon réalisé : commande avec email déjà dans Listmonk → pas d'erreur, ajouté à la liste
- [ ] Page de configuration accessible et fonctionnelle dans l'admin Pretix
- [ ] Logs propres (pas d'exception non gérée en production)
- [ ] Commit sur `main` avec push vers `git@github.com:valentin-gosselin/pretix-listmonk.git`

---

## Estimation

| Partie | Complexité | Points |
|--------|-----------|--------|
| Signals + case à cocher checkout | Faible (scaffold existe) | 1 |
| Tâche Celery + appel API Listmonk | Moyenne (gestion 409, retry) | 2 |
| Page settings + formulaire | Faible (scaffold existe) | 1 |
| Navigation + template HTML | Faible | 1 |
| Installation Docker + debug | Moyenne (inconnues) | 2 |
| Test end-to-end | Faible | 1 |
| **Total** | | **8** |

---

## Suivi

**Historique :**
- 2026-03-10 : Story créée (brainstorming → BMAD create-story)

**Effort réel :** À remplir lors de l'implémentation

---

*Story créée avec BMAD Method v6 — Scrum Master*
*Projet : pretix-listmonk — Sprint 1*
