import io, json, math, os, re, time, threading, hashlib
from datetime import datetime, timezone
from typing import Any
import httpx, pandas as pd
import psycopg
from psycopg.rows import dict_row
from redis import Redis
from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .graph import init_graph, upsert_node, link, graph_snapshot

DB=os.getenv("DATABASE_URL","postgresql://unx4:unx4@localhost:5432/unx4")
REDIS=os.getenv("REDIS_URL","redis://localhost:6379/0")
CKAN=os.getenv("CKAN_BASE_URL","https://www.donneesquebec.ca/recherche/api/3/action")
redis=Redis.from_url(REDIS,decode_responses=True)
app=FastAPI(title="UNX4 Health Gateway",version="0.4.0",description="Public Québec health data gateway for UNX4.")
sync_lock=threading.Lock()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

SOURCES={
 "facilities":"51998b55-7d4c-4381-8c20-0ac1cd9c1b87",
 "services":"e442a663-e069-4209-a4ba-7bd60f6c5fb4",
 "emergency":"d4541afe-9391-44bf-a78f-dae3c9cf1217"
}

def conn():
    return psycopg.connect(DB,row_factory=dict_row)

def event(kind,payload):
    msg={"event":kind,"timestamp":datetime.now(timezone.utc).isoformat(),"payload":payload}
    redis.publish("unx4.health",json.dumps(msg,default=str))
    with conn() as c:
        c.execute("INSERT INTO telemetry(event_type,source,payload) VALUES(%s,%s,%s)",(kind,"UNX4 Health Gateway",json.dumps(payload,default=str)))
    return msg

def init():
    with conn() as c:
        c.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        c.execute("""CREATE TABLE IF NOT EXISTS datasets(
          id TEXT PRIMARY KEY,name TEXT,source_url TEXT,license TEXT,update_frequency TEXT,
          retrieved_at TIMESTAMPTZ,resource_url TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS facilities(
          id TEXT PRIMARY KEY,name TEXT,kind TEXT,region TEXT,territory TEXT,
          latitude DOUBLE PRECISION,longitude DOUBLE PRECISION,
          geom geometry(Point,4326),source_dataset TEXT,source_url TEXT,
          source_updated_at TEXT,raw JSONB)""")
        c.execute("""CREATE TABLE IF NOT EXISTS services(
          id BIGSERIAL PRIMARY KEY,facility_id TEXT,name TEXT,category TEXT,
          capacity TEXT,source_dataset TEXT,source_url TEXT,raw JSONB,
          UNIQUE(facility_id,name,category))""")
        c.execute("""CREATE TABLE IF NOT EXISTS emergency_status(
          id BIGSERIAL PRIMARY KEY,facility_name TEXT,facility_id TEXT,data_time TEXT,
          stretchers DOUBLE PRECISION,patients DOUBLE PRECISION,over_24h DOUBLE PRECISION,
          over_48h DOUBLE PRECISION,present DOUBLE PRECISION,waiting DOUBLE PRECISION,
          source_dataset TEXT,source_url TEXT,raw JSONB,ingested_at TIMESTAMPTZ DEFAULT now())""")
        c.execute("CREATE INDEX IF NOT EXISTS facilities_geom_gix ON facilities USING GIST(geom)")
        c.execute("""CREATE TABLE IF NOT EXISTS telemetry(
          id BIGSERIAL PRIMARY KEY,event_type TEXT,source TEXT,payload JSONB,
          created_at TIMESTAMPTZ DEFAULT now())""")
        c.execute("""CREATE TABLE IF NOT EXISTS sync_runs(
          id BIGSERIAL PRIMARY KEY,dataset TEXT NOT NULL,status TEXT NOT NULL,
          started_at TIMESTAMPTZ NOT NULL DEFAULT now(),finished_at TIMESTAMPTZ,
          rows_count INTEGER DEFAULT 0,source_url TEXT,checksum TEXT,
          changed BOOLEAN DEFAULT TRUE,error TEXT)""")

@app.on_event("startup")
def startup():
    init()
    init_graph()

async def package_show(dataset_id):
    async with httpx.AsyncClient(timeout=30) as x:
        r=await x.get(f"{CKAN}/package_show",params={"id":dataset_id}); r.raise_for_status()
        return r.json()["result"]

async def resource_csv(dataset_id, prefer=None):
    d=await package_show(dataset_id)
    resources=d.get("resources",[])
    csvs=[r for r in resources if "csv" in (r.get("format") or "").lower() or str(r.get("url","")).lower().endswith(".csv")]
    if prefer:
        for r in csvs:
            if prefer.lower() in (r.get("name","")+" "+r.get("url","")).lower(): return d,r
    return d,(csvs[0] if csvs else None)

