# UNX2 Business AI v0.2

Premier module commercial de neurax-ultime-core, maintenant avec Auth, RLS, dashboards, leads, paiements et télémétrie.

## Parcours
Diagnostic -> IA -> Supabase -> lead -> Stripe Checkout -> Stripe webhook -> paiement -> événement Neural Telemetry -> Make/n8n.

## Pages
- /business-ai.html — diagnostic
- /business-ai-auth.html — inscription / connexion / lien magique
- /business-dashboard.html — espace client
- /business-admin.html — espace admin/manager

## Variables Vercel
- OPENAI_API_KEY
- OPENAI_MODEL (optionnel)
- SUPABASE_URL
- SUPABASE_PUBLISHABLE_KEY (ou SUPABASE_ANON_KEY)
- SUPABASE_SERVICE_ROLE_KEY
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- BUSINESS_SUCCESS_URL (optionnel)
- BUSINESS_CANCEL_URL (optionnel)
- MAKE_WEBHOOK_URL (optionnel)

## Supabase
Exécuter supabase/business_ai.sql dans le SQL Editor. La migration crée profiles, business_diagnostics, leads, payments et business_events, avec RLS et rôles client/manager/admin.

La clé service reste uniquement côté serveur. Le navigateur utilise la clé publishable/anon avec Supabase Auth et RLS.

## Stripe
Créer un endpoint webhook vers /api/stripe-webhook et configurer STRIPE_WEBHOOK_SECRET. Les événements checkout.session.completed sont enregistrés dans payments et business_events.

## Déploiement
La branche est prête pour revue via la PR v0.2. Les fournisseurs externes ne sont jamais simulés: sans clés, les fonctions concernées signalent leur configuration manquante.
