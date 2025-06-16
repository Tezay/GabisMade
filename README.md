# Website for GabisMade

## Installation & Lancement

### 1. Cloner le projet

```bash
git clone https://github.com/Tezay/GabisMade.git
cd GabisMade
```
### 2. Créer un environnement virtuel

```bash
python -m venv .venv
```

### 3. Activer l'environnement virtuel

#### Pour Windows
```bash
.venv\Scripts\activate
```

#### Pour Linux/MacOS
```bash
source .venv/bin/activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt python-dotenv
```

### 5. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet (`GabisMade/.env`).
Ce fichier contiendra les configurations sensibles et spécifiques à l'environnement.

Exemple de contenu pour `.env`:
```env
# Flask App Configuration
SECRET_KEY='votre_cle_secrete_ici'

# External Calendar URL
EXTERNAL_CALENDAR_URL='votre_url_icalendar_ici'

# Email configuration
CONTACT_EMAIL_RECIPIENT='contact@gabismade.fr'
```
**Important:** Remplacez les valeurs d'exemple par vos configurations réelles.

### 6. Initialiser la base de données

```bash
flask shell
```

#### Puis dans le Shell Python :
```python
from app import db, create_app
app = create_app() # Crée une instance de l'application pour le contexte
with app.app_context():
    db.create_all()
exit()
```
##### ⚠️ Le fichier de base de données (par défaut `app.db` ou `site.db` selon votre `DATABASE_URL`) sera généré dans le dossier `instance/`.

### 7. Créer un compte administrateur

Exécutez le script `init_admin.py` pour créer un compte administrateur avec un mot de passe généré aléatoirement :

```bash
python init_admin.py
```

Le mot de passe sera affiché dans la console.

### 8. Lancer le serveur Flask

```bash
flask run
```

## Gestion Automatisée des Créneaux de Retrait (via Calendrier Externe)

Le script `populate_slots_from_calendar.py` est conçu pour automatiser la création de créneaux de retrait dans la base de données de l'application. Il fonctionne en récupérant des événements (par exemple, des cours ou des disponibilités) à partir d'un flux iCalendar externe et en générant des créneaux de retrait potentiels basés sur des règles prédéfinies.

### Fonctionnalités Clés :

1.  **Période de Planification :** Le script calcule une période de planification de deux semaines complètes, commençant le lundi de la semaine suivant l'exécution (S+1) et se terminant le dimanche de la semaine d'après (S+2).
2.  **Récupération iCalendar :** Il télécharge les données d'un calendrier via une URL spécifiée dans la variable d'environnement `EXTERNAL_CALENDAR_URL` (définie dans le fichier `.env`).
3.  **Génération de Créneaux :** Pour chaque événement pertinent dans la période de planification, le script génère des créneaux de retrait selon des règles spécifiques :
    *   Au milieu d'un événement de 2 heures.
    *   5 minutes avant le début de chaque événement.
    *   Exactement à la fin de chaque événement.
4.  **Ajout à la Base de Données :** Les créneaux générés (s'ils tombent dans la période de planification) sont ajoutés à la base de données. Le script évite les doublons (même date, heure et lieu).

### Utilisation :

#### 1. Configuration de l'URL du Calendrier :

Assurez-vous que la variable `EXTERNAL_CALENDAR_URL` est correctement définie dans votre fichier `.env` à la racine du projet :

```env
EXTERNAL_CALENDAR_URL='https://votre-url-de-flux-icalendar.ics'
```

#### 2. Exécution Manuelle :

Exécutez le script depuis la racine du projet :

```bash
python populate_slots_from_calendar.py
```

## Réinitialisation de la base de données

### Exécutez le script reset_db.py

```bash
python reset_db.py
```

---

## Licence et Utilisation

Ce projet est fourni sous une licence personnalisée qui restreint son utilisation. Le code est destiné **uniquement à des fins éducatives et de démonstration**.

**Les restrictions clés incluent (mais ne sont pas limitées à) :**
-   Aucune copie ou modification du code.
-   Aucune redistribution ou sous-licence.
-   Aucune utilisation pour des projets commerciaux ou non commerciaux au-delà de la visualisation éducative personnelle.

Veuillez lire attentivement le fichier [LICENSE](LICENSE) complet avant d'interagir avec ce dépôt. Tous droits réservés par l'auteur.