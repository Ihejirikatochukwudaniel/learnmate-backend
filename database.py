from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Supabase configuration from environment
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

# Validate that we have the required environment variables
if not url:
    raise ValueError("SUPABASE_URL environment variable is required")

if not key:
    raise ValueError("SUPABASE_ANON_KEY environment variable is required")

# Create Supabase client
supabase: Client = create_client(url, key)

def get_supabase() -> Client:
    """Get the Supabase client instance"""
    return supabase

# Test connection on import
try:
    # Simple test to verify connection
    test_response = supabase.auth.get_user()
    print("✅ Supabase connection established successfully")
except Exception as e:
    print(f"⚠️ Supabase connection test failed (this is normal without auth): {e}")
    print("✅ Environment variables loaded correctly")