# SNMP Monitoring System - Updated FE/BE Mitigation Plan

## Executive Summary
This updated mitigation plan addresses critical compatibility issues between the Frontend (Next.js) and Backend (FastAPI) components. The plan has been revised to reflect the **current state of the fully-implemented frontend** and prioritizes fixing three critical bugs: threshold updates, performance issues, and error handling.

**Key Changes from Original Plan:**
- Frontend is already 100% built with Next.js 14, TypeScript, React Query, and shadcn/ui
- Authentication moved to Phase 4 (important but not urgent)
- Critical bug fixes prioritized in Phase 1
- Performance optimization moved to Phase 2

---

## Current Frontend Status ✅

### Already Implemented
The frontend is **production-ready** with the following features:

**Technology Stack:**
- Next.js 14 with TypeScript and App Router
- React 18.2 with React Query (TanStack Query v5)
- Tailwind CSS + shadcn/ui component library
- Recharts for data visualization
- Axios for HTTP requests
- Zod for validation

**Fully Built Pages:**
1. **Dashboard** - KPIs, active alerts, top devices, network throughput charts
2. **Devices** - Device inventory table with status indicators
3. **Device Detail** - Per-device metrics, charts, interface table, threshold config
4. **Alerts** - Active alerts with acknowledge/resolve actions
5. **Report** - Historical data viewer with CSV export
6. **Settings** - Alert recipients, interface thresholds, discovery trigger

**Features Working:**
- Real-time monitoring with auto-refresh
- Interactive time-series charts (CPU, Memory, Throughput)
- Alert management workflow
- Threshold configuration UI
- Email recipient management
- Network discovery trigger
- CSV report export

### Known Issues 🔴
1. **Threshold updates failing** - Frontend payload doesn't match backend API
2. **Performance issues** - Large payloads, slow queries
3. **Error handling broken** - Inconsistent error responses from backend

---

## Phase 1: Critical Bug Fixes (Week 1-2) 🔴 HIGH PRIORITY

### 1.1 Fix Threshold Update Endpoint Mismatch

**Current Problem:**
```javascript
// Frontend sends (frontend/src/lib/api.ts)
PUT /device/{ip}/thresholds
{
  cpu_threshold: 80,
  memory_threshold: 85,
  failure_threshold: 3
}

// Backend expects separate calls
PUT /device/{ip}/threshold/cpu
{ "threshold_value": 80 }

PUT /device/{ip}/threshold/memory
{ "threshold_value": 85 }
```

**Solution - Backend:**

```python
# backend/app/schemas/device.py (ADD)
from pydantic import BaseModel, Field
from typing import Optional

class ThresholdBatchUpdate(BaseModel):
    """Batch threshold update matching frontend payload"""
    cpu_threshold: Optional[float] = Field(None, ge=0, le=100)
    memory_threshold: Optional[float] = Field(None, ge=0, le=100)
    failure_threshold: Optional[int] = Field(None, ge=1, le=10)

class DeviceResponse(BaseModel):
    """DTO for device responses"""
    id: int
    ip_address: str
    hostname: str
    vendor: Optional[str]
    is_reachable: bool
    cpu_threshold: float
    memory_threshold: float
    failure_threshold: int
    cpu_alert_state: str
    memory_alert_state: str
    reachability_alert_state: str
    maintenance_mode: bool
    last_poll_success: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
```

```python
# backend/app/api/v1/endpoints/devices.py (UPDATE)
@router.put("/{ip}/thresholds", response_model=schemas.DeviceResponse)
async def update_device_thresholds(
    ip: str,
    thresholds: schemas.ThresholdBatchUpdate,
    db: Session = Depends(get_db)
):
    """Batch update all thresholds for a device"""
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {ip} not found")

    # Update only provided thresholds
    if thresholds.cpu_threshold is not None:
        device.cpu_threshold = thresholds.cpu_threshold
    if thresholds.memory_threshold is not None:
        device.memory_threshold = thresholds.memory_threshold
    if thresholds.failure_threshold is not None:
        device.failure_threshold = thresholds.failure_threshold

    db.commit()
    db.refresh(device)

    return schemas.DeviceResponse.model_validate(device)
```

