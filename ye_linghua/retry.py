"""Elegant retry mechanism module

Provides decorators and utility functions to support retry logic for async functions.

Features:
- Supports exponential backoff strategy
- Configurable retry count and intervals
- Supports specifying retryable exception types
- Detailed logging
- Fully decoupled, non-invasive to business code
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Retry configuration class"""

    def __init__(
        self,
        enabled: bool = True,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Args:
            enabled: Whether to enable retry mechanism
            max_retries: Maximum number of retries
            initial_delay: Initial delay time (seconds)
            max_delay: Maximum delay time (seconds)
            exponential_base: Exponential backoff base
            retryable_exceptions: Tuple of retryable exception types
        """
        self.enabled = enabled
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay time (exponential backoff)

        Args:
            attempt: Current attempt number (starting from 0)

        Returns:
            Delay time (seconds)
        """
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


class RetryExhaustedError(Exception):
    """Retry exhausted exception"""

    def __init__(self, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(f"Retry failed after {attempts} attempts. Last error: {str(last_exception)}")


def async_retry(
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable:
    """Async function retry decorator

    Args:
        config: Retry configuration object, uses default config if None
        on_retry: Callback function on retry, receives exception and current attempt number

    Returns:
        Decorator function

    Example:
        ```python
        @async_retry(RetryConfig(max_retries=3, initial_delay=1.0))
        async def call_api():
            # API call code
            pass
        ```
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    # Try to execute function
                    return await func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    # If this is the last attempt, don't retry
                    if attempt >= config.max_retries:
                        logger.error(f"Function {func.__name__} retry failed, reached maximum retry count {config.max_retries}")
                        raise RetryExhaustedError(e, attempt + 1)

                    # Calculate delay time
                    delay = config.calculate_delay(attempt)

                    # Log
                    logger.warning(
                        f"Function {func.__name__} call {attempt + 1} failed: {str(e)}, "
                        f"retrying attempt {attempt + 2} after {delay:.2f} seconds"
                    )

                    # Call callback function
                    if on_retry:
                        on_retry(e, attempt + 1)

                    # Wait before retry
                    await asyncio.sleep(delay)

            # Should not reach here in theory
            if last_exception:
                raise last_exception
            raise Exception("Unknown error")

        return wrapper

    return decorator
