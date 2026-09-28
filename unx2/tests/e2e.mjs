import assert from "node:assert/strict";
const base=(process.env.UNX2_BASE_URL||"").replace(/\/$/,""),email=process.env.E2E_EMAIL,password=process.env.E2E_PASSWORD,organizationName=process.env.E2E_ORGANIZATION||"UNX2 E2E Tenant";
if(!base||!email||!password)throw new Error("Set UNX2_BASE_URL, E2E_EMAIL and E2E_PASSWORD");
async function call(path,options={}){
  const r=await fetch(base+path,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
  const d=await r.json().catch(()=>({}));assert.equal(r.ok,true,path+" failed: "+JSON.stringify(d));return d;
}
const signup=await call("/api/auth/signup",{method:"POST",body:JSON.stringify({email,password,organizationName})});
const login=await call("/api/auth/login",{method:"POST",body:JSON.stringify({email,password})});
assert.ok(login.access_token,"login must return access_token");
const token=login.access_token,org=signup.organization?.id||login.organization_id;assert.ok(org,"signup must create tenant");
const headers={Authorization:"Bearer "+token,"Content-Type":"application/json"};
const diagnostic=await call("/api/diagnostic",{method:"POST",headers,body:JSON.stringify({organizationId:org,company:"E2E Pilot",operations:"Prospects par courriel, qualification, CRM et rapport hebdomadaire."})});
assert.ok(diagnostic.diagnostic_id);
const agent=await call("/api/agent",{method:"POST",headers,body:JSON.stringify({organizationId:org,agentName:"E2E Agent",task:"Résume en une phrase le prochain geste commercial."})});
assert.ok(agent.text!==undefined);
const workflow=await call("/api/workflow",{method:"POST",headers,body:JSON.stringify({organizationId:org})});
assert.equal(workflow.status,"completed");assert.ok(workflow.run_id);
const lead=await call("/api/crm/leads?organization_id="+encodeURIComponent(org),{method:"POST",headers,body:JSON.stringify({company_name:"E2E Prospect",score:91,status:"qualified"})});
assert.ok(lead.id);
const telemetry=await call("/api/telemetry?organization_id="+encodeURIComponent(org),{headers});
assert.ok(Array.isArray(telemetry.events)&&telemetry.events.length>=8,"telemetry chain incomplete");
let checkout=null;
try{checkout=await call("/api/stripe/create-checkout",{method:"POST",headers,body:JSON.stringify({organizationId:org})})}
catch(e){if(process.env.REQUIRE_STRIPE==="1")throw e;console.log("Stripe skipped: configure STRIPE_* and set REQUIRE_STRIPE=1 for mandatory payment test")}
if(checkout)assert.ok(checkout.url);
console.log(JSON.stringify({pass:true,organization_id:org,diagnostic_id:diagnostic.diagnostic_id,run_id:workflow.run_id,lead_id:lead.id,telemetry_events:telemetry.events.length,stripe:!!checkout},null,2));