import {supabaseFetch} from "./supabase.js";
async function publishRuntime(event){
  const url=process.env.LEVIATHAN_RUNTIME_URL, secret=process.env.LEVIATHAN_RUNTIME_SECRET;
  if(!url||!secret)return false;
  try{
    const r=await fetch(url.replace(/\/$/,"")+"/publish",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+secret},body:JSON.stringify(event)});
    return r.ok;
  }catch{return false}
}
export async function runLeviathan({organizationId,workflowId,steps,token}){
  const started=Date.now();
  const run=(await supabaseFetch("workflow_runs",{method:"POST",body:{organization_id:organizationId,workflow_id:workflowId||null,status:"running"},token}))[0];
  const events=[];
  for(const s of steps){
    const t=Date.now(); const event={organization_id:organizationId,run_id:run.id,event_type:s.event,agent_name:s.agent,status:"success",latency_ms:Date.now()-t,payload:{layer:"LEVIATHAN",workflow_id:workflowId}};
    events.push(event); await publishRuntime(event);
  }
  if(events.length)await supabaseFetch("telemetry_events",{method:"POST",body:events,token});
  const duration=Date.now()-started;
  await supabaseFetch("workflow_runs?id=eq."+encodeURIComponent(run.id),{method:"PATCH",body:{status:"completed",finished_at:new Date().toISOString(),duration_ms:duration,result:{events}},token});
  await publishRuntime({organization_id:organizationId,run_id:run.id,event_type:"workflow.completed",agent_name:"LÉVIATHAN",status:"success",latency_ms:duration,payload:{layer:"LEVIATHAN"}});
  return {run_id:run.id,status:"completed",events,duration_ms:duration};
}
