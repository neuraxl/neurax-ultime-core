export default async function handler(req,res){
 if(req.method!=='POST') return res.status(405).json({error:'Method not allowed'});
 const d=req.body||{};
 if(!d.company||!d.sector||!d.problem) return res.status(400).json({error:'company, sector and problem are required'});
 if(!process.env.OPENAI_API_KEY) return res.status(503).json({error:'OPENAI_API_KEY not configured'});
 const prompt=`Tu es UNX2 Business AI. Analyse ce problème d'entreprise et retourne UNIQUEMENT du JSON valide avec les clés score (0-100), identified, solution, plan (tableau de 3 chaînes), automation, tags (tableau). Entreprise: ${d.company}. Secteur: ${d.sector}. Ville: ${d.city||''}. Clients: ${d.customers||''}. Problème: ${d.problem}. Ne promets aucun résultat financier garanti.`;
 try{
  const r=await fetch('https://api.openai.com/v1/chat/completions',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+process.env.OPENAI_API_KEY},body:JSON.stringify({model:process.env.OPENAI_MODEL||'gpt-5.6',temperature:.2,response_format:{type:'json_object'},messages:[{role:'system',content:'Tu produis des diagnostics business prudents et concrets.'},{role:'user',content:prompt}]})});
  const j=await r.json(); if(!r.ok) return res.status(502).json({error:j.error?.message||'OpenAI error'});
  const out=JSON.parse(j.choices?.[0]?.message?.content||'{}'); return res.status(200).json(out);
 }catch(e){return res.status(500).json({error:e.message})}
}