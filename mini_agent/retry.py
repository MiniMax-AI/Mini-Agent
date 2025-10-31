"""优雅的重试机制模块

提供装饰器和工具函数，支持异步函数的重试逻辑。

特性：
- 支持指数退避策略
- 可配置重试次数和间隔
- 支持指定可重试的异常类型
- 详细的日志记录
- 完全解耦，不侵入业务代码
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """重试配置类"""

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
            enabled: 是否启用重试机制
            max_retries: 最大重试次数
            initial_delay: 初始延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避基数
            retryable_exceptions: 可重试的异常类型元组
        """
        self.enabled = enabled
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """计算延迟时间（指数退避）

        Args:
            attempt: 当前尝试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


class RetryExhaustedError(Exception):
    """重试次数耗尽异常"""

    def __init__(self, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(
            f"重试失败，已尝试 {attempts} 次。最后的错误: {str(last_exception)}"
        )


def async_retry(
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable:
    """异步函数重试装饰器

    Args:
        config: 重试配置对象，如果为 None 则使用默认配置
        on_retry: 重试时的回调函数，接收异常和当前尝试次数

    Returns:
        装饰器函数

    Example:
        ```python
        @async_retry(RetryConfig(max_retries=3, initial_delay=1.0))
        async def call_api():
            # API 调用代码
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
                    # 尝试执行函数
                    return await func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    # 如果是最后一次尝试，不再重试
                    if attempt >= config.max_retries:
                        logger.error(
                            f"函数 {func.__name__} 重试失败，已达到最大重试次数 {config.max_retries}"
                        )
                        raise RetryExhaustedError(e, attempt + 1)

                    # 计算延迟时间
                    delay = config.calculate_delay(attempt)

                    # 记录日志
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次调用失败: {str(e)}，"
                        f"{delay:.2f}秒后进行第 {attempt + 2} 次重试"
                    )

                    # 调用回调函数
                    if on_retry:
                        on_retry(e, attempt + 1)

                    # 等待后重试
                    await asyncio.sleep(delay)

            # 理论上不会执行到这里
            if last_exception:
                raise last_exception
            raise Exception("未知错误")

        return wrapper

    return decorator


async def retry_async_call(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
    **kwargs: Any,
) -> Any:
    """直接调用异步函数并应用重试逻辑

    适用于无法使用装饰器的场景。

    Args:
        func: 要执行的异步函数
        *args: 函数的位置参数
        config: 重试配置对象
        on_retry: 重试时的回调函数
        **kwargs: 函数的关键字参数

    Returns:
        函数执行结果

    Example:
        ```python
        result = await retry_async_call(
            api_call,
            param1, param2,
            config=RetryConfig(max_retries=3),
            on_retry=lambda e, n: print(f"Retry {n}: {e}")
        )
        ```
    """
    if config is None:
        config = RetryConfig()

    decorated_func = async_retry(config=config, on_retry=on_retry)(func)
    return await decorated_func(*args, **kwargs)
