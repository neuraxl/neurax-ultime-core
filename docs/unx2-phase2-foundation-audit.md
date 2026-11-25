# UNX2 / OpenJarvis — audit de fondation (phase 2)

Date: 2026-11-25
Scope: dépôt `neuraxl/neurax-ultime-core`, branche `main` et branche d'intégration OpenJarvis.

## Résumé exécutif

Le dépôt fournit une base de services locale (FastAPI, PostgreSQL 16, Redis 7 et broker MQTT). Il ne fournit pas encore les primitives nécessaires à un service multi-tenant sécurisé en production. L'intégration OpenJarvis actuelle est un adaptateur expérimental, pas un runtime de production ni un gestionnaire d'instances persistant.

## Constats

| Priorité | Constat | Conséquence | Mesure requise |
|---|---|---|---|
| Bloquant | Aucun mécanisme d'authentification/autorisation visible dans l'API examinée | L'identité du tenant ne peut pas être considérée comme fiable | Authentification, principal vérifié, RBAC |
| Bloquant | Aucun modèle/migration de tenants et d'instances visible sur `main` | Pas de registre durable ni de contraintes relationnelles | SQLAlchemy models + Alembic + contraintes |
| Bloquant | Pas de RLS PostgreSQL ni de contexte de tenant transactionnel | Isolation DB non démontrée | RLS, rôle applicatif non propriétaire, tests croisés |
| Élevé | `/api/v1/modules` est exposé sans dépendance d'authentification | Inventaire accessible publiquement | Protéger la route selon la politique API |
| Élevé | Compose contient des valeurs de développement par défaut pour PostgreSQL | Risque de déploiement avec secret faible | Refuser les secrets par défaut hors développement |
| Élevé | Le chemin de config OpenJarvis était seulement limité au dossier global | Un chemin valide d'un autre tenant pouvait être fourni | Imposer `config_root/tenant_id/instance_id/config.toml` |
| Élevé | Le runtime est créé puis fermé à chaque requête | Coût de démarrage, latence et cycle de vie non maîtrisé | Runtime manager/pool borné avec fermeture au shutdown |
| À vérifier | Signature réelle de `Jarvis(config_path=...)` et options `engine_key/model` au commit épinglé | Compatibilité SDK non encore prouvée par exécution | Smoke test contre le commit exact |
| À vérifier | Backend de mémoire, chemins de stockage et comportement concurrent OpenJarvis | Risque de partage ou de corruption mémoire | Tests d'intégration à deux tenants |

## Ce qui est effectivement présent

- API FastAPI avec endpoints liveness/readiness.
- Connexion SQLAlchemy asynchrone à PostgreSQL et client Redis.
- PostgreSQL 16 et Redis 7 dans Docker Compose.
- Contrats Python pour instance, requête et réponse d'assistant.
- Adaptateur OpenJarvis avec configuration explicite.
- Dépendance OpenJarvis épinglée à un commit upstream immuable.
- Tests unitaires de validation de chemin, de tenant et de prompt.

## Limites de preuve

Les tests ont été ajoutés, mais leur exécution dans GitHub Actions et leur succès ne sont pas confirmés par cet audit. Aucun test PostgreSQL/RLS, authentification, mémoire persistante ou appel réel à un moteur OpenJarvis n'est déclaré réussi.

## Architecture cible avant ouverture multi-tenant

1. Authentification vérifiée; le tenant provient du principal authentifié, jamais d'un champ arbitraire fourni par le client.
2. Registre SQL des tenants et instances avec contraintes uniques, états, versions de config et références de secrets.
3. Transactions tenant-scoped et RLS PostgreSQL; l'application n'utilise pas le rôle propriétaire des tables.
4. Répertoires et mémoire isolés par tenant/instance; aucun chemin de stockage fourni directement par le client.
5. Runtime manager borné (concurrence, timeouts, quotas, annulation, shutdown).
6. AI Router indépendant des moteurs; adaptateurs OpenJarvis, OpenAI, Anthropic, Gemini et futurs fournisseurs derrière un contrat stable.
7. META-ARBITER indépendant des SDK et fournisseurs; il reçoit des résultats normalisés, applique les politiques et produit une décision traçable.
8. Audit logs, télémétrie sans fuite de prompt/secrets, sauvegardes et tests de restauration.

## Critères d'acceptation de la phase suivante

- Deux tenants authentifiés ne peuvent ni lire ni modifier les instances, configs, conversations, mémoires ou événements l'un de l'autre.
- Les identifiants de tenant dans la requête ne peuvent pas remplacer l'identité issue du jeton/session.
- Les migrations s'appliquent à une base vierge et à une base existante.
- Les tests RLS utilisent un rôle applicatif non privilégié.
- Un test smoke valide le commit OpenJarvis épinglé, ses paramètres et la fermeture du runtime.
- Les tests de concurrence, timeout, quota et arrêt propre passent.
- Le META-ARBITER fonctionne avec un moteur simulé et au moins deux adaptateurs sans dépendance à OpenJarvis.

## Décision

Ne pas activer de création d'instances publique, de mémoire partagée, de CRM ou de facturation avant la validation des critères bloquants. Conserver cette intégration sur une branche/PR non fusionnée jusqu'à revue et CI verte.
