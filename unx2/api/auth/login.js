import {getProfile,requireEnv} from "../_lib/supabase.js";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    await requireEnv(); const {email,password}=req.body||{};
    if(!email||!password)return res.status(400).json({error:"email and password required"});
    const base=(process.env.SUPABASE_URL||"").replace(/\/$/,"");
    const r=await fetch(base+"/auth/v1/token?grant_type=password",{method:"POST",headers:{"Content-Type":"application/json",apikey:process.env.SUPABASE_ANON_KEY},body:JSON.stringify({email,password})});
    const auth=await r.json(); if(!r.ok)return res.status(r.status).json(auth);
    const profile=auth.user?.id?await getProfile(auth.access_token,auth.user.id):null;
    return res.status(200).json({...auth,organization_id:profile?.organization_id||null,role:profile?.role||null});
  }catch(e){return res.status(500).json({error:e.message})}
}
