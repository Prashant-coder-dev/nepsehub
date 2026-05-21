"""
Authentication utility functions
- Password hashing
- JWT token generation
- Email sending
"""

import bcrypt
import jwt
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import random
from datetime import datetime, timedelta

JWT_SECRET = os.getenv('JWT_SECRET')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# ─────────────────────────────────────────────
# PASSWORD FUNCTIONS
# ─────────────────────────────────────────────

def generate_password(length=12):
    """Generate random secure password"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password):
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hash_value):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))

# ─────────────────────────────────────────────
# JWT FUNCTIONS
# ─────────────────────────────────────────────

def generate_token(user, expires_in='1h'):
    """Generate JWT token"""
    if expires_in == '1h':
        exp = datetime.utcnow() + timedelta(hours=1)
    elif expires_in == '7d':
        exp = datetime.utcnow() + timedelta(days=7)
    else:
        exp = datetime.utcnow() + timedelta(hours=1)
    
    payload = {
        'id': str(user['id']),
        'email': user['email'],
        'name': user['name'],
        'exp': exp,
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ─────────────────────────────────────────────
# EMAIL FUNCTIONS
# ─────────────────────────────────────────────

def send_email(to_email, subject, html_body):
    """Send email via Gmail SMTP"""
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = GMAIL_USER
        message['To'] = to_email
        
        part = MIMEText(html_body, 'html')
        message.attach(part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())
        
        return True
    except Exception as e:
        print(f'Email error: {str(e)}')
        return False

def send_signup_email(email, password):
    """Send signup credentials email"""
    subject = 'NEPSE HUB - Your Login Credentials'
    html = f"""
    <h2>Welcome to NEPSE HUB!</h2>
    <p>Your account has been created successfully.</p>
    <p><strong>Your Login Credentials:</strong></p>
    <ul>
        <li><strong>Email:</strong> {email}</li>
        <li><strong>Password:</strong> <code>{password}</code></li>
    </ul>
    <p><a href="https://nepse-hub.vercel.app/pages/login.html">Click here to login</a></p>
    <p><strong>⚠️ Important:</strong> Please change your password after first login.</p>
    """
    return send_email(email, subject, html)

def send_reset_email(email, temp_password):
    """Send password reset email"""
    subject = 'NEPSE HUB - Password Reset'
    html = f"""
    <h2>Password Reset Request</h2>
    <p>Your temporary password is:</p>
    <p><code style="background: #f0f0f0; padding: 10px; border-radius: 5px;">{temp_password}</code></p>
    <p><a href="https://nepse-hub.vercel.app/pages/login.html">Click here to login</a></p>
    <p><strong>⚠️ Important:</strong> Please change your password after login.</p>
    """
    return send_email(email, subject, html)
