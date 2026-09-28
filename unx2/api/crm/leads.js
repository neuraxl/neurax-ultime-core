import{requireOrgMember,supabaseFetch}from"../_lib/supabase.js";
export default async function handler(req,res){
  try{
    const o=req.query.organization_id; const {user,token}=await requireOrgMember(req,o);
    if(req.method==="GET")return res.status(200).json({user_id:user.id,organization_id:o,leads:await supabaseFetch("leads?organization_id=eq."+encodeURIComponent(o)+"&order=created_at.desc",{token})});
    if(req.method==="POST"){
      const{company_name,score,status,metadata}=req.body||{}; if(!company_name)return res.status(400).json({error:"company_name required"});
      const row=(await supabaseFetch("leads",{method:"POST",body:{organization_id:o,company_name,score:score??null,status:status||"new",metadata:metadata||{}},token}))[0];
      await supabaseFetch("telemetry_events",{method:"POST",body:{organization_id:o,event_type:"crm.lead.created",agent_name:"Lead Agent",status:"success",payload:{lead_id:row.id}},token});
      return res.status(201).json(row);
    }
    return res.status(405).end();
  }catch(e){res.status(/Unauthorized|Forbidden/.test(e.message)?401:500).json({error:e.message})}
}
