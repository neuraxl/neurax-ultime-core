# UNX2 Business AI v0.1

Premier module commercial intégré à `neurax-ultime-core`.

## Flux
1. Prospect → formulaire de diagnostic
2. `/api/business/diagnostic` → OpenAI si configuré, sinon interface locale de secours
3. Résultat → problème / solution / plan / automatisation
4. `/api/business/checkout` → Stripe Checkout réel lorsque configuré
5. `/api/business/automation` → webhook Make/n8n optionnel

## Variables Vercel
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optionnel)
- `STRIPE_SECRET_KEY`
- `STRIPE_STARTER_PRICE_ID`
- `APP_URL`
- `AUTOMATION_WEBHOOK_URL`

Les secrets restent côté serveur. Aucun paiement n'est simulé.

## Supabase
La persistance Supabase est prévue comme prochaine couche : businesses, diagnostics, leads, customers, payments, automation_events et ai_generations. Le module actuel fonctionne sans base afin de pouvoir être testé immédiatement.

## Démarrage
Depuis le dépôt : ouvrir `/business/` sur Vercel. En local, utiliser un serveur compatible avec les fonctions `/api`.
