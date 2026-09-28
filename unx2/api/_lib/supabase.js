export async function supabaseFetch(path,{method="GET",body,token,prefer="return=representation"}={}) {
  const url=(process.env.SUPABASE_URL||"").replace(/\/$/,"")+"/rest/v1/"+path;
  const apiKey=process.env.SUPABASE_SECRET_KEY||process.env.SUPABASE_SERVICE_ROLE_KEY||process.env.SUPABASE_ANON_KEY||"";
  const headers={"apikey":apiKey,"Content-Type":"application/json","Prefer":prefer};
  if(token) headers.Authorization="Bearer "+token;
  const r=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
  const text=await r.text(); let data; try{data=text?JSON.parse(text):null}catch{data=text}
  if(!r.ok) throw new Error(typeof data==="string"?data:JSON.stringify(data));
  return data;
}
export async function requireEnv(){for(const k of ["SUPABASE_URL","SUPABASE_ANON_KEY"])if(!process.env[k])throw new Error("Missing "+k)}
export async function requireUser(req){
  const h=req.headers.authorization||""; if(!h.startsWith("Bearer "))throw new Error("Unauthorized");
  const token=h.slice(7);
  const r=await fetch((process.env.SUPABASE_URL||"").replace(/\/$/,"")+"/auth/v1/user",{headers:{apikey:process.env.SUPABASE_ANON_KEY||process.env.SUPABASE_PUBLISHABLE_KEY||"",Authorization:"Bearer "+token}});
  if(!r.ok)throw new Error("Unauthorized");
  return {user:await r.json(),token};
}
export async function getProfile(token,userId){
  const rows=await supabaseFetch("profiles?id=eq."+encodeURIComponent(userId)+"&select=id,organization_id,role",{token});
  return rows[0]||null;
}
export async function requireOrgMember(req,organizationId){
  if(!organizationId)throw new Error("organizationId required");
  const {user,token}=await requireUser(req); const profile=await getProfile(token,user.id);
  if(!profile||profile.organization_id!==organizationId)throw new Error("Forbidden: organization membership required");
  return {user,token,profile};
}
export async function adminRest(path,{method="GET",body,prefer="return=representation"}={}){
  const key=process.env.SUPABASE_SECRET_KEY||process.env.SUPABASE_SERVICE_ROLE_KEY;
  if(!key)throw new Error("Missing SUPABASE_SECRET_KEY/SUPABASE_SERVICE_ROLE_KEY");
  return supabaseFetch(path,{method,body,prefer,token:key});
}
export async function adminAuth(path,{method="GET",body}={}){
  const base=(process.env.SUPABASE_URL||"").replace(/\/$/,"");
  const key=process.env.SUPABASE_SECRET_KEY||process.env.SUPABASE_SERVICE_ROLE_KEY;
  if(!base||!key)throw new Error("Missing Supabase server credentials");
  const r=await fetch(base+"/auth/v1/admin/"+path,{method,headers:{apikey:key,Authorization:"Bearer "+key,"Content-Type":"application/json"},body:body===undefined?undefined:JSON.stringify(body)});
  const text=await r.text(); let data; try{data=text?JSON.parse(text):null}catch{data=text}
  if(!r.ok)throw new Error(typeof data==="string"?data:JSON.stringify(data));
  return data;
}
