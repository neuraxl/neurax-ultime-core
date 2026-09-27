import json, os
import psycopg
from psycopg.rows import dict_row

DB=os.getenv("DATABASE_URL","postgresql://unx4:unx4@localhost:5432/unx4")
def conn(): return psycopg.connect(DB,row_factory=dict_row)

def init_graph():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS knowledge_nodes(
          id TEXT PRIMARY KEY,node_type TEXT NOT NULL,label TEXT,properties JSONB,
          updated_at TIMESTAMPTZ DEFAULT now())""")
        c.execute("""CREATE TABLE IF NOT EXISTS knowledge_edges(
          id BIGSERIAL PRIMARY KEY,source_id TEXT NOT NULL,target_id TEXT NOT NULL,
          relation TEXT NOT NULL,properties JSONB,
          UNIQUE(source_id,target_id,relation))""")

def upsert_node(node_id,node_type,label,properties=None):
    with conn() as c:
        c.execute("""INSERT INTO knowledge_nodes(id,node_type,label,properties)
          VALUES(%s,%s,%s,%s)
          ON CONFLICT(id) DO UPDATE SET label=EXCLUDED.label,properties=EXCLUDED.properties,updated_at=now()""",
          (node_id,node_type,label,json.dumps(properties or {},default=str)))

def link(source_id,target_id,relation,properties=None):
    with conn() as c:
        c.execute("""INSERT INTO knowledge_edges(source_id,target_id,relation,properties)
          VALUES(%s,%s,%s,%s)
          ON CONFLICT(source_id,target_id,relation) DO UPDATE SET properties=EXCLUDED.properties""",
          (source_id,target_id,relation,json.dumps(properties or {},default=str)))

def graph_snapshot(limit=500):
    with conn() as c:
        nodes=c.execute("SELECT id,node_type,label,properties FROM knowledge_nodes ORDER BY id LIMIT %s",(limit,)).fetchall()
        edges=c.execute("SELECT source_id,target_id,relation,properties FROM knowledge_edges ORDER BY id LIMIT %s",(limit,)).fetchall()
    return {"nodes":nodes,"edges":edges}