**Files to Update:**
- `backend/app/schemas/device.py` - Add ThresholdBatchUpdate and DeviceResponse
- `backend/app/api/v1/endpoints/devices.py` - Add PUT /device/{ip}/thresholds endpoint
- Keep existing individual threshold endpoints for backward compatibility

**Testing:**
```bash
# Test from frontend threshold configuration UI
# Or test manually:
curl -X PUT http://localhost:8000/device/192.168.1.1/thresholds \
  -H "Content-Type: application/json" \
  -d '{"cpu_threshold": 80, "memory_threshold": 85}'
```

---

### 1.2 Implement Response DTOs (Prevent Schema Breakage)

**Issue:** Backend returns raw SQLAlchemy ORM objects, creating unstable API contracts.

**Impact:** Schema changes silently break frontend, ORM internals leak to API responses.

**Implementation:**

```python
# backend/app/schemas/__init__.py (CREATE OR UPDATE)
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class DeviceResponse(BaseModel):
    """Stable contract for device API responses"""
    id: int
    ip_address: str
    hostname: str
    vendor: Optional[str]
    is_reachable: bool
    cpu_threshold: float
    memory_threshold: float
    failure_threshold: int
    cpu_alert_state: str
    memory_alert_state: str
    reachability_alert_state: str
    maintenance_mode: bool
    last_poll_success: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class InterfaceSummaryResponse(BaseModel):
    """Lightweight interface data (only fields used by frontend)"""
    if_index: int
    if_name: str
    if_descr: Optional[str]
    oper_status: int
    admin_status: int
    octets_in: Optional[int]
    octets_out: Optional[int]
    discards_in: Optional[int]
    discards_out: Optional[int]
    errors_in: Optional[int]
    errors_out: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class MetricResponse(BaseModel):
    """Standardized metric response"""
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    uptime_seconds: int

    model_config = ConfigDict(from_attributes=True)

class AlertResponse(BaseModel):
    """Alert data for frontend"""
    id: int
    device_id: int
    device_ip: str
    device_hostname: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    state: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    remarks: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class NetworkSummaryResponse(BaseModel):
    """Dashboard network summary"""
    total_devices: int
    devices_up: int
    devices_down: int
    active_alerts: int
    critical_alerts: int
    warning_alerts: int

class TopDeviceResponse(BaseModel):
    """Top device by metric"""
    hostname: str
    ip_address: str
    value: float
```

**Update All Endpoints:**

```python
# backend/app/api/v1/endpoints/devices.py
@router.get("/", response_model=List[schemas.DeviceResponse])
async def get_all_devices(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    return [schemas.DeviceResponse.model_validate(d) for d in devices]

@router.get("/{ip}", response_model=schemas.DeviceResponse)
async def get_device(ip: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {ip} not found")
    return schemas.DeviceResponse.model_validate(device)
```

```python
# backend/app/api/v1/endpoints/query.py
@router.get("/network-summary", response_model=schemas.NetworkSummaryResponse)
async def get_network_summary(db: Session = Depends(get_db)):
    # ... existing logic ...
    return schemas.NetworkSummaryResponse(
        total_devices=total,
        devices_up=up_count,
        devices_down=down_count,
        active_alerts=alert_count,
        critical_alerts=critical,
        warning_alerts=warnings
    )
```

**Files to Update:**
- `backend/app/schemas/__init__.py` or `backend/app/schemas/device.py` - Create all DTOs
- `backend/app/api/v1/endpoints/devices.py` - Use DTOs, add response_model
- `backend/app/api/v1/endpoints/query.py` - Use DTOs, add response_model
- `backend/app/api/v1/endpoints/alerts.py` - Use DTOs, add response_model

---

### 1.3 Standardize Error Responses

**Current Problem:** Mixed error formats confuse frontend error handling

**Solution:**

