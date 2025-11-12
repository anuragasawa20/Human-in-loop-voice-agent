"""
Comprehensive error handling and retry logic.

Design Decision:
- Classify errors into Transient, Permanent, and User errors
- Retry transient errors with exponential backoff
- Log all errors appropriately
- Provide graceful fallbacks
"""

import logging
import asyncio
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Temporary error that may succeed on retry."""
    pass


class PermanentError(Exception):
    """Permanent error that won't be fixed by retrying."""
    pass


class UserError(Exception):
    """User-caused error (bad input, etc.)."""
    pass


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay


async def retry_with_backoff(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Design Decision:
    - Exponential backoff: 1s, 2s, 4s, 8s, ...
    - Max delay cap to prevent too long waits
    - Only retry TransientErrors
    
    Args:
        func: Function to retry
        config: Retry configuration
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result
        
    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(f"Retry succeeded on attempt {attempt + 1}")
            
            return result
            
        except TransientError as e:
            last_exception = e
            
            if attempt < config.max_retries:
                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{config.max_retries + 1}: {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay = min(delay * config.backoff_multiplier, config.max_delay)
            else:
                logger.error(f"All {config.max_retries + 1} attempts failed: {e}")
                
        except (PermanentError, UserError) as e:
            # Don't retry these
            logger.error(f"Non-retryable error: {type(e).__name__}: {e}")
            raise
            
        except Exception as e:
            # Unknown errors - don't retry for safety
            logger.error(f"Unknown error type: {type(e).__name__}: {e}")
            raise
    
    # All retries exhausted
    raise last_exception


def with_error_handling(error_type: str = "general"):
    """
    Decorator for adding error handling to functions.
    
    Design Decision:
    - Categorize errors automatically
    - Log with appropriate severity
    - Provide fallback behavior
    
    Args:
        error_type: Type of operation (for logging context)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
                
            except UserError as e:
                logger.warning(f"User error in {error_type}: {e}")
                raise
                
            except TransientError as e:
                logger.warning(f"Transient error in {error_type}: {e}")
                # Retry automatically
                return await retry_with_backoff(func, *args, **kwargs)
                
            except PermanentError as e:
                logger.error(f"Permanent error in {error_type}: {e}")
                # Alert team in production
                await alert_team(error_type, str(e))
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error in {error_type}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


async def alert_team(context: str, error_message: str):
    """
    Alert team about critical errors.
    
    Design Decision:
    - In production: Send to Sentry, PagerDuty, etc.
    - In development: Just log
    
    Args:
        context: Where the error occurred
        error_message: Error details
    """
    logger.critical(f"ALERT - {context}: {error_message}")
    
    # In production, integrate with:
    # - Sentry for error tracking
    # - PagerDuty for on-call alerts
    # - Slack for team notifications
    
    # For now, just log
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for external services.
    
    Design Decision:
    - Prevent cascading failures
    - Fail fast when service is down
    - Automatically recover when service is back
    
    States:
    - CLOSED: Normal operation
    - OPEN: Service is down, fail fast
    - HALF_OPEN: Testing if service is back
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    logger.info("Circuit breaker timeout elapsed, entering HALF_OPEN state")
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    return False
            return True
        return False
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker recovered, entering CLOSED state")
                self.state = "CLOSED"
                self.success_count = 0
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
                self.state = "OPEN"
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass
            
        Returns:
            Function result
            
        Raises:
            Exception if circuit is open or function fails
        """
        if self.is_open():
            raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


# Global circuit breakers for external services
firebase_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
ai_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30)


def handle_database_error(error: Exception) -> Exception:
    """
    Classify database errors.
    
    Returns appropriate error type based on the error.
    """
    error_msg = str(error).lower()
    
    # Transient errors (retry)
    if any(x in error_msg for x in ['timeout', 'connection', 'temporary', 'unavailable']):
        return TransientError(f"Database temporarily unavailable: {error}")
    
    # Permanent errors (don't retry)
    if any(x in error_msg for x in ['permission', 'authentication', 'not found']):
        return PermanentError(f"Database access error: {error}")
    
    # Default to permanent to be safe
    return PermanentError(f"Database error: {error}")


def handle_ai_error(error: Exception) -> Exception:
    """
    Classify AI/LLM errors.
    
    Returns appropriate error type based on the error.
    """
    error_msg = str(error).lower()
    
    # Transient errors
    if any(x in error_msg for x in ['timeout', 'rate limit', 'overloaded', 'retry']):
        return TransientError(f"AI service temporarily unavailable: {error}")
    
    # Permanent errors
    if any(x in error_msg for x in ['invalid key', 'quota exceeded', 'model not found']):
        return PermanentError(f"AI configuration error: {error}")
    
    # Default to transient (AI services often have temporary issues)
    return TransientError(f"AI service error: {error}")

