# UNX2 — YC BUILD v0.1

UNX2 est positionné comme **AI Business Operating System** : une couche opérationnelle qui identifie les tâches répétitives des PME, déploie des agents IA et mesure la valeur créée.

## Ce commit apporte

- Dashboard commercial orienté résultat
- Diagnostic IA
- Agent Registry
- Workflow Lead → Research → Qualification → Email → CRM
- Leads
- Neural Telemetry locale
- Automation Value / ROI
- YC Readiness
- Export JSON des événements
- Mode démo sans aucune clé secrète dans le navigateur

## Architecture cible

```
UNX2 UI
  ↓
API / Auth / Billing
  ↓
LÉVIATHAN CORE
  ├─ Agent Registry
  ├─ AI Router
  ├─ Policy Engine
  ├─ Memory Fabric
  ├─ Event Bus
  ├─ Knowledge Graph
  └─ Neural Telemetry
  ↓
PostgreSQL / Redis / Neo4j
```

## Sécurité

Les clés OpenAI, Anthropic, Google, Stripe, Supabase, etc. doivent rester côté serveur dans des variables d'environnement. Le prototype front-end est volontairement autonome et n'appelle aucun fournisseur IA directement.

## Prochaines intégrations

1. Supabase Auth + PostgreSQL
2. API serveur /api/diagnostic
3. AI Router avec fournisseur configurable
4. Stripe Checkout + webhook
5. CRM connectors
6. WebSocket/OpenTelemetry
7. Admin dashboard
8. E2E tests et monitoring
9. Déploiement Vercel
10. instrumentation des vrais utilisateurs et revenus

## YC KPI

À mesurer avec de vrais utilisateurs : activation, workflow exécuté, tâches réussies, rétention, clients payants, MRR, coût IA/tâche, heures économisées et Automation Value.
