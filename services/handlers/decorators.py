from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)
from models.custom_exceptions import APPException
from functools import wraps
from typing import Dict, Any, Type, List
import traceback


class DecoratorService:
    def __init__(self):
        pass

    def base_exception_handler(self, func):
        @wraps(func)
        async def wrapper(*args, **kargs):
            try:
                result = await func(*args, **kargs)
                return result
            except Exception as ex:
                params: Dict[str, Any] = {}
                params.update(kargs)

                raise APPException(
                    message=str(ex),
                    event_type="unknown",
                    ex_class=f"{type(ex).__module__}.{type(ex).__name__}",
                    params=params,
                    service_name='unknown',
                    stack_trace=traceback.format_exc(),
                )

        return wrapper

    def service_exception_handler(
            self,
            excluded_method_params: List[str],
            service_name: str,
            attempt: int = 3,
            *interested_exceptions,
    ):
        if interested_exceptions:
            retry_condition = retry_if_exception_type(interested_exceptions)
        else:
            retry_condition = retry_if_exception_type(Exception)

        def service_decorator(func):
            def handle_retry_error(retry_state):
                method_params: Dict = retry_state.kwargs
                last_exception = retry_state.outcome.exception()
                for key, value in list(method_params.items()):

                    if key in excluded_method_params:
                        method_params.pop(key, None)

                params: Dict[str, Any] = {}
                params.update(**method_params)

                raise APPException(
                    message=str(last_exception),
                    event_type="unknown",
                    ex_class=f"{type(last_exception).__module__}.{type(last_exception).__name__}",
                    params=params,
                    stack_trace="".join(
                        traceback.format_exception(
                            type(last_exception),
                            last_exception,
                            last_exception.__traceback__,
                        )
                    ),
                    service_name=service_name,
                )

            @wraps(func)
            @retry(
                stop=stop_after_attempt(attempt),
                wait=wait_exponential(multiplier=1, min=1, max=3),
                retry=retry_condition,
                retry_error_callback=handle_retry_error,
            )
            async def wrapper(*args, **kargs):
                return await func(*args, **kargs)

            return wrapper

        return service_decorator

    def message_handler_exception_decorator(self, event_type: str):
        def handler_decorator(func):
            @wraps(func)
            async def wrapper(*args, **kargs):
                try:
                    result = await func(*args, **kargs)
                    return result
                except APPException as ex:
                    ex.event_type = event_type
                    raise ex

            return wrapper

        return handler_decorator


decorator_service: DecoratorService = DecoratorService()
