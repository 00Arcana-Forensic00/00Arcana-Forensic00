// COMMERCIAL TIER STRUCTURE DEFINITIONS
pub struct HostMachine {
    pub id: i32,
    pub computer_name: String,
    pub ip_address: String,
    pub os_type: String,
}

pub struct ForensicArtifact {
    pub id: i32,
    pub host_id: i32,
    pub file_name: String,
    pub file_path: String,
    pub file_size: i64,
    pub true_signature: String,
    pub sha256_hash: String,
    pub dormant_status: bool,
}

// PREMIUM ENTERPRISE EXTENSION: Threat Lineage Tracking Model
pub struct OriginTrace {
    pub id: i32,
    pub artifact_id: i32,
    pub source_zone: Option<String>,
    pub download_url: Option<String>,
    pub source_ip: Option<String>,
    pub referrer_url: Option<String>,
}
