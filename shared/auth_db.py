from supabase import create_client
import os

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Global placeholder for lazy initialization
supabase_client = None

def get_supabase():
    """Lazily initialize Supabase client to prevent startup crashes when credentials are not configured."""
    global supabase_client
    if supabase_client is not None:
        return supabase_client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase environment variables (SUPABASE_URL and SUPABASE_KEY) are not configured.")
    
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase_client

# ─────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────

def user_exists(email):
    """Check if user with email exists"""
    try:
        response = get_supabase().table('users').select('id').eq('email', email).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f'Database error: {str(e)}')
        return False

def create_user(email, name, password_hash):
    """Create new user"""
    try:
        response = get_supabase().table('users').insert({
            'email': email,
            'name': name,
            'password_hash': password_hash
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f'Create user error: {str(e)}')
        return None

def get_user_by_email(email):
    """Get user by email"""
    try:
        response = get_supabase().table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f'Get user error: {str(e)}')
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        response = get_supabase().table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f'Get user error: {str(e)}')
        return None

def update_user_password(user_id, password_hash):
    """Update user password"""
    try:
        response = get_supabase().table('users').update({
            'password_hash': password_hash
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f'Update password error: {str(e)}')
        return False
