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
pip install -r requirements.txt
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

# Discord Bot Configuration (for order notifications)
DISCORD_BOT_TOKEN='votre_token_de_bot_discord'
DISCORD_SERVER_ID='id_de_votre_serveur_discord'
DISCORD_CHANNEL_ID='id_du_salon_discord_pour_les_notifications'
DISCORD_NOTIFICATIONS_ENABLED='False'

PUBLIC_BASE_URL='http://127.0.0.1:5000'
```
**Important:** Remplacez les valeurs d'exemple par vos configurations réelles.

### 6. Initialiser la base de données

```bash
flask shell
```

#### Puis dans le Shell Python :
```python
from app import db
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

## Déploiement avec Docker Compose

### Prérequis

- [Docker Engine](https://docs.docker.com/engine/install/) et le plugin Docker Compose.
- Un fichier `.env` prêt à l'emploi à la racine du projet (voir la section "Installer & Lancement").

### 1. Lancer l'environnement conteneurisé

Le dépôt inclut un `docker-compose.yml` qui construit l'image de l'application, expose le port 5000 et déclare deux volumes nommés pour
persister la base SQLite (`instance`) ainsi que les images téléversées (`static_img`).

```bash
docker compose up -d --build
```

Cette commande construit l'image (si nécessaire) puis démarre le service web en arrière-plan. La première exécution crée
automatiquement le dossier `instance/` et initialise la base `site.db` via le script `prestart.py`.

### 2. Suivre les logs et vérifier le démarrage

```bash
docker compose logs -f web
```

Attendez de voir Gunicorn à l'écoute sur le port `5000`. Le site est alors accessible sur <http://127.0.0.1:5000> (ou via `PUBLIC_BASE_URL`
si vous l'avez personnalisé).

### 3. Créer le compte administrateur

Une fois le conteneur lancé, générez le compte administrateur initial directement dans le conteneur :

```bash
docker compose exec web python init_admin.py
```

Le mot de passe généré est affiché dans la console (notez-le immédiatement). Les scripts utilitaires comme
`populate_slots_from_calendar.py` ou `reset_db.py` se lancent de la même façon avec `docker compose exec web python <script>.py`.

### 4. Gérer les volumes persistants

Les données sont conservées dans des volumes Docker nommés :

- `instance` pour la base SQLite et les fichiers liés à Flask.
- `static_img` pour les images uploadées et l'image par défaut (`default.png`).

Vous pouvez les sauvegarder ou les inspecter via `docker volume inspect` ou en les montant temporairement dans un conteneur utilitaire.

### 5. Arrêter ou recréer l'environnement

```bash
docker compose down
```

Relancez ensuite avec `docker compose up -d` pour appliquer des mises à jour (après un `git pull`, par exemple). Ajoutez `--build` si
le code ou les dépendances ont changé.

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

#### 2. Configuration des Notifications Discord (Optionnel) :

Si vous souhaitez activer les notifications de nouvelles commandes sur un serveur Discord :
1.  Créez un Bot Discord et obtenez son token.
2.  Invitez le bot sur votre serveur Discord.
3.  Obtenez l'ID de votre serveur Discord et l'ID du salon où les notifications doivent être envoyées.
4.  Ajoutez les variables suivantes à votre fichier `.env` :
    ```env
    DISCORD_BOT_TOKEN='VOTRE_TOKEN_DE_BOT_ICI'
    DISCORD_SERVER_ID='ID_DE_VOTRE_SERVEUR_ICI'
    DISCORD_CHANNEL_ID='ID_DE_VOTRE_SALON_ICI'
    DISCORD_NOTIFICATIONS_ENABLED='True' # Changez à 'False' pour désactiver
    ```
    Le bot doit avoir les permissions de lire les messages et d'envoyer des messages dans le salon spécifié.

#### 3. Exécution Manuelle (pour le script de calendrier):

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