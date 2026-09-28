# UNX2 v0.2 verification checklist
GET /api/health → 200
POST /api/auth/signup → Supabase Auth
POST /api/auth/login → access_token
POST /api/agent + Bearer → AI Router
POST /api/workflow + Bearer → LÉVIATHAN run + telemetry
GET /api/telemetry + Bearer → persistent events
GET/POST /api/crm/leads + Bearer → persistent CRM
POST /api/stripe/create-checkout + Bearer → subscription checkout
POST /api/stripe-webhook → signed event validation
GET /api/realtime → event stream snapshot
Security: protected routes reject missing/invalid tokens; provider secrets server-side only; tenant tables use RLS.
WebSocket note: Vercel serverless is not a durable WebSocket server. Set LEVIATHAN_WS_URL to a separately hosted WS runtime; /api/realtime is the deployment-safe SSE fallback.
