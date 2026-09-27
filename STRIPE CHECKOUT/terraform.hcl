# variables.tf
variable "stripe_api_key" {
  type        = string
  sensitive   = true
  description = "Stripe API key for product provisioning"
}

# products.tf
terraform {
  required_providers {
    stripe = {
      source  = "franckverrot/stripe"
      version = "~> 1.0"
    }
  }
}

provider "stripe" {
  api_key = var.stripe_api_key
}

# Community Product (Free)
resource "stripe_product" "community" {
  name        = "Arcana Forensics — Community"
  description = "Open-source digital forensics acquisition. MIT License. No telemetry."
  metadata = {
    tier                              = "community"
    license_type                      = "open_source"
    support_level                     = "github_issues"
    seats                             = "unlimited"
    export_control_required           = "false"
    authorization_attestation_required = "false"
  }
}

resource "stripe_price" "community_free" {
  product     = stripe_product.community.id
  unit_amount = 0
  currency    = "usd"
  type        = "one_time"
  
  metadata = {
    delivery_method      = "direct_download"
    license_key_required = "false"
  }
}

# Professional Product
resource "stripe_product" "professional" {
  name        = "Arcana Forensics — Professional"
  description = "Commercial forensic acquisition for solo practitioners. Annual subscription."
  metadata = {
    tier                               = "professional"
    license_type                       = "commercial_subscription"
    support_level                      = "email_48h_sla"
    seats                              = "1"
    export_control_required            = "true"
    authorization_attestation_required = "true"
  }
}

resource "stripe_price" "professional_annual" {
  product     = stripe_product.professional.id
  unit_amount = 350000
  currency    = "usd"
  type        = "recurring"
  
  recurring {
    interval       = "year"
    interval_count = 1
  }
  
  metadata = {
    trial_days      = "14"
    cancellation_policy = "end_of_period"
  }
}

# Enterprise Product
resource "stripe_product" "enterprise" {
  name        = "Arcana Forensics — Enterprise"
  description = "Scalable forensic infrastructure for law firms and corporate security."
  metadata = {
    tier                               = "enterprise"
    license_type                       = "enterprise_agreement"
    support_level                      = "priority_24h_sla"
    seats                              = "unlimited"
    export_control_required            = "true"
    authorization_attestation_required = "true"
    api_access                         = "true"
    sso_enabled                        = "true"
  }
}

resource "stripe_price" "enterprise_annual" {
  product     = stripe_product.enterprise.id
  unit_amount = 3500000
  currency    = "usd"
  type        = "recurring"
  
  recurring {
    interval       = "year"
    interval_count = 1
  }
  
  metadata = {
    onboarding_included         = "4_hour_virtual"
    dedicated_account_manager   = "true"
    annual_security_assessment  = "true"
  }
}

# Government Product (Quote-only)
resource "stripe_product" "government" {
  name        = "Arcana Forensics — Federal/Government"
  description = "Hardened forensic acquisition for law enforcement and military. Custom quote only."
  metadata = {
    tier                    = "government"
    license_type            = "federal_contract"
    support_level           = "24_7_hotline"
    seats                   = "negotiated"
    export_control_required = "true"
    us_government_only      = "true"
    fips_compliance         = "consultation_included"
    classified_deployment   = "supported"
  }
}

# Outputs
output "community_product_id" {
  value = stripe_product.community.id
}

output "professional_price_id" {
  value = stripe_price.professional_annual.id
}

output "enterprise_price_id" {
  value = stripe_price.enterprise_annual.id
}