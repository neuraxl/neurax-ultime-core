export default async function handler(req,res){
if(req.method!=='POST')return res.status(405).json({error:'POST requis'});
try{const event={...req.body,received_at:new Date().toISOString(),source:'UNX2 Business AI v0.1'};
if(process.env.SUPABASE_URL&&process.env.SUPABASE_SERVICE_ROLE_KEY)await fetch(process.env.SUPABASE_URL.replace(/\/$/,'')+'/rest/v1/business_events',{method:'POST',headers:{apikey:process.env.SUPABASE_SERVICE_ROLE_KEY,Authorization:'Bearer '+process.env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'},body:JSON.stringify({event:event.event||'business.event',source:event.source,received_at:event.received_at,payload:event})});
if(process.env.MAKE_WEBHOOK_URL)await fetch(process.env.MAKE_WEBHOOK_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(event)});
return res.status(202).json({accepted:true})}catch(e){return res.status(500).json({error:e.message||'Erreur événement'})}}