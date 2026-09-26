import {supabaseInsert,supabaseConfigured} from './_supabase.js';
export default async function handler(req,res){
 if(req.method!=='POST')return res.status(405).json({error:'Method not allowed'});
 const d=req.body||{};
 if(!d.company||!d.sector||!d.problem)return res.status(400).json({error:'company, sector and problem are required'});
 if(!supabaseConfigured())return res.status(202).json({saved:false,configured:false});
 try{
  const b=await supabaseInsert('businesses',{company:d.company,sector:d.sector,city:d.city||null,website:d.website||null,customers:d.customers?Number(d.customers):null});
  const l=await supabaseInsert('leads',{business_id:b.data.id,source:'unx2-business-ai',status:'new'});
  return res.status(201).json({saved:true,business_id:b.data.id,lead_id:l.data.id});
 }catch(e){return res.status(502).json({saved:false,error:e.message})}
}