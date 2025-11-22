"""
Polling state management module.
Provides thread-safe tracking of active polling operations.
"""
import asyncio
from typing import Optional


class PollingState:
    """Thread-safe polling state manager"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._is_polling = False
        self._polling_type: Optional[str] = None  # "automatic" or "manual"

    async def start_polling(self, polling_type: str = "automatic") -> bool:
        """
        Attempt to start a polling operation.

        Args:
            polling_type: Type of polling ("automatic" or "manual")

        Returns:
            True if polling was started, False if already in progress
        """
        async with self._lock:
            if self._is_polling:
                return False
            self._is_polling = True
            self._polling_type = polling_type
            return True

    async def end_polling(self):
        """Mark polling operation as complete"""
        async with self._lock:
            self._is_polling = False
            self._polling_type = None

    async def is_polling(self) -> bool:
        """Check if polling is currently active"""
        async with self._lock:
            return self._is_polling

    async def get_status(self) -> dict:
        """Get current polling status"""
        async with self._lock:
            return {
                "is_polling": self._is_polling,
                "polling_type": self._polling_type
            }


# Global polling state instance
_polling_state = PollingState()


def get_polling_state() -> PollingState:
    """Get the global polling state instance"""
    return _polling_state
