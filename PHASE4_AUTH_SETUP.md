# Phase 4: Authentication System - Setup Guide

## Overview

Phase 4 implements JWT-based authentication for the SNMP Monitoring System. This guide will help you deploy and configure the authentication system.

## Features Implemented

### Backend
- ✅ JWT token-based authentication (24-hour expiration)
- ✅ Bcrypt password hashing
- ✅ User model with admin role support
- ✅ Login endpoint (`POST /auth/login`)
- ✅ User info endpoint (`GET /auth/me`)
- ✅ Change password endpoint (`PUT /auth/me/password`)
- ✅ Change email endpoint (`PUT /auth/me/email`)
- ✅ Protected API routes (all endpoints require authentication)
- ✅ Admin email linked to alert recipients

### Frontend
- ✅ Login page with form validation
- ✅ JWT token storage and management
- ✅ Automatic token injection in API requests
- ✅ User profile dropdown in navbar
- ✅ Profile settings page (change password/email)
- ✅ Automatic logout on 401 errors
- ✅ Route protection (redirects to login)

---

## Deployment Steps

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added:**
- `python-jose[cryptography]==3.3.0` - JWT token handling
- `passlib[bcrypt]==1.7.4` - Password hashing
- `python-multipart==0.0.6` - Form data parsing

### Step 2: Run Admin Setup Script

⚠️ **IMPORTANT:** Run this script **BEFORE** starting the application for the first time.

```bash
cd /home/user/SNMP-Monitoring
python3 scripts/setup_admin.py
```

The script will prompt you for:
1. **Username** - Admin username (3-50 characters, alphanumeric + underscore/hyphen)
2. **Password** - Admin password (minimum 6 characters, recommended: letters + numbers)
3. **Email** - Admin email for alert notifications

**Example:**
```
🔐 SNMP Monitoring System - Admin Setup
═══════════════════════════════════════

Enter admin username: admin
Enter admin password: ********
Confirm password: ********
Enter admin email (for alerts): admin@example.com

✅ Admin user 'admin' created successfully
✅ Email 'admin@example.com' added as alert recipient
```

### Step 3: Start the Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The database will be automatically created with the User table.

### Step 4: Start the Frontend

```bash
cd frontend
npm install  # if not already done
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Step 5: Login

1. Navigate to `http://localhost:3000`
2. You'll be automatically redirected to `/login`
3. Enter your admin credentials
4. Upon successful login, you'll be redirected to the dashboard

---

## API Endpoints

### Authentication Endpoints

#### 1. Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2. Get Current User Info
```http
GET /auth/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_admin": true,
  "is_active": true
}
```

#### 3. Change Password
```http
PUT /auth/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}

Response:
{
  "message": "Password changed successfully"
}
```

#### 4. Change Email
```http
PUT /auth/me/email
Authorization: Bearer <token>
Content-Type: application/json

{
  "new_email": "newemail@example.com",
  "password": "current_password"
}

Response:
{
  "message": "Email changed successfully and alert recipient updated"
}
```

**Note:** If the user is an admin, changing email will also update the alert recipient email.

---

## Frontend Usage

### Login Flow

1. User visits any protected route → redirected to `/login`
2. User enters credentials
3. On success:
   - JWT token stored in `localStorage`
   - User info cached
   - Redirected to `/dashboard`
4. On failure:
   - Error message displayed
   - User remains on login page

### Token Management

- **Storage:** JWT token stored in `localStorage` as `snmp_auth_token`
- **Injection:** Automatically injected in all API requests via axios interceptor
- **Expiration:** Tokens expire after 24 hours
- **Invalidation:** On 401 error, token is cleared and user redirected to login

### User Profile

1. Click username dropdown in navbar (top-right)
2. View current username and email
3. Click "Profile Settings" to change password/email
4. Click "Logout" to sign out

### Profile Settings Page

Located at `/settings/profile`, allows:

- **View account info:** Username, email, role
- **Change password:**
  - Requires current password
  - New password must be 6+ characters
  - Must be different from current password
- **Change email:**
  - Requires password verification
  - Must be valid email format
  - Must be different from current email
  - **Admin users:** Alert recipient email is automatically updated

---

## Security Configuration

### JWT Secret Key

⚠️ **IMPORTANT:** Change the JWT secret key in production!

**File:** `backend/app/core/security.py`

```python
# Current (INSECURE for production):
SECRET_KEY = "snmp-monitoring-secret-key-change-in-production"

# Production (use strong random key):
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-very-long-random-secret-key")
```

