// crates/arcana-sanitize/src/lib.rs
pub mod traits;
pub mod software;      // Always included
pub mod hardware;      // cfg(feature = "enterprise-scif")

pub struct SanitizationEngine {
    software_checks: Vec<Box<dyn SoftwareCheck>>,
    #[cfg(feature = "enterprise-scif")]
    hardware_checks: Vec<Box<dyn HardwareCheck>>,
}

impl SanitizationEngine {
    pub fn verify(&self) -> Result<SanitizationCert, SanitizationError> {
        // Layer 1-5: Software (always run)
        for check in &self.software_checks {
            check.verify()?;
        }
        
        // Layer 6+: Hardware (only if feature enabled)
        #[cfg(feature = "enterprise-scif")]
        for check in &self.hardware_checks {
            check.verify()?; // Requires human confirmation
        }
        
        Ok(SanitizationCert::new())
    }
}
