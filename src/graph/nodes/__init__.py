from functools import wraps
from src.monitoring.logger import get_logger

logger = get_logger("nodes")

def log_node(name: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(state, *args, **kwargs):
            logger.info(
                "Node start",
                extra={"extra": {"node": name, "trace_id": state.trace_id}},
            )
            result = await fn(state, *args, **kwargs)
            logger.info(
                "Node end",
                extra={"extra": {"node": name, "trace_id": state.trace_id, "result": result}},
            )
            return result
        return wrapper
    return decorator
