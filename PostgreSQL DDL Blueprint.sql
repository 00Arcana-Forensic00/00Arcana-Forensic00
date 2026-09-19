-- 1. TRACK WORKSTATIONS RUNNING SCAN PIPELINES
CREATE TABLE host_machines (
    id SERIAL PRIMARY KEY,
    computer_name VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NOT NULL,
    os_type VARCHAR(50) NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. MASTER LOG FOR INGESTED FORENSIC ARTIFACTS
CREATE TABLE forensic_artifacts (
    id SERIAL PRIMARY KEY,
    host_id INT REFERENCES host_machines(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    claimed_extension VARCHAR(10) NOT NULL,
    true_signature VARCHAR(50) NOT NULL, -- Extracted via Magic Bytes
    sha256_hash CHAR(64) NOT NULL UNIQUE,
    dormant_status BOOLEAN DEFAULT FALSE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PREMIUM ONLY: ORIGIN SNIFFING AND THREAT LINEAGE METADATA
CREATE TABLE origin_traces (
    id SERIAL PRIMARY KEY,
    artifact_id INT REFERENCES forensic_artifacts(id) ON DELETE CASCADE UNIQUE,
    source_zone VARCHAR(50),               -- e.g., Zone.Identifier: ZoneId=3 (Internet)
    download_url TEXT,                     -- Extracted download source URI
    source_ip VARCHAR(45),                 -- Remote malicious ip address matching
    referrer_url TEXT,                     -- Referring website context
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. DISTRIBUTED IMMUTABLE CUSTODY LOGGING LEDGER
CREATE TABLE custody_ledger (
    id SERIAL PRIMARY KEY,
    artifact_id INT REFERENCES forensic_artifacts(id) ON DELETE CASCADE,
    operator_id VARCHAR(100) NOT NULL,
    action_taken TEXT NOT NULL,           -- e.g., "Isolated and re-encrypted via AES-256-GCM"
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --- High-Speed Performance Optimization Indexes ---
CREATE INDEX idx_artifacts_hash ON forensic_artifacts(sha256_hash);
CREATE INDEX idx_origin_ip ON origin_traces(source_ip);
CREATE INDEX idx_ledger_artifact ON custody_ledger(artifact_id);
