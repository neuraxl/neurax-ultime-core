const prompts={
  system:"You are UNX2 Diagnostic Agent. Analyze small-business operations and return practical automation opportunities. Never invent measured savings. Clearly label estimates.",
};
export default async function handler(req,res){
  if(req.method!=="POST") return res.status(405).json({error:"Method not allowed"});
  const {company,operations}=req.body||{};
  if(!operations) return res.status(400).json({error:"operations is required"});
  const key=process.env.OPENAI_API_KEY;
  if(!key){
    return res.status(200).json({
      mode:"demo",
      company:company||"Unknown",
      opportunities:[
        "Qualification et enrichissement des prospects",
        "Triage et préparation des courriels",
        "Mise à jour CRM",
        "Rapport hebdomadaire automatisé"
      ],
      estimate:"8–20 h/semaine potentiellement automatisables — estimation à valider avec le client."
    });
  }
  const r=await fetch("https://api.openai.com/v1/responses",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization:"Bearer "+key},
    body:JSON.stringify({model:process.env.OPENAI_MODEL||"gpt-5.6-mini",input:[
      {role:"system",content:prompts.system},
      {role:"user",content:"Company: "+(company||"Unknown")+"\nOperations:\n"+operations}
    ]})
  });
  if(!r.ok) return res.status(502).json({error:"AI provider error"});
  const data=await r.json();
  return res.status(200).json({mode:"live",result:data.output_text||""});
}