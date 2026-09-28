const FEDERAL_HINTS=["canada","fédéral","federal","assurance-emploi","passeport canadien","nas","impôt fédéral","arc","immigration"];
const QUEBEC_HINTS=["québec","quebec","services québec","aide sociale","solidarité sociale","revenu québec","emploi québec","ramq","saaq","retraite québec","impôt du québec"];
const MUNICIPAL_HINTS=["ville","municipal","municipalité","arrondissement","taxes municipales","permis"];

function norm(v){return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();}
function jurisdiction(q){
  const x=norm(q);
  const f=FEDERAL_HINTS.some(k=>x.includes(norm(k)));
  const qc=QUEBEC_HINTS.some(k=>x.includes(norm(k)));
  const m=MUNICIPAL_HINTS.some(k=>x.includes(norm(k)));
  if(m) return "municipal";
  if(qc && f) return "federal+quebec";
  if(qc) return "quebec";
  if(f) return "federal";
  return "undetermined";
}
function route(q,{federal=[],quebec=[]}={}){
  const x=norm(q), j=jurisdiction(q);
  const score=s=>(s.keywords||[]).reduce((n,k)=>n+(x.includes(norm(k))?2:0),0);
  const pool=[...federal.map(s=>({...s,jurisdiction:"federal"})),...quebec.map(s=>({...s,jurisdiction:"quebec"}))];
  const ranked=pool.map(s=>({...s,matchScore:score(s)})).filter(s=>s.matchScore>0).sort((a,b)=>b.matchScore-a.matchScore);
  return {schema:"unx2.civic.route.v0.4",query:q,jurisdiction:j,candidates:ranked.slice(0,6),provenance:{officialSourceFirst:true,humanHandoff:true}};
}
window.UNX2_CIVIC_ROUTER={jurisdiction,route};
