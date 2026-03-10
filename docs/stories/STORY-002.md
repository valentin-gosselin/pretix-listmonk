# STORY-002 : Internationalisation (i18n) du plugin pretix-listmonk

**Epic :** Qualité & Distribution
**Priorité :** Should Have
**Story Points :** 3
**Statut :** Not Started
**Assigné à :** Non assigné
**Créé le :** 2026-03-10
**Sprint :** 1

---

## User Story

En tant qu'**organisateur d'événements non anglophone**,
je veux que le plugin Listmonk s'affiche dans ma langue (français, allemand, néerlandais, espagnol),
afin de **comprendre les options de configuration et la case à cocher newsletter sans effort de traduction**.

---

## Description

### Contexte

Le plugin utilise déjà `gettext_lazy` (`_()`) sur toutes ses chaînes — les chaînes sont donc correctement marquées pour la traduction. Il manque uniquement les fichiers de traduction (`.po` / `.mo`) et la configuration pour que Django les charge.

### Objectif

Générer les catalogues de traduction pour les 4 langues prioritaires et les traduire, afin que le plugin soit utilisable nativement par les organisateurs francophones, germanophones, hispanophones et néerlandophones.

### Périmètre

**Inclus :**
- Structure `locale/` dans le package `pretix_listmonk/`
- Extraction des chaînes (`makemessages`) → fichiers `.po`
- Traductions pour : `fr`, `de`, `nl`, `es`
- Compilation (`compilemessages`) → fichiers `.mo`
- Mise à jour `setup.py` et `MANIFEST.in` pour inclure les fichiers locale dans la distribution

**Hors périmètre :**
- Traductions supplémentaires au-delà des 4 langues (peuvent être ajoutées par la communauté)
- Interface Weblate / plateforme de traduction collaborative
- Traduction du README

---

## Chaînes à traduire

Inventaire complet des chaînes du plugin :

**`forms.py`**
- `'Listmonk URL'`
- `'Base URL of your Listmonk instance, e.g. https://newsletter.example.com'`
- `'API username'`
- `'API password / token'`
- `'Newsletter list'`
- `'Save URL and credentials first to load available lists'`
- `'— Save URL & credentials first —'`
- `'Subscribe on'`
- `'Order placed (recommended)'`
- `'Payment confirmed'`
- `'When to send the subscription to Listmonk'`
- `'Consent checkbox label'`
- `'Leave empty to use the default text'`

**`signals.py`**
- `'I would like to subscribe to the newsletter'`
- `'Listmonk Newsletter'`

**`views.py`**
- `'Listmonk settings saved.'`
- `'Settings saved, but could not connect to Listmonk. Check your URL and credentials.'`

**`templates/pretix_listmonk/organizer_settings.html`**
- `'Listmonk Newsletter'` (titre)
- `'Configure the connection to your Listmonk instance...'`
- `'Could not connect to Listmonk with the saved credentials...'`
- `'Save your URL and credentials first...'`
- `'Listmonk connection'`
- `'Save'`

**`templates/pretix_listmonk/event_settings.html`**
- `'Listmonk Newsletter'` (titre)
- `'Optional per-event customisation...'`
- `'Save'`

---

## Critères d'acceptation

- [ ] **CA-01** : Le dossier `pretix_listmonk/locale/` existe avec les sous-dossiers `fr/LC_MESSAGES/`, `de/LC_MESSAGES/`, `nl/LC_MESSAGES/`, `es/LC_MESSAGES/`
- [ ] **CA-02** : Chaque dossier contient un fichier `django.po` avec toutes les chaînes extraites et traduites
- [ ] **CA-03** : Chaque dossier contient un fichier `django.mo` compilé (résultat de `compilemessages`)
- [ ] **CA-04** : En passant l'interface Pretix en français → les labels du formulaire organisateur et la case à cocher checkout sont en français
- [ ] **CA-05** : La chaîne par défaut de la case à cocher (`'I would like to subscribe to the newsletter'`) est traduite dans les 4 langues
- [ ] **CA-06** : Les fichiers `.po` et `.mo` sont inclus dans la distribution (`setup.py` `package_data` + `MANIFEST.in`)
- [ ] **CA-07** : Aucune régression sur le comportement fonctionnel du plugin après ajout des traductions

---

## Notes techniques

### Structure cible

