from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import uvicorn

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import auth utilities from shared
try:
    from shared.auth_utils import (
        generate_password, hash_password, verify_password,
        generate_token, verify_token,
        send_signup_email, send_reset_email
    )
    from shared.auth_db import (
        user_exists, create_user, get_user_by_email,
        get_user_by_id, update_user_password
    )
    print("✅ Imported from shared folder")
except ImportError as e:
    print(f"⚠️  Could not import from shared: {e}")
    print("    Make sure auth_utils.py and auth_db.py exist in shared/")
    raise

# Pydantic Models
class SignupRequest(BaseModel):
    email: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refreshToken: str

class ChangePasswordRequest(BaseModel):
    email: str
    currentPassword: str
    newPassword: str

class ForgotPasswordRequest(BaseModel):
    email: str

# FastAPI App
app = FastAPI(title="NEPSE Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# HEALTH & STATUS
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "Auth Service Running",
        "service": "Authentication/User Management",
        "version": "1.0.0",
        "endpoints": {
            "signup": "POST /signup",
            "login": "POST /login",
            "refresh": "POST /refresh",
            "change-password": "POST /change-password",
            "forgot-password": "POST /forgot-password"
        }
    }

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.post("/signup")
def signup(req: SignupRequest):
    """Create new user account with auto-generated password"""
    try:
        email = req.email.strip().lower()
        name = req.name.strip()
        
        if not email or not name:
            raise HTTPException(status_code=400, detail="Email and name are required")
        
        if user_exists(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        password = generate_password()
        password_hash = hash_password(password)
        
        user = create_user(email, name, password_hash)
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        send_signup_email(email, password)
        
        return {
            "message": "Account created! Check your email for login credentials.",
            "user": {"id": user.get('id'), "email": user.get('email'), "name": user.get('name')}
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f'Signup error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(req: LoginRequest):
    """Authenticate user and return JWT tokens"""
    try:
        email = req.email.strip().lower()
        password = req.password
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        user = get_user_by_email(email)
        if not user or not verify_password(password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = generate_token(user, '1h')
        refresh_token = generate_token(user, '7d')
        
        return {
            "token": token,
            "refreshToken": refresh_token,
            "user": {"id": user['id'], "email": user['email'], "name": user['name']}
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f'Login error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
def refresh(req: RefreshRequest):
    """Refresh JWT token"""
    try:
        if not req.refreshToken:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        payload = verify_token(req.refreshToken)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = get_user_by_id(payload['id'])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        new_token = generate_token(user, '1h')
        return {"token": new_token}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Refresh error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/change-password")
def change_password(req: ChangePasswordRequest):
    """Change user password"""
    try:
        email = req.email.strip().lower()
        
        if not email or not req.currentPassword or not req.newPassword:
            raise HTTPException(status_code=400, detail="All fields are required")
        
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not verify_password(req.currentPassword, user['password_hash']):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        new_password_hash = hash_password(req.newPassword)
        if not update_user_password(user['id'], new_password_hash):
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Change password error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """Send password reset email"""
    try:
        email = req.email.strip().lower()
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        user = get_user_by_email(email)
        if not user:
            return {"message": "If account exists, password reset email has been sent"}
        
        temp_password = generate_password()
        temp_password_hash = hash_password(temp_password)
        
        if not update_user_password(user['id'], temp_password_hash):
            raise HTTPException(status_code=500, detail="Failed to process request")
        
        send_reset_email(email, temp_password)
        
        return {"message": "Password reset email sent"}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Forgot password error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005))
    print(f"\n🚀 Auth Service starting on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)