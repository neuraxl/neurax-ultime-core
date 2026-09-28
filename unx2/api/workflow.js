const sleep=ms=>new Promise(r=>setTimeout(r,ms));
export default async function handler(req,res){
  if(req.method!=="POST") return res.status(405).json({error:"Method not allowed"});
  const started=Date.now();
  const steps=[
    ["lead.received","Lead Agent"],
    ["research.completed","Research Agent"],
    ["lead.qualified","Lead Agent"],
    ["response.drafted","Email Agent"],
    ["crm.updated","Lead Agent"]
  ];
  const events=steps.map(([event,agent],i)=>({event,agent,status:"success",latency_ms:180+i*70}));
  await sleep(40);
  res.status(200).json({
    run_id:crypto.randomUUID(),
    status:"completed",
    duration_ms:Date.now()-started,
    events
  });
}