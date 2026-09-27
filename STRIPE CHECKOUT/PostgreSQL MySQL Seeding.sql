-- PostgreSQL Schema
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tier VARCHAR(50),
    license_type VARCHAR(100),
    support_level VARCHAR(100),
    seats VARCHAR(50),
    file_cap VARCHAR(50),
    export_control_required BOOLEAN DEFAULT false,
    authorization_attestation_required BOOLEAN DEFAULT false,
    api_access BOOLEAN DEFAULT false,
    sso_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prices (
    id VARCHAR(50) PRIMARY KEY,
    product_id VARCHAR(50) REFERENCES products(id),
    amount INTEGER, -- in cents
    currency VARCHAR(3) DEFAULT 'usd',
    type VARCHAR(50), -- one_time, recurring, quote_only
    interval_period VARCHAR(50), -- month, year, null
    trial_days INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_features (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) REFERENCES products(id),
    feature TEXT NOT NULL
);

-- Insert Products
INSERT INTO products (id, name, description, tier, license_type, support_level, seats, file_cap, export_control_required, authorization_attestation_required, api_access, sso_enabled) VALUES
('prod_community', 'Arcana Forensics — Community', 'Open-source digital forensics acquisition and custody management. Air-gapped filesystem acquisition, AES-256-GCM vault isolation, SHA-256 hash-chained custody ledger. Written in Rust. MIT License. No telemetry.', 'community', 'open_source', 'github_issues', 'unlimited', 'none', false, false, false, false),
('prod_professional', 'Arcana Forensics — Professional', 'Commercial forensic acquisition platform for solo practitioners and boutique firms. Professional-grade cryptographic custody with priority support. Annual subscription. Authorization attestation required.', 'professional', 'commercial_subscription', 'email_48h_sla', '1', 'none', true, true, false, false),
('prod_enterprise', 'Arcana Forensics — Enterprise', 'Scalable forensic acquisition infrastructure for law firms, corporate security, and incident response. Multi-seat deployment with API access. Annual subscription.', 'enterprise', 'enterprise_agreement', 'priority_24h_sla', 'unlimited', 'none', true, true, true, true),
('prod_government', 'Arcana Forensics — Federal/Government', 'Hardened forensic acquisition for law enforcement, intelligence, and military. Air-gapped deployment, FIPS compliance consultation. Custom quote only. US Government only.', 'government', 'federal_contract', '24_7_hotline', 'negotiated', 'none', true, true, false, false);

-- Insert Prices
INSERT INTO prices (id, product_id, amount, currency, type, interval_period, trial_days) VALUES
('price_community_free', 'prod_community', 0, 'usd', 'one_time', NULL, NULL),
('price_prof_annual', 'prod_professional', 350000, 'usd', 'recurring', 'year', 14),
('price_ent_annual', 'prod_enterprise', 3500000, 'usd', 'recurring', 'year', NULL),
('price_gov_custom', 'prod_government', 0, 'usd', 'quote_only', NULL, NULL);

-- Insert Features (Community)
INSERT INTO product_features (product_id, feature) VALUES
('prod_community', 'Full source code access'),
('prod_community', 'Community support via GitHub'),
('prod_community', 'Complete documentation'),
('prod_community', 'Unlimited cases'),
('prod_community', 'No file caps'),
('prod_community', 'Air-gapped operation'),
('prod_community', 'AES-256-GCM encryption'),
('prod_community', 'SHA-256 custody chain');

-- Insert Features (Professional)
INSERT INTO product_features (product_id, feature) VALUES
('prod_professional', 'Unlimited cases'),
('prod_professional', 'No file caps'),
('prod_professional', 'Priority email support (48-hour SLA)'),
('prod_professional', 'Single seat license'),
('prod_professional', 'Multiple workstation activation'),
('prod_professional', 'Chain-of-custody documentation templates'),
('prod_professional', 'Daubert-ready technical specifications'),
('prod_professional', 'Quarterly security updates');

-- Insert Features (Enterprise)
INSERT INTO product_features (product_id, feature) VALUES
('prod_enterprise', 'Unlimited seats organization-wide'),
('prod_enterprise', 'REST API access'),
('prod_enterprise', 'Custom custody schema development'),
('prod_enterprise', 'Priority support (24-hour SLA)'),
('prod_enterprise', 'SAML 2.0 / OIDC SSO integration'),
('prod_enterprise', 'Multi-tenant case management'),
('prod_enterprise', 'Automated custody report generation'),
('prod_enterprise', 'Integration with Relativity, Nuix, Autopsy'),
('prod_enterprise', 'White-label reporting options'),
('prod_enterprise', 'Dedicated account manager'),
('prod_enterprise', 'Annual security assessment included');

-- Insert Features (Government)
INSERT INTO product_features (product_id, feature) VALUES
('prod_government', 'Perpetual license option available'),
('prod_government', 'On-site installation and configuration'),
('prod_government', 'Customized training programs'),
('prod_government', 'FedRAMP compliance consultation'),
('prod_government', 'CJIS compliance consultation'),
('prod_government', 'State Department ITAR compliance'),
('prod_government', 'Classified environment deployment support'),
('prod_government', 'Source code escrow available'),
('prod_government', 'Liability indemnification (negotiated)'),
('prod_government', '24/7 emergency support hotline');