def norm(v):
    return re.sub(r"[^a-z0-9]","",str(v).lower())

def pick(row,*keys):
    m={norm(k):v for k,v in row.items()}
    for k in keys:
        if norm(k) in m and pd.notna(m[norm(k)]): return m[norm(k)]
    for k,v in row.items():
        nk=norm(k)
        if any(norm(q) in nk for q in keys) and pd.notna(v): return v
    return None

def num(v):
    try:
        return float(str(v).replace(",",".").replace(" ",""))
    except: return None

def source_checksum(raw):
    return hashlib.sha256(raw).hexdigest()

def cache_key(prefix, params):
    raw=json.dumps(params, sort_keys=True, default=str)
    return "unx4:health:"+prefix+":"+hashlib.sha256(raw.encode()).hexdigest()

def cache_get(key):
    try:
        value=redis.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None

def cache_set(key, value, ttl=60):
    try:
        redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass

def invalidate_cache():
    try:
        keys=list(redis.scan_iter("unx4:health:*"))
        if keys:
            redis.delete(*keys)
    except Exception:
        pass

async def ingest_facilities():
    d,r=await resource_csv(SOURCES["facilities"],"installations")
    if not r: raise RuntimeError("CSV installations introuvable")
    raw=(await httpx.AsyncClient(timeout=60).get(r["url"])).content
    df=pd.read_csv(io.BytesIO(raw),sep=None,engine="python",encoding_errors="replace")
    n=0
    with conn() as c:
        for _,rr in df.iterrows():
            row=rr.to_dict()
            ident=str(pick(row,"Code_Installation","Code Installation","Installation","No_Installation","CodeInstallation") or pick(row,"Nom_Installation","Nom Installation") or "")
            name=str(pick(row,"Nom_Installation","Nom Installation","Installation") or ident)
            lat=num(pick(row,"Latitude","Lat","LATITUDE")); lon=num(pick(row,"Longitude","Lon","LONGITUDE"))
            if not ident or ident=="nan": continue
            c.execute("""INSERT INTO facilities(id,name,kind,region,territory,latitude,longitude,geom,source_dataset,source_url,raw)
              VALUES(%s,%s,'installation',%s,%s,%s,%s,CASE WHEN %s IS NOT NULL AND %s IS NOT NULL THEN ST_SetSRID(ST_MakePoint(%s,%s),4326) END,%s,%s,%s)
              ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,region=EXCLUDED.region,territory=EXCLUDED.territory,
              latitude=EXCLUDED.latitude,longitude=EXCLUDED.longitude,geom=EXCLUDED.geom,raw=EXCLUDED.raw""",
              (ident,name,str(pick(row,"RSS_Installation","RSS Installation","Région sociosanitaire")),
               str(pick(row,"RTS_Installation","RTS Installation","Territoire")),
               lat,lon,lat,lon,lon,lat,SOURCES["facilities"],r["url"],json.dumps(row,default=str)))
            upsert_node("facility:"+ident,"Facility",name,row)
            n+=1
    return n,r["url"],source_checksum(raw)

async def ingest_services():
    d,r=await resource_csv(SOURCES["services"],"2024-04-01")
    if not r: raise RuntimeError("CSV capacités/services introuvable")
    async with httpx.AsyncClient(timeout=90) as x:
        resp=await x.get(r["url"]); resp.raise_for_status(); raw=resp.content
    df=pd.read_csv(io.BytesIO(raw),sep=None,engine="python",encoding_errors="replace")
    n=0
    with conn() as c:
        for _,rr in df.iterrows():
            row=rr.to_dict()
            fid=str(pick(row,"Code_Installation","Code Installation","CodeInstallation","Installation") or "")
            svc=str(pick(row,"Nom_Service","Nom Service","Service","Description_Service","Mission") or "").strip()
            if not fid or not svc or fid=="nan": continue
            cap=pick(row,"Capacité","Capacite","Nombre","Valeur")
            cat=pick(row,"Catégorie","Categorie","Mission","Type_Service")
            c.execute("""INSERT INTO services(facility_id,name,category,capacity,source_dataset,source_url,raw)
              VALUES(%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(facility_id,name,category) DO UPDATE SET capacity=EXCLUDED.capacity,raw=EXCLUDED.raw""",
              (fid,svc,str(cat or ""),str(cap or ""),SOURCES["services"],r["url"],json.dumps(row,default=str)))
            upsert_node("facility:"+fid,"Facility",fid,{})
            upsert_node("service:"+fid+":"+svc,"Service",svc,{"category":cat,"capacity":cap})
            link("facility:"+fid,"service:"+fid+":"+svc,"OFFERS")
            n+=1
    return n,r["url"]

