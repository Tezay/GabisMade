# GabisMade
Website for GabisMade

---

## Installation & Lancement

### 1. Cloner le projet

```bash
git clone https://github.com/Tezay/GabisMade.git
cd GabisMade
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Initialiser la base de données

```bash
flask shell
```

Puis dans le Sheel Python :
```python
from app import db
db.create_all()
exit()
```
##### ⚠️ Le fichier site.db sera généré dans le dossier instance/

### 5. Lancer le serveur Flask

```bash
flask run
```

## Pour réinitialiser la base de données

### Exécuter le script app/reset_db.py

```bash
python app/reset_db.py
```