**Generate a secure secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Token Expiration

Default: **24 hours**

To change:
```python
# File: backend/app/core/security.py
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Change this value
```

### Password Requirements

Current minimum: **6 characters**

To enforce stronger passwords, update validation in:
- `backend/app/api/v1/endpoints/auth.py` (Pydantic validators)
- `scripts/setup_admin.py` (validation function)

---

## Protected Routes

All API endpoints (except `/auth/*`) now require authentication:

- ✅ `/device/*` - All device management endpoints
- ✅ `/query/*` - All query endpoints
- ✅ `/recipients/*` - Alert recipient management
- ✅ `/polling/*` - Manual polling trigger

**No authentication required:**
- ❌ `/auth/login` - Login endpoint
- ❌ `/docs` - OpenAPI documentation (if enabled)

---

## Troubleshooting

### Issue: Cannot login after setup

**Solution:**
1. Check if admin user exists:
   ```bash
   sqlite3 backend/snmp_monitor.db
   SELECT * FROM users;
   ```
2. If no users exist, run setup script again:
   ```bash
   python3 scripts/setup_admin.py
   ```

### Issue: "Could not validate credentials" error

**Possible causes:**
1. Token expired (24 hours)
   - **Solution:** Login again
2. Token invalid or corrupted
   - **Solution:** Clear localStorage and login again
   ```javascript
   localStorage.clear();
   ```
3. Secret key changed on backend
   - **Solution:** All users must login again

### Issue: Frontend shows "Network Error"

**Possible causes:**
1. Backend not running
   - **Solution:** Start backend: `uvicorn main:app`
2. CORS issues
   - **Solution:** Check `app/api/middleware.py` CORS settings
3. Wrong API URL
   - **Solution:** Check `NEXT_PUBLIC_API_URL` in frontend `.env`

### Issue: "Email already in use" when changing email

**Cause:** Another user has this email

**Solution:** Choose a different email address

---

## Database Schema

### User Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
- `username` - Unique index for fast lookups
- `email` - Unique index for fast lookups

---

## Advanced Configuration

### Multiple Admin Users

To create additional admin users:

```bash
python3 scripts/setup_admin.py
```

The script will detect existing users and ask for confirmation.

### Disable a User (Database)

```bash
sqlite3 backend/snmp_monitor.db
UPDATE users SET is_active = 0 WHERE username = 'username';
```

### Reset Admin Password (Database)

1. Generate new password hash:
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   print(pwd_context.hash("new_password"))
   ```

2. Update database:
   ```bash
   sqlite3 backend/snmp_monitor.db
   UPDATE users SET hashed_password = '<hash_from_step1>' WHERE username = 'admin';
   ```

---

## Migration from No-Auth System

If you have an existing deployment without authentication:

1. **Backup your database:**
   ```bash
   cp backend/snmp_monitor.db backend/snmp_monitor.db.backup
   ```

2. **Pull Phase 4 changes:**
   ```bash
   git pull origin <branch>
   ```

3. **Install new dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run setup script:**
   ```bash
   python3 scripts/setup_admin.py
   ```

5. **Restart backend:**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Clear frontend cache:**
   - In browser: Open DevTools → Application → Clear Storage → Clear site data

7. **Login** with your new admin credentials

---

## Testing Checklist

- [ ] Admin user creation via setup script
- [ ] Login with correct credentials
- [ ] Login fails with wrong credentials
- [ ] Dashboard loads after login
- [ ] User info displayed in navbar
- [ ] Logout redirects to login page
- [ ] Accessing protected routes without token redirects to login
- [ ] Change password in profile settings
- [ ] Change email in profile settings
- [ ] Admin email change updates alert recipient
- [ ] Token expires after 24 hours (optional: wait)
- [ ] API requests include Authorization header
- [ ] 401 errors clear token and redirect to login

---

## Next Steps

After successful authentication deployment:

1. **Change JWT Secret Key** (production)
2. **Configure HTTPS** for secure token transmission
3. **Set up environment variables** for secrets
4. **Enable rate limiting** to prevent brute force attacks
5. **Implement session management** (optional)
6. **Add audit logging** for security events (optional)
7. **Configure password reset** via email (optional)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs: `backend/logs/`
3. Check browser console for frontend errors
4. Verify database state: `sqlite3 backend/snmp_monitor.db`

---

**Phase 4 Complete! 🎉**

Your SNMP Monitoring System is now secured with JWT authentication.
