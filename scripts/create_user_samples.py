#!/usr/bin/env python3
"""
Create user-friendly sample files from demo samples
"""

import shutil
from pathlib import Path

def create_user_samples():
    """Copy demo samples to user samples directory with friendly names"""
    print("Creating user sample files...\n")
    
    base_dir = Path(__file__).parent.parent
    demo_samples = base_dir / "demo_samples"
    user_samples = base_dir / "samples_for_users"
    
    # Ensure user samples directory exists
    user_samples.mkdir(exist_ok=True)
    
    # File mappings: demo_file -> user_file
    file_mappings = {
        "corporate_phishing.eml": "corporate_benefits_scam.eml",
        "paypal_scam.eml": "paypal_security_alert.eml", 
        "amazon_fraud.eml": "amazon_delivery_issue.eml",
        "microsoft_account_scam.eml": "microsoft_security_warning.eml",
        "crypto_wallet_scam.eml": "crypto_wallet_breach.eml",
        "irs_tax_scam.eml": "irs_refund_notice.eml",
        "fake_invoice_scam.eml": "quickbooks_overdue_invoice.eml",
        "romance_scam.eml": "dating_site_message.eml"
    }
    
    copied_count = 0
    
    for demo_file, user_file in file_mappings.items():
        demo_path = demo_samples / demo_file
        user_path = user_samples / user_file
        
        if demo_path.exists():
            shutil.copy2(demo_path, user_path)
            print(f"Created: {user_file}")
            copied_count += 1
        else:
            print(f"Missing: {demo_file}")
    
    print(f"\nSuccessfully created {copied_count} user sample files!")
    print(f"Location: {user_samples}")
    print("\nUsers can now download these files to test the phishing detector.")
    
    return copied_count

if __name__ == "__main__":
    create_user_samples()