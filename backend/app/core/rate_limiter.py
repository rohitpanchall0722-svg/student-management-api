import logging

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from backend.app.core.redis import redis_client

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        real_ip = real_ip.strip()
        if real_ip:
            return real_ip

    if request.client:
        return request.client.host

    return "unknown"


def rate_limit(
    request: Request,
    key_prefix: str,
    limit: int,
    window: int
):
    client_identifier = get_client_identifier(request)
    key = f"{key_prefix}:{client_identifier}"

    try:
        current_count = redis_client.incr(key)

        if current_count == 1:
            redis_client.expire(key, window)
    except RedisError:
        logger.exception("Redis rate limit failed for key %s", key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limit service unavailable. Please try again later."
        ) from None

    if current_count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )


def rate_limit_dependency(
        key_prefix:str,limit:int,window:int
):
    def dependency(request:Request):
        rate_limit(
            request=request,
            key_prefix=key_prefix,
            window=window,
            limit=limit
        )
    return dependency