"""
Security utilities for Django authentication.
Matches FastAPI security implementation with Argon2 password hashing.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import jwt
from passlib.context import CryptContext


# Use Argon2 password context matching FastAPI implementation
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,      # Number of iterations
    argon2__memory_cost=65536, # Memory usage in kibibytes
    argon2__parallelism=4     # Number of parallel threads
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token matching FastAPI implementation.
    
    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=getattr(settings, 'JWT_TOKEN_EXPIRY_MINUTES', 30)
        )
    
    # Add JWT claims matching FastAPI implementation
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(data["sub"])  # Ensure sub is a string
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
    )
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using Argon2 hashing (matches FastAPI).
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using Argon2 (matches FastAPI).
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_refresh_token(user) -> str:
    """
    Create refresh token for user.
    
    Args:
        user: User instance
        
    Returns:
        Refresh token string
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, 'JWT_ALGORITHM', 'HS256')],
            options={
                "verify_exp": True,
                "verify_iat": True,
                "require_exp": True,
                "require_iat": True,
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.JWTError:
        raise TokenError("Invalid token")


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded secure token
    """
    return secrets.token_hex(length)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate numeric verification code.
    
    Args:
        length: Code length
        
    Returns:
        Numeric verification code
    """
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify API key against hash.
    
    Args:
        plain_key: Plain API key
        hashed_key: Hashed API key from database
        
    Returns:
        True if key matches, False otherwise
    """
    return hash_api_key(plain_key) == hashed_key


def create_session_token(user_id: int, session_data: Optional[Dict] = None) -> str:
    """
    Create session token with optional data.
    
    Args:
        user_id: User ID
        session_data: Optional session data
        
    Returns:
        Session token
    """
    token_data = {
        "user_id": user_id,
        "session_id": generate_secure_token(16),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if session_data:
        token_data.update(session_data)
    
    return create_access_token({"sub": str(user_id), **token_data})


def invalidate_user_tokens(user_id: int):
    """
    Invalidate all tokens for a user (logout from all devices).
    
    Args:
        user_id: User ID
    """
    # Add user to token blacklist cache
    cache_key = f"blacklisted_user_{user_id}"
    cache.set(cache_key, True, timeout=86400 * 7)  # 7 days


def is_token_blacklisted(user_id: int) -> bool:
    """
    Check if user tokens are blacklisted.
    
    Args:
        user_id: User ID
        
    Returns:
        True if tokens are blacklisted, False otherwise
    """
    cache_key = f"blacklisted_user_{user_id}"
    return cache.get(cache_key, False)


def rate_limit_key(user_id: int, action: str) -> str:
    """
    Generate rate limit cache key.
    
    Args:
        user_id: User ID
        action: Action being rate limited
        
    Returns:
        Cache key for rate limiting
    """
    return f"rate_limit_{action}_{user_id}"


def check_rate_limit(user_id: int, action: str, limit: int, window: int) -> bool:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id: User ID
        action: Action being checked
        limit: Maximum number of actions allowed
        window: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    key = rate_limit_key(user_id, action)
    current = cache.get(key, 0)
    
    if current >= limit:
        return False
    
    # Increment counter
    cache.set(key, current + 1, timeout=window)
    return True


def create_password_reset_token(user_id: int) -> str:
    """
    Create password reset token.
    
    Args:
        user_id: User ID
        
    Returns:
        Password reset token
    """
    token_data = {
        "sub": str(user_id),
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
    }
    
    return jwt.encode(
        token_data,
        settings.SECRET_KEY,
        algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
    )


def verify_password_reset_token(token: str) -> Optional[int]:
    """
    Verify password reset token and return user ID.
    
    Args:
        token: Password reset token
        
    Returns:
        User ID if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, 'JWT_ALGORITHM', 'HS256')]
        )
        
        if payload.get("type") != "password_reset":
            return None
            
        return int(payload.get("sub"))
    except (jwt.JWTError, ValueError, TypeError):
        return None


def create_email_verification_token(user_id: int, email: str) -> str:
    """
    Create email verification token.
    
    Args:
        user_id: User ID
        email: Email address to verify
        
    Returns:
        Email verification token
    """
    token_data = {
        "sub": str(user_id),
        "email": email,
        "type": "email_verification",
        "exp": datetime.now(timezone.utc) + timedelta(days=1)  # 24 hour expiry
    }
    
    return jwt.encode(
        token_data,
        settings.SECRET_KEY,
        algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
    )


def verify_email_verification_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify email verification token.
    
    Args:
        token: Email verification token
        
    Returns:
        Dict with user_id and email if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, 'JWT_ALGORITHM', 'HS256')]
        )
        
        if payload.get("type") != "email_verification":
            return None
            
        return {
            "user_id": int(payload.get("sub")),
            "email": payload.get("email")
        }
    except (jwt.JWTError, ValueError, TypeError):
        return None