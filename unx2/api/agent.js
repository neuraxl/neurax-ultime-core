import {requireOrgMember,supabaseFetch} from "./_lib/supabase.js";
import {aiRouter} from "./_lib/router.js";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    const {organizationId,agentName,task}=req.body||{}; const {user,token}=await requireOrgMember(req,organizationId);
    if(!task)return res.status(400).json({error:"task required"});
    const started=Date.now(); const out=await aiRouter({system:"You are "+(agentName||"UNX2 Agent")+". Be concise, factual and action-oriented.",messages:[{role:"user",content:task}]});
    await supabaseFetch("telemetry_events",{method:"POST",body:{organization_id:organizationId,event_type:"agent.completed",agent_name:agentName||"UNX2 Agent",status:"success",latency_ms:Date.now()-started,payload:{provider:out.provider,user_id:user.id}},token});
    return res.status(200).json(out);
  }catch(e){return res.status(/Unauthorized|Forbidden/.test(e.message)?401:500).json({error:e.message})}
}
