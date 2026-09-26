# UNX2 Business AI v0.1

## Flux persistant
Prospect → diagnostic → Supabase → lead → Stripe → automation.

## Tables Supabase
businesses, diagnostics, leads, customers, payments, automation_events, ai_generations.

## Configuration
Ajouter dans Vercel : OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, STRIPE_SECRET_KEY, STRIPE_STARTER_PRICE_ID, APP_URL et éventuellement AUTOMATION_WEBHOOK_URL.

Exécuter supabase/schema.sql dans Supabase SQL Editor.

Le SUPABASE_SERVICE_ROLE_KEY est strictement serveur. Ne jamais l'envoyer au navigateur.
