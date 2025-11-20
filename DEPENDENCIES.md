# SNMP Monitoring System - Dependencies Documentation

## Overview
This document lists all dependencies for both backend and frontend, including their purpose and version requirements.

---

## Backend Dependencies

### Core Web Framework
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.104.0 | Modern async web framework for building APIs |
| `uvicorn[standard]` | >=0.24.0 | ASGI server for running FastAPI applications |
| `httpx` | >=0.26.0 | HTTP client for async requests (used for frontend communication) |

### Database & ORM
| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | >=2.0.0 | SQL toolkit and ORM for database operations |

### Data Validation & Configuration
| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >=2.0.0 | Data validation using Python type annotations |
| `pydantic-settings` | >=2.0.0 | Settings management with environment variables |
| `python-dotenv` | >=1.0.0 | Load environment variables from .env files |

### Network & SNMP
| Package | Version | Purpose |
|---------|---------|---------|
| `pysnmp` | >=4.4.12 | SNMP library for device monitoring and discovery |

### Caching
| Package | Version | Purpose |
|---------|---------|---------|
| `redis` | >=5.0.1 | Redis client for caching API responses and improving performance |

### Authentication & Security
| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | >=3.3.0 | JWT token creation and verification |
| `passlib[bcrypt]` | >=1.7.4 | Password hashing with bcrypt |
| `python-multipart` | >=0.0.6 | Multipart form data parsing |

### Email
Email functionality uses Python's built-in modules:
- `smtplib` - SMTP protocol client (built-in)
- `email.mime` - Email message construction (built-in)

No additional packages required for email alerts.

### Standard Library (Built-in)
The following are used from Python's standard library (no installation needed):
- `asyncio` - Async I/O operations
- `datetime` - Date and time handling
- `json` - JSON encoding/decoding
- `logging` - Logging functionality
- `pathlib` - Object-oriented filesystem paths
- `sys` - System-specific parameters
- `threading` - Thread-based parallelism
- `time` - Time access and conversions
- `typing` - Type hints
- `uuid` - UUID generation
- `ipaddress` - IP address manipulation
- `functools` - Higher-order functions
- `contextlib` - Context management utilities

---

## Frontend Dependencies

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| `next` | ^14.2.33 | React framework with server-side rendering |
| `react` | ^18.2.0 | JavaScript library for building user interfaces |
| `react-dom` | ^18.2.0 | React DOM rendering |
| `typescript` | ^5 | TypeScript language for type safety |

### UI Components & Styling
| Package | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/react-dialog` | ^1.0.5 | Accessible dialog component |
| `@radix-ui/react-dropdown-menu` | ^2.1.16 | Dropdown menu component |
| `@radix-ui/react-label` | ^2.1.8 | Label component |
| `@radix-ui/react-select` | ^2.0.0 | Select input component |
| `@radix-ui/react-separator` | ^1.1.8 | Visual separator component |
| `@radix-ui/react-slot` | ^1.0.2 | Slot component for composition |
| `@radix-ui/react-tabs` | ^1.0.4 | Tabs component |
| `@radix-ui/react-toast` | ^1.1.5 | Toast notification component |
| `lucide-react` | ^0.323.0 | Icon library |
| `tailwindcss` | ^3.4.1 | Utility-first CSS framework |
| `tailwindcss-animate` | ^1.0.7 | Animation utilities for Tailwind |
| `class-variance-authority` | ^0.7.1 | CSS class variance utility |
| `clsx` | ^2.1.0 | Utility for constructing className strings |
| `tailwind-merge` | ^2.2.1 | Merge Tailwind CSS classes |

### Data Fetching & State Management
| Package | Version | Purpose |
|---------|---------|---------|
| `@tanstack/react-query` | ^5.17.19 | Data fetching and caching library |
| `@tanstack/react-table` | ^8.11.7 | Headless table library for React |
| `axios` | ^1.6.7 | Promise-based HTTP client |

### Forms & Validation
| Package | Version | Purpose |
|---------|---------|---------|
| `react-hook-form` | ^7.49.3 | Form state management and validation |
| `zod` | ^3.22.4 | TypeScript-first schema validation |

### Charts & Visualization
| Package | Version | Purpose |
|---------|---------|---------|
| `recharts` | ^2.12.0 | Composable charting library for React |

### Utilities
| Package | Version | Purpose |
|---------|---------|---------|
| `date-fns` | ^3.3.1 | Modern date utility library |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `@types/node` | ^20 | TypeScript definitions for Node.js |
| `@types/react` | ^18 | TypeScript definitions for React |
| `@types/react-dom` | ^18 | TypeScript definitions for React DOM |
| `autoprefixer` | ^10.4.17 | PostCSS plugin for vendor prefixes |
| `eslint` | ^9.39.1 | JavaScript/TypeScript linter |
| `@eslint/js` | ^9.39.1 | ESLint JavaScript configurations |
| `eslint-config-next` | ^14.2.33 | ESLint configuration for Next.js |
| `postcss` | ^8 | CSS transformation tool |

---

## Installation

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
```

### Using Setup Script (Recommended)
```bash
./setup.sh
```
This will automatically install all dependencies for both backend and frontend.

---

## Version Compatibility

### Backend
- **Python**: 3.12 or higher required
- **Redis**: 5.0 or higher (optional but recommended)

### Frontend
- **Node.js**: 18.0 or higher required
- **npm**: 9.0 or higher recommended

---

## Optional Dependencies

### Redis
Redis is optional but highly recommended for production environments:
- **Purpose**: Caches API responses to reduce database queries and improve performance
- **Impact without Redis**: System will work but with reduced performance
- **Automated Installation**: The `./setup.sh` wizard will automatically install and start Redis if you choose to enable caching
- **Manual Installation**: You can also install Redis separately (see instructions below)

#### Manual Redis Installation (if not using setup.sh)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# RedHat/CentOS
sudo yum install redis
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

### Gmail App Password
For email alerts to work with Gmail:
- **Requirement**: App-specific password (not regular Gmail password)
- **Setup**: https://myaccount.google.com/apppasswords
- **Configuration**: Set in `SENDER_PASSWORD` environment variable

---

## Security Notes

1. **JWT Secret Key**: Auto-generated during setup using OpenSSL (`openssl rand -hex 32`)
2. **Password Hashing**: Uses bcrypt via passlib
3. **Email Credentials**: Stored in .env file (never commit to version control)
4. **HTTPS**: Recommended for production deployments (see nginx configuration in DEPLOYMENT.md)

---

## Updating Dependencies

### Backend
```bash
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Frontend
```bash
cd frontend
npm update
```

### Check for Outdated Packages
```bash
# Backend
pip list --outdated

# Frontend
npm outdated
```

---

## Troubleshooting

### Backend Issues

**Problem**: `pip install` fails for pysnmp
```bash
# Solution: Install system dependencies first (Ubuntu/Debian)
sudo apt-get install python3-dev libssl-dev
```

**Problem**: Redis connection errors
```bash
# Solution: Ensure Redis is running
sudo systemctl status redis-server
# or
redis-cli ping  # Should return PONG
```

### Frontend Issues

**Problem**: Peer dependency conflicts
```bash
# Solution: Use --legacy-peer-deps flag
npm install --legacy-peer-deps
```

**Problem**: TypeScript errors after update
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

---

## Validation

After installation, validate your setup:

```bash
# Check all dependencies
./scripts/validate-setup.sh

# or use Makefile
make validate
```

---

## Last Updated
This document reflects the dependencies as of the streamlined setup implementation (2025).

For the latest requirements, always refer to:
- Backend: `backend/requirements.txt`
- Frontend: `frontend/package.json`