```
pretix_listmonk/
└── locale/
    ├── fr/
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    ├── de/
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    ├── nl/
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    └── es/
        └── LC_MESSAGES/
            ├── django.po
            └── django.mo
```

### Commandes Django à exécuter dans le container

```bash
# 1. Extraction des chaînes (depuis le répertoire source du plugin dans le container)
docker exec pretix-dev bash -c "
  cd /pretix/src &&
  python manage.py makemessages \
    -l fr -l de -l nl -l es \
    --ignore=pretix_listmonk/locale \
    --path /pretix/src/pretix/plugins/pretix_listmonk/pretix_listmonk
"

# 2. Après traduction manuelle des .po → compiler
docker exec pretix-dev bash -c "
  cd /pretix/src &&
  python manage.py compilemessages \
    --path /pretix/src/pretix/plugins/pretix_listmonk/pretix_listmonk/locale
"
```

> **Alternative :** Créer les fichiers `.po` directement à la main (plus simple pour un petit plugin avec ~15 chaînes).

### En-tête standard d'un fichier `.po`

```po
# pretix-listmonk plugin
msgid ""
msgstr ""
"Project-Id-Version: pretix-listmonk 1.0.0\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2026-03-10 00:00+0000\n"
"PO-Revision-Date: 2026-03-10 00:00+0000\n"
"Language-Team: French\n"
"Language: fr\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=n > 1;\n"
```

### Mise à jour `setup.py`

```python
package_data={
    'pretix_listmonk': [
        'templates/pretix_listmonk/*.html',
        'locale/*/LC_MESSAGES/django.po',
        'locale/*/LC_MESSAGES/django.mo',
    ],
},
```

### Mise à jour `apps.py`

Ajouter le chemin locale à `ListmonkPluginConfig` :
```python
class ListmonkPluginConfig(PluginConfig):
    ...
    def ready(self):
        from . import signals  # noqa
        from django.utils.translation import get_language
        import os
        locale_path = os.path.join(os.path.dirname(__file__), 'locale')
        # Django trouve automatiquement les locales si le app_label est correct
        # et que les fichiers sont dans pretix_listmonk/locale/
```

En réalité, Django charge automatiquement les locales depuis `<app>/locale/` si l'app est dans `INSTALLED_APPS` — aucun code supplémentaire n'est nécessaire dans `apps.py`.

### Traductions de référence (chaîne clé)

| Chaîne EN | FR | DE | NL | ES |
|-----------|----|----|----|----|
| I would like to subscribe to the newsletter | Je souhaite m'inscrire à la newsletter | Ich möchte den Newsletter abonnieren | Ik wil me inschrijven voor de nieuwsbrief | Me gustaría suscribirme al boletín |
| Save | Enregistrer | Speichern | Opslaan | Guardar |
| Newsletter list | Liste newsletter | Newsletter-Liste | Nieuwsbrieflijst | Lista de boletín |
| Order placed (recommended) | Commande passée (recommandé) | Bestellung aufgegeben (empfohlen) | Bestelling geplaatst (aanbevolen) | Pedido realizado (recomendado) |
| Payment confirmed | Paiement confirmé | Zahlung bestätigt | Betaling bevestigd | Pago confirmado |

---

## Dépendances

**Prérequis :**
- STORY-001 complétée ✅ (le plugin fonctionnel est la base)
- Toutes les chaînes déjà marquées avec `_()` ✅

**Ne bloque aucune autre story.**

---

## Définition de Done

- [ ] Dossier `locale/` créé avec les 4 langues
- [ ] Tous les fichiers `.po` contiennent 100% des chaînes traduites (0 `msgstr ""` vide)
- [ ] Fichiers `.mo` compilés présents
- [ ] `setup.py` mis à jour pour inclure les fichiers locale
- [ ] Test manuel : interface Pretix en FR → labels en français ✅
- [ ] CA-01 à CA-07 validés
- [ ] Commit sur `main` + push GitHub

---

## Estimation

| Partie | Points |
|--------|--------|
| Création structure + fichiers `.po` (4 langues × ~15 chaînes) | 1 |
| Traductions (FR, DE, NL, ES) | 1 |
| Compilation `.mo` + setup.py + test | 1 |
| **Total** | **3** |

---

## Suivi

**Historique :**
- 2026-03-10 : Story créée

---

*Story créée avec BMAD Method v6 — Scrum Master*
*Projet : pretix-listmonk — Sprint 1*
