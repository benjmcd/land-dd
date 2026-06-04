-- 02 Postgres/PostGIS Storage Spec
-- Executable draft. Validate against your selected Postgres/PostGIS version before production.
-- Design goal: Postgres/PostGIS as the system of record for sources, areas, evidence, claims, rules, reports, jobs, audit, and vector-derived facts.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS geo;
CREATE SCHEMA IF NOT EXISTS evidence;
CREATE SCHEMA IF NOT EXISTS rules;
CREATE SCHEMA IF NOT EXISTS claims;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS jobs;
CREATE SCHEMA IF NOT EXISTS audit;

DO $$ BEGIN
    CREATE TYPE core.area_type AS ENUM ('parcel','multi_parcel','polygon','address','locality','county','watershed','corridor','generated_candidate');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE core.intent_code AS ENUM ('rural_land_purchase','homestead_feasibility','farmland','development','solar','data_center','conservation','mineral_resource_screen','speculative_hold');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE evidence.authority_level AS ENUM ('official_primary','official_secondary','commercial_normalized','open_community','derived_model','user_supplied','unknown');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE evidence.confidence_band AS ENUM ('very_low','low','medium','high','very_high','unknown');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE claims.severity_band AS ENUM ('critical','high','medium','low','informational','unknown');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE jobs.job_status AS ENUM ('queued','running','succeeded','failed','cancelled','needs_review');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS core.workspaces (
    workspace_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    plan_code text NOT NULL DEFAULT 'internal',
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS core.users (
    user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES core.workspaces(workspace_id),
    email citext NOT NULL,
    role_code text NOT NULL DEFAULT 'member',
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(workspace_id, email)
);

CREATE TABLE IF NOT EXISTS core.areas (
    area_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid REFERENCES core.workspaces(workspace_id),
    area_type core.area_type NOT NULL,
    label text,
    input_reference text,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    geom_validated boolean NOT NULL DEFAULT false,
    geom_source text,
    geom_confidence evidence.confidence_band NOT NULL DEFAULT 'unknown',
    centroid geometry(Point, 4326) GENERATED ALWAYS AS (ST_Centroid(geom)) STORED,
    bbox geometry(Polygon, 4326) GENERATED ALWAYS AS (ST_Envelope(geom)) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES core.users(user_id),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS areas_geom_gix ON core.areas USING gist (geom);
CREATE INDEX IF NOT EXISTS areas_workspace_idx ON core.areas (workspace_id);

CREATE TABLE IF NOT EXISTS core.area_versions (
    area_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    version_num integer NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    change_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES core.users(user_id),
    UNIQUE(area_id, version_num)
);
CREATE INDEX IF NOT EXISTS area_versions_geom_gix ON core.area_versions USING gist (geom);

CREATE TABLE IF NOT EXISTS core.intents (
    intent_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_code core.intent_code NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL,
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS core.intent_versions (
    intent_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id uuid NOT NULL REFERENCES core.intents(intent_id),
    version_label text NOT NULL,
    definition jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz,
    UNIQUE(intent_id, version_label)
);

CREATE TABLE IF NOT EXISTS source.sources (
    source_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    organization text,
    homepage_url text,
    authority_level evidence.authority_level NOT NULL DEFAULT 'unknown',
    geographic_scope text,
    domain text NOT NULL,
    update_cadence text,
    commercial_use_status text NOT NULL DEFAULT 'unknown',
    license_summary text,
    attribution_required boolean NOT NULL DEFAULT false,
    ai_use_allowed text NOT NULL DEFAULT 'unknown',
    cache_allowed text NOT NULL DEFAULT 'unknown',
    export_allowed text NOT NULL DEFAULT 'unknown',
    raw_data_allowed text NOT NULL DEFAULT 'unknown',
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(name, organization)
);

CREATE TABLE IF NOT EXISTS source.datasets (
    dataset_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES source.sources(source_id),
    dataset_name text NOT NULL,
    dataset_code text,
    domain text NOT NULL,
    geometry_type text,
    spatial_resolution text,
    temporal_coverage text,
    legal_caveat text,
    source_url text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(source_id, dataset_name)
);

CREATE TABLE IF NOT EXISTS source.dataset_versions (
    dataset_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id uuid NOT NULL REFERENCES source.datasets(dataset_id),
    version_label text NOT NULL,
    published_at timestamptz,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    valid_from timestamptz,
    valid_to timestamptz,
    checksum text,
    storage_uri text,
    manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_current boolean NOT NULL DEFAULT false,
    notes text,
    UNIQUE(dataset_id, version_label, retrieved_at)
);

CREATE TABLE IF NOT EXISTS source.ingest_runs (
    ingest_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_version_id uuid REFERENCES source.dataset_versions(dataset_version_id),
    connector_name text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status jobs.job_status NOT NULL DEFAULT 'queued',
    row_count integer,
    error_count integer NOT NULL DEFAULT 0,
    warning_count integer NOT NULL DEFAULT 0,
    log_uri text,
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS geo.parcels (
    parcel_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_version_id uuid NOT NULL REFERENCES source.dataset_versions(dataset_version_id),
    jurisdiction_code text NOT NULL,
    parcel_identifier text NOT NULL,
    owner_name text,
    situs_address text,
    mailing_address text,
    assessed_value numeric,
    tax_year integer,
    acreage numeric,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    source_attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(dataset_version_id, jurisdiction_code, parcel_identifier)
);
CREATE INDEX IF NOT EXISTS parcels_geom_gix ON geo.parcels USING gist (geom);
CREATE INDEX IF NOT EXISTS parcels_jurisdiction_idx ON geo.parcels (jurisdiction_code);
CREATE INDEX IF NOT EXISTS parcels_identifier_trgm_idx ON geo.parcels USING gin (parcel_identifier gin_trgm_ops);

CREATE TABLE IF NOT EXISTS geo.reference_features (
    feature_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_version_id uuid NOT NULL REFERENCES source.dataset_versions(dataset_version_id),
    feature_type text NOT NULL,
    feature_code text,
    name text,
    geom geometry(Geometry, 4326) NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS reference_features_geom_gix ON geo.reference_features USING gist (geom);
CREATE INDEX IF NOT EXISTS reference_features_type_idx ON geo.reference_features (feature_type);

CREATE TABLE IF NOT EXISTS geo.area_metrics (
    area_metric_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    dataset_version_id uuid REFERENCES source.dataset_versions(dataset_version_id),
    metric_code text NOT NULL,
    metric_value numeric,
    metric_unit text,
    method_code text NOT NULL,
    method_version text NOT NULL,
    confidence evidence.confidence_band NOT NULL DEFAULT 'unknown',
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(area_id, dataset_version_id, metric_code, method_code, method_version)
);
CREATE INDEX IF NOT EXISTS area_metrics_area_idx ON geo.area_metrics (area_id, metric_code);

CREATE TABLE IF NOT EXISTS evidence.observations (
    evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    dataset_version_id uuid REFERENCES source.dataset_versions(dataset_version_id),
    ingest_run_id uuid REFERENCES source.ingest_runs(ingest_run_id),
    evidence_type text NOT NULL,
    domain text NOT NULL,
    observation text NOT NULL,
    observed_value jsonb NOT NULL DEFAULT '{}'::jsonb,
    method_code text NOT NULL,
    method_version text NOT NULL,
    authority_level evidence.authority_level NOT NULL DEFAULT 'unknown',
    confidence evidence.confidence_band NOT NULL DEFAULT 'unknown',
    source_date date,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    caveat text,
    is_negative_evidence boolean NOT NULL DEFAULT false,
    is_source_failure boolean NOT NULL DEFAULT false,
    geometry geometry(Geometry, 4326),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS observations_area_idx ON evidence.observations (area_id);
CREATE INDEX IF NOT EXISTS observations_domain_idx ON evidence.observations (domain);
CREATE INDEX IF NOT EXISTS observations_geom_gix ON evidence.observations USING gist (geometry);
CREATE INDEX IF NOT EXISTS observations_json_gin ON evidence.observations USING gin (observed_value);

CREATE TABLE IF NOT EXISTS evidence.contradiction_groups (
    contradiction_group_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    domain text NOT NULL,
    summary text NOT NULL,
    status text NOT NULL DEFAULT 'open',
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    resolution_note text
);

CREATE TABLE IF NOT EXISTS evidence.contradiction_members (
    contradiction_group_id uuid NOT NULL REFERENCES evidence.contradiction_groups(contradiction_group_id),
    evidence_id uuid NOT NULL REFERENCES evidence.observations(evidence_id),
    role text NOT NULL DEFAULT 'conflicting',
    PRIMARY KEY (contradiction_group_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS rules.rule_sets (
    rule_set_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id uuid REFERENCES core.intents(intent_id),
    name text NOT NULL,
    description text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rules.rule_versions (
    rule_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id uuid NOT NULL REFERENCES rules.rule_sets(rule_set_id),
    version_label text NOT NULL,
    ruleset_body jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES core.users(user_id),
    UNIQUE(rule_set_id, version_label)
);

CREATE TABLE IF NOT EXISTS rules.rule_execution_runs (
    rule_execution_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    rule_version_id uuid NOT NULL REFERENCES rules.rule_versions(rule_version_id),
    report_run_id uuid,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status jobs.job_status NOT NULL DEFAULT 'queued',
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS claims.claims (
    claim_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    rule_execution_run_id uuid REFERENCES rules.rule_execution_runs(rule_execution_run_id),
    intent_id uuid REFERENCES core.intents(intent_id),
    claim_code text NOT NULL,
    domain text NOT NULL,
    assertion text NOT NULL,
    severity claims.severity_band NOT NULL DEFAULT 'unknown',
    confidence evidence.confidence_band NOT NULL DEFAULT 'unknown',
    user_safe_language text NOT NULL,
    verification_required boolean NOT NULL DEFAULT false,
    verification_task text,
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS claims_area_idx ON claims.claims (area_id);
CREATE INDEX IF NOT EXISTS claims_code_idx ON claims.claims (claim_code);

CREATE TABLE IF NOT EXISTS claims.claim_evidence (
    claim_id uuid NOT NULL REFERENCES claims.claims(claim_id) ON DELETE CASCADE,
    evidence_id uuid NOT NULL REFERENCES evidence.observations(evidence_id),
    support_role text NOT NULL DEFAULT 'supports',
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS claims.verification_tasks (
    verification_task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    claim_id uuid REFERENCES claims.claims(claim_id),
    task_code text NOT NULL,
    task_text text NOT NULL,
    responsible_party text,
    priority claims.severity_band NOT NULL DEFAULT 'medium',
    status text NOT NULL DEFAULT 'open',
    due_at timestamptz,
    completed_at timestamptz,
    completion_note text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports.report_runs (
    report_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid REFERENCES core.workspaces(workspace_id),
    area_id uuid NOT NULL REFERENCES core.areas(area_id),
    intent_id uuid REFERENCES core.intents(intent_id),
    intent_version_id uuid REFERENCES core.intent_versions(intent_version_id),
    rule_version_id uuid REFERENCES rules.rule_versions(rule_version_id),
    requested_by uuid REFERENCES core.users(user_id),
    status jobs.job_status NOT NULL DEFAULT 'queued',
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    output_uri text,
    machine_json_uri text,
    source_manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
    assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
    caveats jsonb NOT NULL DEFAULT '[]'::jsonb,
    cost_metrics jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE rules.rule_execution_runs
    ADD CONSTRAINT rule_execution_report_fk
    FOREIGN KEY (report_run_id) REFERENCES reports.report_runs(report_run_id);

CREATE TABLE IF NOT EXISTS reports.report_sections (
    report_section_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_run_id uuid NOT NULL REFERENCES reports.report_runs(report_run_id) ON DELETE CASCADE,
    section_code text NOT NULL,
    title text NOT NULL,
    section_order integer NOT NULL,
    body_markdown text NOT NULL,
    evidence_ids uuid[] NOT NULL DEFAULT '{}',
    claim_ids uuid[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(report_run_id, section_code)
);

CREATE TABLE IF NOT EXISTS reports.report_assets (
    report_asset_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_run_id uuid NOT NULL REFERENCES reports.report_runs(report_run_id) ON DELETE CASCADE,
    asset_type text NOT NULL,
    storage_uri text NOT NULL,
    checksum text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS jobs.job_queue (
    job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid REFERENCES core.workspaces(workspace_id),
    job_type text NOT NULL,
    status jobs.job_status NOT NULL DEFAULT 'queued',
    priority integer NOT NULL DEFAULT 100,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key text,
    attempts integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL DEFAULT 3,
    not_before timestamptz NOT NULL DEFAULT now(),
    locked_by text,
    locked_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(idempotency_key)
);
CREATE INDEX IF NOT EXISTS job_queue_status_idx ON jobs.job_queue (status, priority, not_before);

CREATE TABLE IF NOT EXISTS audit.events (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid REFERENCES core.workspaces(workspace_id),
    actor_user_id uuid REFERENCES core.users(user_id),
    event_type text NOT NULL,
    target_table text,
    target_id uuid,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    ip_address inet,
    user_agent text,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS audit_events_workspace_idx ON audit.events (workspace_id, occurred_at DESC);

COMMIT;

INSERT INTO core.intents(intent_code, name, description)
VALUES
('rural_land_purchase', 'Rural land purchase', 'Screen a parcel or area before purchase for buildability, access, hazards, water, zoning, and market context.'),
('homestead_feasibility', 'Homestead feasibility', 'Screen whether available evidence suggests a parcel could plausibly support residence, water, septic, access, and basic rural living requirements.')
ON CONFLICT (intent_code) DO NOTHING;
