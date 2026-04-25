# **MLOps — Socratic : The Ethical Reasoning Game**

## 1. Présentation du projet

**Socratic** est une application web interactive basée sur l'intelligence artificielle qui analyse le raisonnement humain à travers un jeu philosophique.

L'utilisateur est confronté à **5 scénarios éthiques**, dans lesquels il doit :

* Prendre une décision
* Justifier son raisonnement

Ces réponses sont ensuite analysées par deux modèles de Machine Learning afin de :

*  Déterminer son **profil éthique dominant**
*  Détecter ses **schémas de biais logiques** (fallacies)
*  Générer une **explication personnalisée** grâce à une IA (Groq)
*  Recommander un **livre adapté** à son profil

Ce projet combine **NLP (Natural Language Processing)**, **classification supervisée** et un pipeline **MLOps complet** (DVC + MLflow + CI/CD + Docker + AWS).



## 2. Architecture technique globale

L'architecture repose sur une infrastructure **cloud-native et modulaire**.



```
                        ┌─────────────────────────────────┐
                        │           AWS Cloud             │
                        │                                 │
  User ──── Browser ───►│  EC2 (t3.medium, Ubuntu 22.04)  │
                        │  ├── Docker: FastAPI :8000      │
                        │  └── MLflow Server :5000        │
                        │                                 │
                        │  S3: group4-soc-bucket          │
                        │  ├── data/raw/                  │
                        │  ├── data/processed/            │
                        │  ├── mlflow/  (artifacts)       │
                        │  └── dvc-store/  (DVC cache)    │
                        └─────────────────────────────────┘
```


### Composants principaux

| Composant | Rôle |
|---|---|
| **AWS EC2** | Hébergement du serveur MLflow + déploiement de l'API (Docker) |
| **AWS S3** | Stockage des datasets (raw + processed) + artefacts MLflow (remote DVC) |
| **MLflow** | Tracking des expériences + Registry des modèles (Staging / Production) |
| **DVC** | Versionnage des données + pipeline reproductible |
| **FastAPI** | API backend pour prédiction et interaction |
| **Frontend (Jinja2 + JS)** | Interface du jeu + page de résultats |
| **Groq API** | Génération d'explications intelligentes multilingues |
| **Docker** | Conteneurisation de l'API |
| **GitHub Actions** | CI/CD (déploiement + réentraînement) |

### Pipeline MLOps (DVC)

```
preprocess → train → evaluate → register
```

Chaque étape est **versionnée**, **reproductible** et **automatisée**.



## 3. Modèles de Machine Learning

### Modèle 1 — Ethics Classifier

* **Objectif** : Classifier le raisonnement en 5 théories éthiques
* **Classes** : `utilitarianism`, `deontology`, `virtue ethics`, `care ethics`, `egoism`
* **Algorithme** : Logistic Regression (multinomial, solver=saga)
* **Features** : TF-IDF (word n-grams + char n-grams)
* **Performance** : F1-score ≈ **0.84**

### Modèle 2 — Fallacy Detector

* **Objectif** : Détecter les erreurs de raisonnement
* **Classes** : 13 types de biais logiques
* **Algorithme** : LinearSVC ou Logistic Regression (via validation croisée)
* **Particularité** : Dataset déséquilibré → utilisation de `class_weight=balanced`
* **Performance** : F1-score ≈ **0.60**



## 4. Données utilisées

### Datasets

| Fichier | Exemples | Description |
|---|---|---|
| `ethics_dataset.csv` | 305 (équilibré) | colonnes : `scenario`, `decision`, `reason`, `label` |
| `fallacy_dataset.csv` | 2452 (déséquilibré) | classification multi-classes |

### Prétraitement

* Nettoyage texte (`clean_text`)
* Fusion des champs (`scenario + decision + reason`)
* Vectorisation TF-IDF
* Encodage des labels
* Split train/test (stratifié)



## 5. Arborescence du projet

```plaintext
project-root/
│
├── src/                    # Pipeline ML
│   ├── preprocess.py
│   ├── train.py
│   ├── evaluate.py
│   ├── register.py
│   └── utils.py
│
├── api/                    # Backend FastAPI
│   └── main.py
│
├── templates/              # Frontend (HTML)
│   ├── index.html
│   ├── language.html
│   ├── game.html
│   └── result.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
├── .github/workflows/      # CI/CD
│   ├── deploy.yml
│   └── retrain.yml
│
├── dvc.yaml                # Pipeline DVC
├── Dockerfile
├── requirements.txt
└── README.md
```



## 6. Instructions pour reproduire l'environnement et relancer le projet

### Prérequis

* Python 3.9+
* Git
* DVC
* Docker (optionnel)



### 6.1. Cloner le projet et installer les dépendances

```bash
git clone <repo_url>
cd project-root
pip install -r requirements.txt
```



### 6.2. Lancer le pipeline ML

```bash
dvc pull
dvc repro
```



### 6.3. Lancer l'API localement

```bash
uvicorn api.main:app --reload --port 8000
```

 Accès : `http://localhost:8000`



## 7. Déploiement sur AWS EC2 :

### 7.1. Lancer le serveur MLflow

```bash
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://<bucket>/mlflow
```

### 7.2. Lancer l'API avec Docker

```bash
docker build -t socratic-api .
docker run -d -p 8000:8000 socratic-api
```



## 8. CI/CD (GitHub Actions)

### `deploy.yml`

Déploiement automatique sur EC2 à chaque push sur `main`.

### `retrain.yml`

Réentraînement automatique :
* Déclenchement manuel ou planifié (cron)
* Exécute `dvc repro`



## 9. Fonctionnement du jeu

1. **Page d'accueil** → Démarrer
2. **Choix de langue**
3. **5 scénarios** : choix d'une décision + choix d'un raisonnement
4. **Analyse via API**
5. **Résultat final** :
   *  Profil éthique dominant
   *  Biais logique détecté
   *  Explication IA personnalisée
   *  Insight personnel
   *  Recommandation de livre



## 10. Bonnes pratiques MLOps appliquées

*  Versionnage des données (DVC)
*  Suivi des expériences (MLflow)
*  Séparation des environnements
*  Déploiement conteneurisé (Docker)
*  Automatisation (CI/CD)
*  Gestion des secrets (`.env`)



## 11. Limitations actuelles

* Performance du modèle de fallacy encore faible (~0.60)
* Dépendance à l'API Groq
* Dataset limité pour certains biais rares



## 12. Améliorations futures

*  Amélioration des performances modèles
*  Ajout de modèles deep learning (Transformers)
*  Support multilingue natif (sans traduction)
*  Dashboard d'analyse utilisateur
*  Pipeline CI/CD complet avec tests automatiques



## 13. Conclusion

**Socratic** illustre une implémentation complète d'un système MLOps moderne, combinant :

* Intelligence artificielle
* Infrastructure cloud
* Automatisation
* Expérience utilisateur interactive

