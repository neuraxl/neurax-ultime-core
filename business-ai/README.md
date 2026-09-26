# UNX2 Business AI v0.1
Premier module commercial intégré à neurax-ultime-core.

Flux: Diagnostic -> IA -> Supabase -> Make/n8n -> Stripe.

Variables Vercel:
OPENAI_API_KEY
OPENAI_MODEL (optionnel)
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
STRIPE_SECRET_KEY
BUSINESS_SUCCESS_URL (optionnel)
BUSINESS_CANCEL_URL (optionnel)
MAKE_WEBHOOK_URL (optionnel)

URL: /business-ai.html

Exécuter supabase/business_ai.sql pour activer la persistance.
Les secrets restent côté serveur. Stripe n'est jamais simulé.