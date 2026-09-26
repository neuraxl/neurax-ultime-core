import {supabaseInsert,supabaseConfigured} from './_supabase.js';
export default async function handler(req,res){
 if(req.method!=='POST')return res.status(405).json({error:'Method not allowed'});
 const payload={source:'UNX2 Business AI',event:req.body?.event||'diagnostic.created',data:req.body?.data||{},timestamp:new Date().toISOString()};
 let persisted=false;
 if(supabaseConfigured()){try{await supabaseInsert('automation_events',{business_id:req.body?.business_id||null,event:payload.event,payload});persisted=true}catch(e){return res.status(502).json({accepted:false,persisted:false,error:e.message})}}
 if(!process.env.AUTOMATION_WEBHOOK_URL)return res.status(202).json({accepted:true,configured:false,persisted,payload});
 try{const r=await fetch(process.env.AUTOMATION_WEBHOOK_URL,{method:'POST',headers:{'content-type':'application/json','x-unx2-source':'business-ai'},body:JSON.stringify(payload)});return res.status(200).json({accepted:r.ok,configured:true,persisted,status:r.status})}catch(e){return res.status(502).json({accepted:false,persisted,error:e.message})}
}