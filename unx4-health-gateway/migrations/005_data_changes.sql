CREATE TABLE IF NOT EXISTS data_changes (
  id BIGSERIAL PRIMARY KEY,
  dataset TEXT NOT NULL,
  entity_id TEXT,
  change_type TEXT NOT NULL CHECK (change_type IN ('added','updated','removed')),
  changed_fields JSONB,
  before JSONB,
  after JSONB,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sync_run_id BIGINT REFERENCES sync_runs(id)
);
CREATE INDEX IF NOT EXISTS data_changes_dataset_idx
  ON data_changes(dataset, detected_at DESC);
CREATE INDEX IF NOT EXISTS data_changes_entity_idx
  ON data_changes(dataset, entity_id, detected_at DESC);
