import http from "node:http";
import {WebSocketServer} from "ws";
const PORT=Number(process.env.PORT||8787),SUPABASE_URL=(process.env.SUPABASE_URL||"").replace(/\/$/,"");
const SUPABASE_KEY=process.env.SUPABASE_ANON_KEY||process.env.SUPABASE_PUBLISHABLE_KEY||"",SECRET=process.env.LEVIATHAN_RUNTIME_SECRET||"";
const peers=new Map();
async function authenticate(token,org){
  if(!token||!org||!SUPABASE_URL||!SUPABASE_KEY)return null;
  const r=await fetch(SUPABASE_URL+"/auth/v1/user",{headers:{apikey:SUPABASE_KEY,Authorization:"Bearer "+token}});
  if(!r.ok)return null; const user=await r.json();
  const p=await fetch(SUPABASE_URL+"/rest/v1/profiles?id=eq."+encodeURIComponent(user.id)+"&organization_id=eq."+encodeURIComponent(org)+"&select=id",{headers:{apikey:SUPABASE_KEY,Authorization:"Bearer "+token}});
  if(!p.ok||!(await p.json()).length)return null; return user;
}
function send(ws,payload){if(ws.readyState===1)ws.send(JSON.stringify(payload))}
const server=http.createServer(async(req,res)=>{
  if(req.url==="/health"){res.writeHead(200,{"Content-Type":"application/json"});return res.end(JSON.stringify({service:"LÉVIATHAN Runtime",status:"operational",connections:[...peers.values()].reduce((n,s)=>n+s.size,0)}))}
  if(req.method==="POST"&&req.url==="/publish"){
    if(!SECRET||req.headers.authorization!=="Bearer "+SECRET){res.writeHead(401);return res.end("Unauthorized")}
    let raw="";for await(const c of req)raw+=c;let event;try{event=JSON.parse(raw)}catch{res.writeHead(400);return res.end("Invalid JSON")}
    const set=peers.get(event.organization_id)||new Set();for(const ws of set)send(ws,{type:"telemetry",event});
    res.writeHead(202,{"Content-Type":"application/json"});return res.end(JSON.stringify({published:set.size}));
  }
  res.writeHead(404);res.end();
});
const wss=new WebSocketServer({server,path:"/ws"});
wss.on("connection",async(ws,req)=>{
  const u=new URL(req.url,"http://localhost"),token=u.searchParams.get("token"),org=u.searchParams.get("organization_id"),user=await authenticate(token,org);
  if(!user){ws.close(1008,"Unauthorized");return}
  if(!peers.has(org))peers.set(org,new Set());peers.get(org).add(ws);
  send(ws,{type:"connected",organization_id:org,user_id:user.id,service:"LÉVIATHAN"});
  ws.on("close",()=>{const set=peers.get(org);if(set){set.delete(ws);if(!set.size)peers.delete(org)}});
});
server.listen(PORT,()=>console.log("LÉVIATHAN WebSocket runtime listening on "+PORT));