```python
# backend/app/core/exceptions.py (CREATE)
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

class APIError(HTTPException):
    """Base API error with consistent format"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": self.details
            }
        )

# Common errors
class DeviceNotFoundError(APIError):
    def __init__(self, ip: str):
        super().__init__(
            status_code=404,
            error_code="DEVICE_NOT_FOUND",
            message=f"Device with IP {ip} not found"
        )

class ValidationError(APIError):
    def __init__(self, field: str, error: str):
        super().__init__(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="Invalid input data",
            details={"field": field, "error": error}
        )

class SNMPConnectionError(APIError):
    def __init__(self, ip: str, reason: str):
        super().__init__(
            status_code=503,
            error_code="SNMP_CONNECTION_FAILED",
            message=f"Failed to connect to device {ip}",
            details={"reason": reason}
        )

class DatabaseError(APIError):
    def __init__(self, operation: str):
        super().__init__(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=f"Database operation failed: {operation}"
        )
```

```python
# backend/app/main.py (UPDATE)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import APIError

app = FastAPI()

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle all APIError exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)}
        }
    )
```

**Usage in Endpoints:**

```python
# backend/app/api/v1/endpoints/devices.py
from app.core.exceptions import DeviceNotFoundError, ValidationError

@router.get("/{ip}", response_model=schemas.DeviceResponse)
async def get_device(ip: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise DeviceNotFoundError(ip)  # Returns consistent error format
    return schemas.DeviceResponse.model_validate(device)
```

**Frontend Update:**

```typescript
// frontend/src/lib/api.ts (UPDATE)
import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{error_code: string, message: string, details?: any}>) => {
    if (error.response) {
      const { error_code, message, details } = error.response.data;

      // Log for debugging
      console.error(`API Error [${error_code}]:`, message, details);

      // You can add toast notifications here
      // toast.error(message);

      // Return structured error
      return Promise.reject({
        code: error_code,
        message,
        details,
        status: error.response.status
      });
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Phase 2: Performance Optimization (Week 2-3)

### 2.1 Optimize Interface Endpoints (Reduce Payload by 60-80%)

**Current Problem:** Interface endpoint returns full SNMP data; frontend uses only 20%

**Solution: Create Summary Endpoint**

```python
# backend/app/api/v1/endpoints/query.py
@router.get("/device/{ip}/interfaces/summary", response_model=List[schemas.InterfaceSummaryResponse])
async def get_interface_summary(ip: str, db: Session = Depends(get_db)):
    """Return only essential interface fields needed by frontend"""
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise DeviceNotFoundError(ip)

    # Get latest metrics for each interface
    subquery = (
        db.query(
            models.InterfaceMetric.interface_id,
            func.max(models.InterfaceMetric.timestamp).label('max_timestamp')
        )
        .group_by(models.InterfaceMetric.interface_id)
        .subquery()
    )

    interfaces = (
        db.query(
            models.Interface.if_index,
            models.Interface.if_name,
            models.Interface.if_descr,
            models.InterfaceMetric.oper_status,
            models.InterfaceMetric.admin_status,
            models.InterfaceMetric.octets_in,
            models.InterfaceMetric.octets_out,
            models.InterfaceMetric.discards_in,
            models.InterfaceMetric.discards_out,
            models.InterfaceMetric.errors_in,
            models.InterfaceMetric.errors_out
        )
        .join(models.InterfaceMetric)
        .join(
            subquery,
            and_(
                models.InterfaceMetric.interface_id == subquery.c.interface_id,
                models.InterfaceMetric.timestamp == subquery.c.max_timestamp
            )
        )
        .filter(models.Interface.device_id == device.id)
        .all()
    )

    return [schemas.InterfaceSummaryResponse(
        if_index=intf[0],
        if_name=intf[1],
        if_descr=intf[2],
        oper_status=intf[3],
        admin_status=intf[4],
        octets_in=intf[5],
        octets_out=intf[6],
        discards_in=intf[7],
        discards_out=intf[8],
        errors_in=intf[9],
        errors_out=intf[10]
    ) for intf in interfaces]
