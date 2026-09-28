import {requireOrgMember,supabaseFetch} from "./_lib/supabase.js";
import {aiRouter} from "./_lib/router.js";
const system="You are UNX2 Diagnostic Agent. Analyze small-business operations and return practical automation opportunities. Never invent measured savings. Clearly label estimates.";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    const {company,operations,organizationId}=req.body||{}; if(!operations)return res.status(400).json({error:"operations is required"});
    const {user,token}=await requireOrgMember(req,organizationId);
    const out=await aiRouter({system,messages:[{role:"user",content:"Company: "+(company||"Unknown")+"\\nOperations:\\n"+operations}]});
    const row=(await supabaseFetch("diagnostics",{method:"POST",body:{organization_id:organizationId,user_id:user.id,company_name:company||"Unknown",operations,result:out},token}))[0];
    await supabaseFetch("telemetry_events",{method:"POST",body:{organization_id:organizationId,event_type:"diagnostic.completed",agent_name:"Diagnostic Agent",status:"success",latency_ms:0,payload:{diagnostic_id:row.id,provider:out.provider}},token});
    return res.status(200).json({mode:out.provider==="demo"?"demo":"live",diagnostic_id:row.id,result:out});
  }catch(e){return res.status(/Unauthorized|Forbidden/.test(e.message)?401:500).json({error:e.message})}
}
