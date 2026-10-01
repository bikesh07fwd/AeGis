import time
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit Breaker OPENED after {self.failure_count} failures.")
            
    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
        
    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker HALF_OPEN: Testing next request.")
                return True
            return False
            
        if self.state == "HALF_OPEN":
            # Only allow one request through to test
            return False
            
        return True

def circuit_breaker(breaker: CircuitBreaker, fallback_func: Callable | None = None):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                logger.warning(f"Circuit breaker is OPEN for {func.__name__}. Request blocked.")
                if fallback_func:
                    return await fallback_func(*args, **kwargs)
                raise CircuitBreakerOpenException(f"Circuit breaker is OPEN for {func.__name__}")
                
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise e
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                logger.warning(f"Circuit breaker is OPEN for {func.__name__}. Request blocked.")
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                raise CircuitBreakerOpenException(f"Circuit breaker is OPEN for {func.__name__}")
                
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise e
                
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
        
    return decorator