```

**Frontend Update:**

```typescript
// frontend/src/lib/api.ts (UPDATE)
export const queryApi = {
  // Use new optimized endpoint
  getInterfaceSummary: async (ip: string) => {
    const response = await api.get(`/query/device/${ip}/interfaces/summary`);
    return response.data;
  },

  // Keep old endpoint for backward compatibility if needed
  getInterfaces: async (ip: string) => {
    const response = await api.get(`/query/device/${ip}/interfaces`);
    return response.data;
  },
};
```

**Update Device Detail Page:**

```typescript
// frontend/src/app/devices/[ip]/page.tsx (UPDATE)
// Change from getInterfaces to getInterfaceSummary
const { data: interfaces } = useQuery({
  queryKey: ['interfaces', ip],
  queryFn: () => queryApi.getInterfaceSummary(ip), // Use summary endpoint
  refetchInterval: 60000,
});
```

---

### 2.2 Implement Response Caching (Redis)

**Issue:** Expensive queries run repeatedly without caching

**Setup Redis:**

```python
# backend/requirements.txt (ADD)
redis==5.0.1
```

```python
# backend/app/core/cache.py (CREATE)
import redis
import json
from typing import Callable, Any, Optional
from functools import wraps
from datetime import timedelta

class CacheService:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=2
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            cached = self.redis_client.get(key)
            return json.loads(cached) if cached else None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache with TTL in seconds"""
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
        except (redis.RedisError, TypeError):
            pass  # Fail silently, don't break request

    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
        except redis.RedisError:
            pass

    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except redis.RedisError:
            pass

# Global cache instance
cache = CacheService()

def cached(ttl: int = 60, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

**Usage in Endpoints:**

```python
# backend/app/api/v1/endpoints/query.py
from app.core.cache import cache, cached

@router.get("/network-summary", response_model=schemas.NetworkSummaryResponse)
async def get_network_summary(db: Session = Depends(get_db)):
    """Get network summary with 30-second cache"""
    cache_key = "network_summary"

    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return schemas.NetworkSummaryResponse(**cached_data)

    # Calculate summary (expensive query)
    total = db.query(models.Device).count()
    devices_up = db.query(models.Device).filter(models.Device.is_reachable == True).count()
    active_alerts = db.query(models.Alert).filter(models.Alert.state == 'active').count()
    # ... more queries ...

    result = {
        "total_devices": total,
        "devices_up": devices_up,
        "devices_down": total - devices_up,
        "active_alerts": active_alerts,
        # ... more fields ...
    }

    # Cache for 30 seconds
    cache.set(cache_key, result, ttl=30)

    return schemas.NetworkSummaryResponse(**result)

@router.get("/top-devices/cpu", response_model=List[schemas.TopDeviceResponse])
async def get_top_cpu_devices(db: Session = Depends(get_db), limit: int = 5):
    """Get top CPU devices with 60-second cache"""
    cache_key = f"top_cpu_devices:{limit}"

    cached_data = cache.get(cache_key)
    if cached_data:
        return [schemas.TopDeviceResponse(**d) for d in cached_data]

    # Query top devices
    top_devices = # ... expensive query ...

    result = [{"hostname": d.hostname, "ip_address": d.ip, "value": d.cpu} for d in top_devices]
    cache.set(cache_key, result, ttl=60)

    return [schemas.TopDeviceResponse(**d) for d in result]
```

**Cache Invalidation on Updates:**

```python
# backend/app/api/v1/endpoints/devices.py
from app.core.cache import cache

@router.put("/{ip}/thresholds", response_model=schemas.DeviceResponse)
async def update_device_thresholds(ip: str, thresholds: schemas.ThresholdBatchUpdate, db: Session = Depends(get_db)):
    # ... update logic ...

    # Invalidate related caches
    cache.delete(f"device:{ip}")
    cache.delete("network_summary")
    cache.delete_pattern("top_*_devices:*")

    return schemas.DeviceResponse.model_validate(device)
```

**Optional: Docker Compose Redis**

```yaml
# docker-compose.yml (ADD)
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

---

## Phase 3: Frontend Integration Updates (Week 3-4)

### 3.1 Update All API Calls to Use New Endpoints

```typescript
// frontend/src/lib/api.ts (COMPREHENSIVE UPDATE)
import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Error interceptor (from Phase 1.3)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{error_code: string, message: string, details?: any}>) => {
    if (error.response?.data) {
      const { error_code, message, details } = error.response.data;
      console.error(`API Error [${error_code}]:`, message, details);

      // Return structured error for React Query
      return Promise.reject({
        code: error_code,
        message,
        details,
        status: error.response.status
      });
    }
    return Promise.reject(error);
  }
);

// Device API
export const deviceApi = {
  getAllDevices: async () => {
    const response = await api.get('/device/');
    return response.data;
  },

  getDevice: async (ip: string) => {
    const response = await api.get(`/device/${ip}`);
    return response.data;
  },

  // UPDATED: Use new batch threshold endpoint
  updateThresholds: async (ip: string, thresholds: {
    cpu_threshold?: number;
    memory_threshold?: number;
    failure_threshold?: number;
  }) => {
    const response = await api.put(`/device/${ip}/thresholds`, thresholds);
    return response.data;
  },

  acknowledgeAlert: async (ip: string) => {
    const response = await api.post(`/device/${ip}/acknowledge`);
    return response.data;
  },
};

// Query API
export const queryApi = {
  getNetworkSummary: async () => {
    const response = await api.get('/query/network-summary');
    return response.data;
  },

  getTopCpuDevices: async (limit: number = 5) => {
    const response = await api.get(`/query/top-devices/cpu?limit=${limit}`);
    return response.data;
  },

  getTopMemoryDevices: async (limit: number = 5) => {
    const response = await api.get(`/query/top-devices/memory?limit=${limit}`);
    return response.data;
  },

  // UPDATED: Use new summary endpoint
  getInterfaceSummary: async (ip: string) => {
    const response = await api.get(`/query/device/${ip}/interfaces/summary`);
    return response.data;
  },

  getDeviceMetrics: async (ip: string, hours: number = 24) => {
    const response = await api.get(`/query/device/${ip}/metrics?hours=${hours}`);
    return response.data;
  },

  getNetworkThroughput: async (hours: number = 24) => {
    const response = await api.get(`/query/network-throughput?hours=${hours}`);
    return response.data;
  },

  getActiveAlerts: async () => {
    const response = await api.get('/query/active-alerts');
    return response.data;
  },
};

// Config API
export const configApi = {
  getRecipients: async () => {
    const response = await api.get('/config/recipients');
    return response.data;
  },

  addRecipient: async (email: string) => {
    const response = await api.post('/config/recipients', { email });
    return response.data;
  },

  removeRecipient: async (email: string) => {
    const response = await api.delete(`/config/recipients/${email}`);
    return response.data;
  },

  triggerDiscovery: async () => {
    const response = await api.post('/config/discover');
    return response.data;
  },
};

export default api;
```

### 3.2 Add Error Handling to Components

```typescript
// frontend/src/app/devices/[ip]/page.tsx (UPDATE THRESHOLD HANDLING)
'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi } from '@/lib/api';
import { useState } from 'react';

export default function DeviceDetailPage({ params }: { params: { ip: string } }) {
  const queryClient = useQueryClient();
  const [thresholds, setThresholds] = useState({
    cpu_threshold: 80,
    memory_threshold: 85,
    failure_threshold: 3,
  });
  const [error, setError] = useState<string | null>(null);

  // Mutation for threshold updates
  const updateThresholdsMutation = useMutation({
    mutationFn: (newThresholds: typeof thresholds) =>
      deviceApi.updateThresholds(params.ip, newThresholds),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['device', params.ip] });
      // Show success toast
      alert('Thresholds updated successfully');
    },
    onError: (error: any) => {
      setError(error.message || 'Failed to update thresholds');
      console.error('Threshold update failed:', error);
    },
  });

  const handleThresholdUpdate = () => {
    setError(null);
    updateThresholdsMutation.mutate(thresholds);
  };

  return (
    <div>
      {/* ... device info ... */}

      <div className="threshold-config">
        <h3>Configure Thresholds</h3>

        {error && (
          <div className="error-message bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label>CPU Threshold (%)</label>
            <input
              type="number"
              value={thresholds.cpu_threshold}
              onChange={(e) => setThresholds({
                ...thresholds,
                cpu_threshold: parseFloat(e.target.value)
              })}
              min="0"
              max="100"
            />
          </div>

          <div>
            <label>Memory Threshold (%)</label>
            <input
              type="number"
              value={thresholds.memory_threshold}
              onChange={(e) => setThresholds({
                ...thresholds,
                memory_threshold: parseFloat(e.target.value)
              })}
              min="0"
              max="100"
            />
          </div>

          <button
            onClick={handleThresholdUpdate}
            disabled={updateThresholdsMutation.isPending}
            className="btn-primary"
          >
            {updateThresholdsMutation.isPending ? 'Updating...' : 'Update Thresholds'}
          </button>
        </div>
      </div>

      {/* ... rest of component ... */}
    </div>
  );
}
```

---

## Phase 4: Authentication (Week 4-6) - DEFERRED PRIORITY

### 4.1 Backend JWT Authentication

```python
# backend/requirements.txt (ADD)
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# backend/app/core/security.py (CREATE)
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Move to settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username, **payload}
    except JWTError:
        raise credentials_exception

# User model
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
```

```python
# backend/app/api/v1/endpoints/auth.py (CREATE)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models import User
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user.username, "admin": user.is_admin})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()

    return {"message": "User created successfully"}
```

**Protect Endpoints:**

```python
# backend/app/api/v1/endpoints/devices.py
from app.core.security import get_current_user

@router.get("/", response_model=List[schemas.DeviceResponse], dependencies=[Depends(get_current_user)])
async def get_all_devices(db: Session = Depends(get_db)):
    # ... existing logic ...
```

### 4.2 Frontend Authentication

```typescript
// frontend/src/lib/auth.ts (CREATE)
export const authService = {
  login: async (username: string, password: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    return data;
  },

  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },

  getToken: () => {
    return localStorage.getItem('token');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};

// Update axios interceptor
api.interceptors.request.use((config) => {
  const token = authService.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

```typescript
// frontend/src/app/login/page.tsx (CREATE)
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await authService.login(credentials.username, credentials.password);
      router.push('/dashboard');
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6">SNMP Monitoring Login</h1>

        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}

        <input
          type="text"
          placeholder="Username"
          value={credentials.username}
          onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
          className="w-full p-2 border rounded mb-4"
        />

        <input
          type="password"
          placeholder="Password"
          value={credentials.password}
          onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
          className="w-full p-2 border rounded mb-4"
        />

        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          Login
        </button>
      </form>
    </div>
  );
}
```

---

## Phase 5: Type Safety & Testing (Week 6-7)

### 5.1 Auto-Generate TypeScript Types from OpenAPI

```bash
# Install openapi-typescript
npm install --save-dev openapi-typescript

# Add to package.json scripts
{
  "scripts": {
    "generate-types": "openapi-typescript http://localhost:8000/openapi.json -o ./src/types/api.d.ts",
    "dev": "next dev",
    "build": "npm run generate-types && next build"
  }
}
```

```typescript
// frontend/src/types/api.d.ts (AUTO-GENERATED)
// This file will be generated automatically from backend OpenAPI schema
export interface DeviceResponse {
  id: number;
  ip_address: string;
  hostname: string;
  // ... matches backend DTOs exactly
}
```

### 5.2 Integration Testing

```python
# backend/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_threshold_update_flow():
    """Test complete threshold update flow"""
    # Update thresholds
    response = client.put(
        "/device/192.168.1.1/thresholds",
        json={"cpu_threshold": 80, "memory_threshold": 85}
    )
    assert response.status_code == 200
    assert response.json()["cpu_threshold"] == 80

def test_error_response_format():
    """Test error responses follow standard format"""
    response = client.get("/device/999.999.999.999")
    assert response.status_code == 404
    assert "error_code" in response.json()
    assert response.json()["error_code"] == "DEVICE_NOT_FOUND"
```

---

## Implementation Checklist

### Phase 1 (Week 1-2)
- [ ] Create `backend/app/schemas/device.py` with all DTOs
- [ ] Add `/device/{ip}/thresholds` batch update endpoint
- [ ] Update all device endpoints to use response_model
- [ ] Create `backend/app/core/exceptions.py` with error classes
- [ ] Add exception handlers to `main.py`
- [ ] Update frontend `api.ts` with error interceptor
- [ ] Test threshold updates end-to-end

### Phase 2 (Week 2-3)
- [ ] Install Redis (`docker-compose up -d redis`)
- [ ] Create `backend/app/core/cache.py`
- [ ] Add caching to network summary endpoint
- [ ] Add caching to top devices endpoints
- [ ] Create `/query/device/{ip}/interfaces/summary` endpoint
- [ ] Update frontend to use summary endpoint
- [ ] Add cache invalidation on device updates
- [ ] Monitor cache hit rates

### Phase 3 (Week 3-4)
- [ ] Update all frontend API calls to use new endpoints
- [ ] Add error handling to device detail page
- [ ] Add error handling to alerts page
- [ ] Add error handling to settings page
- [ ] Add loading states for all mutations
- [ ] Test all user flows end-to-end

### Phase 4 (Week 4-6) - DEFERRED
- [ ] Create User model and migration
- [ ] Implement JWT auth endpoints
- [ ] Add auth dependencies to protected routes
- [ ] Create login page in frontend
- [ ] Add auth interceptor to axios
- [ ] Implement route guards
- [ ] Test authentication flow

### Phase 5 (Week 6-7)
- [ ] Set up openapi-typescript generation
- [ ] Generate types from backend
- [ ] Replace manual types with generated types
- [ ] Write integration tests
- [ ] Performance testing
- [ ] Load testing

---

## Success Metrics

### Performance
- ✅ API response time < 200ms for 95% of requests
- ✅ Interface endpoint payload reduced by 60-80%
- ✅ Cache hit rate > 70% for dashboard queries
- ✅ Network summary cached (30s TTL)

### Reliability
- ✅ Error rate < 0.1% for API calls
- ✅ 100% of errors follow standard format
- ✅ Threshold updates work 100% of the time

### Code Quality
- ✅ 100% of API responses use DTOs (no ORM leakage)
- ✅ TypeScript types match backend schemas
- ✅ All mutations have error handling
- ✅ All queries have loading states

---

## Rollback Plan

1. **Feature Flags:** Use environment variables to toggle new endpoints
2. **Versioned APIs:** Keep old endpoints for 1 version overlap
3. **Database Migrations:** All migrations are reversible with Alembic
4. **Cache Failures:** Cache failures don't break requests (fail silently)
5. **Staged Rollout:** Deploy to staging first, production after validation

---

## Additional Recommendations

1. **Monitoring:** Add APM (DataDog, New Relic, or self-hosted Prometheus)
2. **Logging:** Implement structured logging with correlation IDs
3. **Rate Limiting:** Add per-IP rate limiting (slowapi or nginx)
4. **CORS:** Restrict origins in production
5. **Secret Management:** Use environment variables or Vault
6. **API Versioning:** Use `/api/v1` prefix for all endpoints
7. **Health Checks:** Add `/health` endpoint for monitoring

---

## Conclusion

This updated mitigation plan addresses:

✅ **Frontend already complete** - No major frontend work needed
❌ **Three critical bugs** - Threshold updates, performance, error handling
⏸️ **Authentication deferred** - Important but not urgent (Phase 4)
🚀 **Performance optimization** - Caching and optimized endpoints (Phase 2)
🔒 **Type safety** - DTOs prevent schema breakage (Phase 1)

**Next immediate action:** Implement Phase 1 (Critical Bug Fixes) focusing on threshold endpoint, DTOs, and error standardization.
