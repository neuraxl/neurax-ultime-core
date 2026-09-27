CREATE TABLE IF NOT EXISTS sync_runs (
  id BIGSERIAL PRIMARY KEY,
  dataset TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  rows_count INTEGER NOT NULL DEFAULT 0,
  source_url TEXT,
  checksum TEXT,
  changed BOOLEAN NOT NULL DEFAULT TRUE,
  error TEXT
);
CREATE INDEX IF NOT EXISTS sync_runs_dataset_idx
  ON sync_runs(dataset, started_at DESC);
