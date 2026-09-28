const CATALOG=[
{ id:"passport",category:"Immigration et voyage",name:"Passeport canadien",keywords:["passeport","voyage","document","renouveler"],url:"https://www.canada.ca/fr/immigration-refugies-citoyennete/services/passeport-canadien.html",org:"IRCC"},
{ id:"tax",category:"Impôts",name:"Impôts des particuliers et entreprises",keywords:["impôt","impots","taxe","taxes","déclaration","revenu","entreprise"],url:"https://www.canada.ca/fr/agence-revenu/services/impot.html",org:"ARC"},
{ id:"sin",category:"Identité et emploi",name:"Numéro d'assurance sociale (NAS)",keywords:["nas","numero assurance sociale","sin","social insurance","emploi"],url:"https://www.canada.ca/fr/emploi-developpement-social/services/numero-assurance-sociale.html",org:"EDSC"},
{ id:"immigration",category:"Immigration",name:"Visas, permis et immigration",keywords:["immigration","visa","visas","permis","résidence permanente","citoyenneté"],url:"https://www.canada.ca/fr/immigration-refugies-citoyennete.html",org:"IRCC"},
{ id:"benefits",category:"Prestations",name:"Prestations et crédits",keywords:["prestation","prestations","allocation","crédit","enfant","retraite","aide financière"],url:"https://www.canada.ca/fr/services/prestations.html",org:"Canada.ca"},
{ id:"employment",category:"Emploi",name:"Emplois et formation",keywords:["emploi","emplois","travail","formation","chômage","assurance emploi"],url:"https://www.canada.ca/fr/services/emplois.html",org:"EDSC"},
{ id:"health",category:"Santé",name:"Services de santé",keywords:["santé","sante","soins","médicament","dentaire","dentaire canadien"],url:"https://www.canada.ca/fr/services/sante.html",org:"Santé Canada"},
{ id:"funding",category:"Financement",name:"Subventions et financement",keywords:["subvention","financement","fonds","aide","entreprise","programme"],url:"https://www.canada.ca/fr/services/financement.html",org:"Canada.ca"}
];

const RESOURCES=[
["Contact Canada.ca","https://www.canada.ca/fr/contact.html","Portail de coordonnées fédérales"],
["Services du gouvernement","https://www.canada.ca/fr/services.html","Catalogue des services fédéraux"],
["Répertoire des employés du gouvernement","https://gcdirectory-gcannuaire.ssc-spc.gc.ca/","Répertoire officiel"],
["Trouver votre député","https://www.noscommunes.ca/members/fr","Députés de la Chambre des communes"],
["Membres du Sénat","https://sencanada.ca/fr/senateurs/","Sénateurs"],
["Représentants étrangers au Canada","https://www.international.gc.ca/protocol-protocole/reps.aspx?lang=fra","Répertoire du protocole"],
["Agence du revenu du Canada","https://www.canada.ca/fr/agence-revenu.html","Organisme fiscal fédéral"],
["Service Canada","https://www.canada.ca/fr/emploi-developpement-social/ministere/portefeuille/service-canada.html","Programmes et services administrés par Service Canada"]
];

const SOURCE={url:"https://www.canada.ca/fr/contact.html",checkedAt:new Date().toISOString(),authority:"Canada.ca"};

function normalize(s=""){return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
function score(item,q){
 const n=normalize(q); if(!n)return 1;
 const hay=normalize([item.name,item.category,item.org,...item.keywords].join(" "));
 let s=hay.includes(n)?10:0;
 for(const k of item.keywords){if(normalize(k).includes(n)||n.includes(normalize(k)))s+=5;}
 for(const token of n.split(/\s+/).filter(Boolean)){if(hay.includes(token))s+=1;}
 return s;
}
function emit(type,payload={}){
 const event={type,timestamp:new Date().toISOString(),source:"unx2-civic-gateway",...payload};
 window.__UNX2_TELEMETRY__=(window.__UNX2_TELEMETRY__||[]);
 window.__UNX2_TELEMETRY__.push(event);
 window.dispatchEvent(new CustomEvent("unx2:civic",{detail:event}));
}
function render(q=""){
 const results=CATALOG.map(x=>({...x,_score:score(x,q)})).filter(x=>!q||x._score>0).sort((a,b)=>b._score-a._score);
 document.querySelector("#serviceGrid").innerHTML=results.map(x=>`<article data-id="${x.id}"><small>${x.category}</small><b>${x.org}</b><h3>${x.name}</h3><p>Source: Canada.ca • Vérification: ${SOURCE.checkedAt.slice(0,10)}</p><a href="${x.url}" target="_blank" rel="noopener" onclick="emit('civic.handoff',{service:'${x.id}'})">Ouvrir la source officielle ↗</a></article>`).join("")||"<p>Aucun service correspondant. Essayez une autre formulation.</p>";
 emit("civic.search",{query:q,results:results.length});
}
function findService(){render(document.querySelector("#q").value.trim());}
function routeNaturalLanguage(q){
 const results=CATALOG.map(x=>({...x,_score:score(x,q)})).sort((a,b)=>b._score-a._score).slice(0,3);
 emit("civic.route",{query:q,candidates:results.map(x=>x.id)});
 return results;
}
window.UNX2_CIVIC={catalog:CATALOG,resources:RESOURCES,source:SOURCE,search:routeNaturalLanguage,telemetry:()=>window.__UNX2_TELEMETRY__||[]};

render();
document.querySelector("#links").innerHTML=RESOURCES.map(x=>`<a href="${x[1]}" target="_blank" rel="noopener">↗ ${x[0]}</a>`).join("");
document.querySelector("#q").addEventListener("keydown",e=>{if(e.key==="Enter")findService();});
