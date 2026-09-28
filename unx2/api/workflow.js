import {requireOrgMember,supabaseFetch} from "./_lib/supabase.js";
import {runLeviathan} from "./_lib/leviathan.js";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    const {organizationId,name="Lead qualification",steps}=req.body||{}; const {token}=await requireOrgMember(req,organizationId);
    const definition={steps:steps||[
      {event:"lead.received",agent:"Lead Agent"},
      {event:"research.completed",agent:"Research Agent"},
      {event:"lead.qualified",agent:"Lead Agent"},
      {event:"response.drafted",agent:"Email Agent"},
      {event:"crm.updated",agent:"Lead Agent"}
    ]};
    const workflow=(await supabaseFetch("workflows",{method:"POST",body:{organization_id:organizationId,name,definition,status:"active"},token}))[0];
    const result=await runLeviathan({organizationId,workflowId:workflow.id,steps:definition.steps,token});
    return res.status(200).json({workflow_id:workflow.id,...result});
  }catch(e){return res.status(/Unauthorized|Forbidden/.test(e.message)?401:500).json({error:e.message})}
}
