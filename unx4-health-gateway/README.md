# UNX4 Health Gateway v0.2

Premier connecteur public de santé d'UNX4.

## Architecture
- FastAPI REST + OpenAPI
- PostgreSQL/PostGIS
- Redis Event Bus
- Neural Telemetry
- Knowledge Graph relationnel initial
- WebSocket
- Dashboard cartographique Québec
- Ingestion/adaptateurs MSSS/Données Québec

## Sources officielles
- M02 installations/établissements: https://www.donneesquebec.ca/recherche/dataset/fichiers-cartographiques-m02-des-installations-et-etablissements
- Capacités/services M02: https://www.donneesquebec.ca/recherche/dataset/m02-repartition-des-capacites-et-des-services-autorises-au-permis-par-installation
- Urgences horaires: https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence

## Démarrage
```bash
docker compose up --build
```

API: http://localhost:8000/docs
Dashboard: http://localhost:8000/
Health: http://localhost:8000/api/health/status

## Synchronisation
```bash
curl -X POST http://localhost:8000/api/health/sync
```

La synchronisation découvre les ressources CSV via l'API CKAN de Données Québec, normalise les colonnes, déduplique les entités et conserve la provenance.

## Sécurité
Cette version utilise uniquement des données publiques. Aucun dossier patient, aucune donnée personnelle de santé et aucun contournement d'authentification.