async def ingest_emergency():
    d,r=await resource_csv(SOURCES["emergency"],"situation à l'urgence")
    if not r:
        d,r=await resource_csv(SOURCES["emergency"])
    if not r: raise RuntimeError("CSV urgences introuvable")
    async with httpx.AsyncClient(timeout=60) as x:
        resp=await x.get(r["url"]); resp.raise_for_status(); raw=resp.content
    df=pd.read_csv(io.BytesIO(raw),sep=None,engine="python",encoding_errors="replace")
    n=0
    with conn() as c:
        for _,rr in df.iterrows():
            row=rr.to_dict()
            name=str(pick(row,"Installation","Nom Installation","Nom_Installation") or "").strip()
            if not name: continue
            vals=dict(
              facility_name=name, data_time=str(pick(row,"Date","Date_heure","Date et heure","Heure") or ""),
              stretchers=num(pick(row,"Civières fonctionnelles","Civieres fonctionnelles","Civières")),
              patients=num(pick(row,"Patients sur civière","Patients sur civieres")),
              over_24h=num(pick(row,"Patients sur civière > 24h","Patients sur civieres > 24h","Plus de 24")),
              over_48h=num(pick(row,"Patients sur civière > 48h","Patients sur civieres > 48h","Plus de 48")),
              present=num(pick(row,"Personnes présentes","Personnes presentes","Présents")),
              waiting=num(pick(row,"Patients en attente","En attente")))
            c.execute("""INSERT INTO emergency_status(facility_name,data_time,stretchers,patients,over_24h,over_48h,present,waiting,source_dataset,source_url,raw)
              SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s""",
              (vals["facility_name"],vals["data_time"],vals["stretchers"],vals["patients"],vals["over_24h"],vals["over_48h"],vals["present"],vals["waiting"],SOURCES["emergency"],r["url"],json.dumps(row,default=str)))
            n+=1
    return n,r["url"]

@app.get("/")
def root(): return FileResponse("static/index.html")

@app.get("/healthz")
def healthz():
    return {"status":"ok","service":"unx4-health-gateway","version":"0.3.0"}

@app.get("/readyz")
def readyz():
    checks={"database":False,"redis":False}
    try:
        with conn() as c:
            c.execute("SELECT 1")
        checks["database"]=True
    except Exception:
        pass
    try:
        checks["redis"]=bool(redis.ping())
    except Exception:
        pass
    ok=all(checks.values())
    return {"status":"ready" if ok else "not_ready","checks":checks}

@app.get("/api/health/status")
def status():
    with conn() as c:
        db=c.execute("SELECT count(*) n FROM facilities").fetchone()["n"]
        sv=c.execute("SELECT count(*) n FROM services").fetchone()["n"]
        er=c.execute("SELECT count(*) n FROM emergency_status").fetchone()["n"]
    return {"module":"UNX4 Health Gateway","version":"0.3.0","status":"operational","public_data_only":True,"facilities":db,"services":sv,"emergency_rows":er}

@app.post("/api/health/sync")
async def sync():
    if not sync_lock.acquire(blocking=False):
        raise HTTPException(409,"Une synchronisation est déjà en cours")
    try:
        t=time.perf_counter(); results={}
        event("health.sync.started",{})
        for name,fn in [("facilities",ingest_facilities),("services",ingest_services),("emergency",ingest_emergency)]:
            run_id=None
            try:
                with conn() as c:
                    row=c.execute("INSERT INTO sync_runs(dataset,status) VALUES(%s,'running') RETURNING id",(name,)).fetchone()
                    run_id=row["id"]
                count,url,checksum=await fn()
                with conn() as c:
                    c.execute("UPDATE sync_runs SET status='completed',finished_at=now(),rows_count=%s,source_url=%s,checksum=%s WHERE id=%s",(count,url,checksum,run_id))
                results[name]={"rows":count,"url":url,"checksum":checksum,"sync_run_id":run_id}
                event(f"health.{name}.ingested",results[name])
            except Exception as e:
                if run_id:
                    with conn() as c:
                        c.execute("UPDATE sync_runs SET status='failed',finished_at=now(),error=%s WHERE id=%s",(str(e),run_id))
                results[name]={"error":str(e),"sync_run_id":run_id}
                event("health.ingest.error",{"dataset":name,"error":str(e)})
        results["duration_ms"]=round((time.perf_counter()-t)*1000,2)
        event("health.sync.completed",results)
        return results
    finally:
        sync_lock.release()

@app.get("/api/health/sync/runs")
def sync_runs(limit:int=20):
    limit=max(1,min(limit,100))
    with conn() as c:
        rows=c.execute("SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT %s",(limit,)).fetchall()
    return {"count":len(rows),"items":rows}

