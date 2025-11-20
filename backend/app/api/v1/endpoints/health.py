"""
Health check endpoints for monitoring system status
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any
import redis
from datetime import datetime

from app.core.database import get_db
from app.config.settings import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    details: Dict[str, Any] = {}


class ServiceStatus(BaseModel):
    """Individual service status"""
    service: str
    status: str
    message: str = ""
    response_time_ms: float = 0


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health(db: Session = Depends(get_db)):
    """
    Overall system health check

    Returns the health status of all system components:
    - Database connectivity
    - Redis cache (if enabled)
    - System timestamp

    Status codes:
    - 200: System is healthy
    - 503: System has issues (check details)
    """
    timestamp = datetime.utcnow().isoformat()
    details = {}
    overall_healthy = True

    # Check database
    try:
        start_time = datetime.utcnow()
        db.execute(text("SELECT 1"))
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        details["database"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        details["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False

    # Check Redis (if enabled)
    if settings.cache_enabled:
        try:
            start_time = datetime.utcnow()
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                socket_connect_timeout=2,
                decode_responses=True
            )
            redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            details["redis"] = {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            details["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False
    else:
        details["redis"] = {
            "status": "disabled",
            "message": "Redis caching is disabled"
        }

    # Add configuration info
    details["config"] = {
        "environment": settings.environment,
        "cache_enabled": settings.cache_enabled,
        "polling_interval": settings.polling_interval
    }

    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        timestamp=timestamp,
        details=details
    )


@router.get("/health/database", response_model=ServiceStatus, tags=["Health"])
async def check_database(db: Session = Depends(get_db)):
    """
    Database health check

    Tests database connectivity and response time
    """
    try:
        start_time = datetime.utcnow()
        result = db.execute(text("SELECT 1")).scalar()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result == 1:
            return ServiceStatus(
                service="database",
                status="healthy",
                message="Database connection successful",
                response_time_ms=round(response_time, 2)
            )
        else:
            return ServiceStatus(
                service="database",
                status="unhealthy",
                message="Database query returned unexpected result"
            )
    except Exception as e:
        return ServiceStatus(
            service="database",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}"
        )


@router.get("/health/redis", response_model=ServiceStatus, tags=["Health"])
async def check_redis():
    """
    Redis cache health check

    Tests Redis connectivity and response time
    """
    if not settings.cache_enabled:
        return ServiceStatus(
            service="redis",
            status="disabled",
            message="Redis caching is disabled in configuration"
        )

    try:
        start_time = datetime.utcnow()
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            socket_connect_timeout=2,
            decode_responses=True
        )

        # Test ping
        redis_client.ping()

        # Test set/get
        test_key = "health_check_test"
        test_value = "ok"
        redis_client.setex(test_key, 10, test_value)
        retrieved = redis_client.get(test_key)
        redis_client.delete(test_key)

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if retrieved == test_value:
            return ServiceStatus(
                service="redis",
                status="healthy",
                message=f"Redis connection successful ({settings.redis_host}:{settings.redis_port})",
                response_time_ms=round(response_time, 2)
            )
        else:
            return ServiceStatus(
                service="redis",
                status="unhealthy",
                message="Redis read/write test failed"
            )
    except redis.ConnectionError as e:
        return ServiceStatus(
            service="redis",
            status="unhealthy",
            message=f"Cannot connect to Redis at {settings.redis_host}:{settings.redis_port} - {str(e)}"
        )
    except Exception as e:
        return ServiceStatus(
            service="redis",
            status="unhealthy",
            message=f"Redis health check failed: {str(e)}"
        )


@router.get("/health/services", tags=["Health"])
async def check_all_services(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all services

    Returns detailed status of all system components
    """
    services = []

    # Check database
    db_status = await check_database(db)
    services.append(db_status.dict())

    # Check Redis
    redis_status = await check_redis()
    services.append(redis_status.dict())

    # Overall status
    all_healthy = all(
        s["status"] in ["healthy", "disabled"]
        for s in services
    )

    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
        "environment": settings.environment
    }


@router.get("/ping", tags=["Health"])
async def ping():
    """
    Simple ping endpoint

    Returns a simple response to verify the API is running
    """
    return {
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }
