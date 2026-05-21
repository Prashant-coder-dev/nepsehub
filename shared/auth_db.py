"""
Supabase database connection and queries
"""

from supabase import create_client
import os

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────

def user_exists(email):
    """Check if user with email exists"""
    try:
        response = supabase.table('users').select('id').eq('email', email).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f'Database error: {str(e)}')
        return False

def create_user(email, name, password_hash):
    """Create new user"""
    try:
        response = supabase.table('users').insert({
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
        response = supabase.table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f'Get user error: {str(e)}')
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f'Get user error: {str(e)}')
        return None

def update_user_password(user_id, password_hash):
    """Update user password"""
    try:
        response = supabase.table('users').update({
            'password_hash': password_hash
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f'Update password error: {str(e)}')
        return False