@app.get("/api/health/facilities")
def facilities(region:str|None=None,service:str|None=None,lat:float|None=None,lon:float|None=None,radius_km:float=25,limit:int=100):
    if radius_km <= 0 or radius_km > 500:
        raise HTTPException(400,"radius_km doit être compris entre 0 et 500")
    if limit <= 0 or limit > 1000:
        raise HTTPException(400,"limit doit être compris entre 1 et 1000")
    clauses=[]; args=[]
    if region: clauses.append("f.region ILIKE %s"); args.append("%"+region+"%")
    if service:
        clauses.append("EXISTS (SELECT 1 FROM services s WHERE s.facility_id=f.id AND s.name ILIKE %s)"); args.append("%"+service+"%")
    if lat is not None and lon is not None:
        clauses.append("f.geom IS NOT NULL AND ST_DWithin(f.geom::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)")
        args += [lon,lat,radius_km*1000]
    where=(" WHERE "+" AND ".join(clauses)) if clauses else ""
    with conn() as c:
        rows=c.execute(f"""SELECT f.id,f.name,f.region,f.territory,f.latitude,f.longitude,
          f.source_dataset,f.source_url,
          COALESCE(json_agg(DISTINCT jsonb_build_object('name',s.name,'category',s.category,'capacity',s.capacity))
            FILTER(WHERE s.id IS NOT NULL),'[]') services,
          (SELECT jsonb_build_object('data_time',e.data_time,'patients',e.patients,'over_24h',e.over_24h,'over_48h',e.over_48h,'present',e.present)
           FROM emergency_status e WHERE e.facility_name ILIKE f.name ORDER BY e.ingested_at DESC LIMIT 1) emergency
          FROM facilities f LEFT JOIN services s ON s.facility_id=f.id {where}
          GROUP BY f.id ORDER BY f.name LIMIT %s""",args+[limit]).fetchall()
    return {"count":len(rows),"items":rows}

@app.get("/api/health/facilities/{facility_id}")
def facility(facility_id:str):
    with conn() as c:
        f=c.execute("SELECT * FROM facilities WHERE id=%s",(facility_id,)).fetchone()
        if not f: raise HTTPException(404,"Installation inconnue")
        sv=c.execute("SELECT id,name,category,capacity,source_url FROM services WHERE facility_id=%s",(facility_id,)).fetchall()
        er=c.execute("SELECT * FROM emergency_status WHERE facility_name ILIKE %s ORDER BY ingested_at DESC LIMIT 1",(f["name"],)).fetchone()
    return {"facility":f,"services":sv,"emergency":er,"provenance":{"dataset":f["source_dataset"],"url":f["source_url"]}}

@app.get("/api/health/services")
def services(q:str|None=None,limit:int=100):
    with conn() as c:
        rows=c.execute("SELECT name,category,count(*) AS facilities FROM services WHERE (%s IS NULL OR name ILIKE %s) GROUP BY name,category ORDER BY facilities DESC LIMIT %s",(q,"%"+q+"%" if q else None,limit)).fetchall()
    return {"count":len(rows),"items":rows}

@app.get("/api/health/regions")
def regions():
    with conn() as c: rows=c.execute("SELECT region,count(*) facilities FROM facilities GROUP BY region ORDER BY region").fetchall()
    return {"items":rows}

@app.get("/api/health/graph")
def graph(limit:int=500):
    return graph_snapshot(limit)

@app.get("/api/health/telemetry")
def telemetry(limit:int=100):
    with conn() as c: rows=c.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT %s",(limit,)).fetchall()
    return {"count":len(rows),"items":rows}

@app.get("/api/health/provenance")
def provenance():
    return {"datasets":[
      {"id":SOURCES["facilities"],"name":"M02 installations/établissements","license":"CC-BY 4.0","url":"https://www.donneesquebec.ca/recherche/dataset/fichiers-cartographiques-m02-des-installations-et-etablissements"},
      {"id":SOURCES["services"],"name":"M02 capacités et services","license":"CC-BY 4.0","url":"https://www.donneesquebec.ca/recherche/dataset/m02-repartition-des-capacites-et-des-services-autorises-au-permis-par-installation"},
      {"id":SOURCES["emergency"],"name":"Situation horaire à l'urgence","license":"CC-BY 4.0","url":"https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence"}]}

@app.websocket("/ws/health")
async def ws(ws:WebSocket):
    await ws.accept(); await ws.send_json({"event":"connected","module":"UNX4 Health Gateway"})
    pub=redis.pubsub(); pub.subscribe("unx4.health")
    try:
        while True:
            msg=pub.get_message(ignore_subscribe_messages=True,timeout=20)
            if msg: await ws.send_text(msg["data"])
            else: await ws.send_json({"event":"heartbeat","timestamp":datetime.now(timezone.utc).isoformat()})
    except Exception: pass
    finally: pub.close()
