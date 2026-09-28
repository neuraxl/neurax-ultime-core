import {adminAuth,adminRest,requireEnv} from "../_lib/supabase.js";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    await requireEnv();
    const {email,password,organizationName}=req.body||{};
    if(!email||!password)return res.status(400).json({error:"email and password required"});
    if(password.length<8)return res.status(400).json({error:"password must be at least 8 characters"});
    const base=(process.env.SUPABASE_URL||"").replace(/\/$/,"");
    const r=await fetch(base+"/auth/v1/signup",{method:"POST",headers:{"Content-Type":"application/json",apikey:process.env.SUPABASE_ANON_KEY},body:JSON.stringify({email,password})});
    const auth=await r.json(); if(!r.ok)return res.status(r.status).json(auth);
    const user=auth.user||auth; if(!user?.id)return res.status(502).json({error:"Supabase did not return a user id"});
    const name=(organizationName||((email.split("@")[0]||"UNX2")+" Workspace")).trim().slice(0,120);
    const org=(await adminRest("organizations",{method:"POST",body:{name}}))[0];
    try{
      await adminRest("profiles",{method:"POST",body:{id:user.id,organization_id:org.id,role:"owner"}});
    }catch(e){
      await adminAuth("users/"+encodeURIComponent(user.id),{method:"DELETE"}).catch(()=>{});
      await adminRest("organizations?id=eq."+encodeURIComponent(org.id),{method:"DELETE",prefer:"return=minimal"}).catch(()=>{});
      throw e;
    }
    return res.status(r.status||201).json({...auth,organization:{id:org.id,name:org.name},profile:{id:user.id,organization_id:org.id,role:"owner"}});
  }catch(e){return res.status(500).json({error:e.message})}
}
