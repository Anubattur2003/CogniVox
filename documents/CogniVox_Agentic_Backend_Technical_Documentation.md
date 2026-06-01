# CogniVox Agentic Backend Technical Documentation

## Overview

The Agentic Backend serves as the central orchestrator for the CogniVox ecosystem, providing authentication, user management, conversation threading, and API coordination between frontend and backend services. Built with modern FastAPI architecture, UV package management, and comprehensive health monitoring for optimal performance and reliability.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Modern Setup with UV](#modern-setup-with-uv)
3. [Technology Stack](#technology-stack)
4. [Enhanced API Design](#enhanced-api-design)
5. [Database Architecture](#database-architecture)
6. [Authentication & Security](#authentication--security)
7. [Service Integration](#service-integration)
8. [Health Monitoring](#health-monitoring)
9. [Timezone Management](#timezone-management)
10. [Performance Optimization](#performance-optimization)

## Architecture Overview

### Core Responsibilities
- **API Gateway**: Central point for all frontend requests with intelligent routing
- **Authentication**: JWT-based user authentication with role-based authorization
- **User Management**: Registration, profiles, subscription management, and admin controls
- **Thread Management**: Conversation threading with timezone-aware metadata
- **Service Orchestration**: Coordination between Memory and GraphRAG services
- **Request Routing**: Intelligent routing to appropriate backend services with load balancing

### Modern Architecture Features
- **UV Package Management**: 10-100x faster dependency installation with Windows compatibility
- **Health Monitoring**: Built-in health checks for all dependencies with real-time status
- **Graceful Shutdown**: Signal handling for clean service termination with state preservation
- **Service Discovery**: Dynamic service configuration and communication with auto-failover
- **Async Operations**: Full async/await support for high performance and concurrency
- **Enhanced Security**: Rate limiting, input validation, and comprehensive CORS configuration

## Modern Setup with UV

### Quick Setup (2-5 minutes)
```bash
cd Agentic-Backend

# UV-based setup with automatic virtual environment
python setup.py

# Start with health monitoring and service discovery
python run.py
```

### Advanced Setup Features
The enhanced `setup.py` script provides:
- **Python version validation** (3.8+ required with compatibility checks)
- **Automatic UV installation** (Windows/Unix compatible with PowerShell support)
- **Virtual environment creation** with Python 3.11 preference and fallback
- **Dependency installation** with Windows compilation fixes and binary preference
- **Installation verification** and comprehensive health checks
- **Error handling** with detailed troubleshooting and recovery suggestions

### Enhanced Run Script Capabilities
The modernized `run.py` provides:
- **Environment validation** and dependency health checks
- **External service discovery** (PostgreSQL, MongoDB, Ollama) with connection validation
- **Signal handling** for graceful shutdown with proper cleanup
- **Service configuration** for Memory and GraphRAG service integration
- **Multiple run modes** (development, production, debug) with performance tuning
- **Comprehensive logging** with structured output and monitoring integration

### Command Line Options
```bash
# Basic startup with health checks
python run.py

# Development mode with auto-reload and debug logging
python run.py --reload --log-level debug

# Custom port configuration with host binding
python run.py --port 9000 --host 0.0.0.0

# Auto-find available port with service discovery
python run.py --auto-port

# Production mode with multiple workers
python run.py --workers 4 --log-level info

# Skip dependency checks for faster startup
python run.py --skip-checks
```

## Technology Stack

### Core Framework
```yaml
API Framework:
  - FastAPI: 0.104.1 (high-performance async API with automatic OpenAPI)
  - Uvicorn: 0.24.0 (ASGI server with worker process management)
  - Pydantic: 2.5.0 (data validation, serialization, and JSON schema)

Development:
  - UV: Ultra-fast package manager (10-100x faster than pip)
  - Python: 3.8+ (with async/await support and type hints)
  - Virtual Environment: Isolated per-service environments with dependency management
```

### Database Layer
```yaml
Primary Database:
  - PostgreSQL: 16+ (ACID transactions, JSON support, UUID primary keys)
  - SQLAlchemy: 2.0.23 (async ORM with modern syntax and connection pooling)
  - Alembic: 1.13.0 (database migrations with dependency checking)

Document Storage:
  - MongoDB: 7.0+ (flexible document storage with aggregation pipelines)
  - Motor: 3.3.2 (async MongoDB driver with connection pooling)
```

### Authentication & Security
```yaml
Authentication:
  - JWT: 2.8.0 (stateless token-based auth with refresh tokens)
  - Passlib: 1.7.4 (password hashing utilities with Argon2)
  - Bcrypt: 4.1.2 (secure password hashing with salt rounds)

Security:
  - CORS middleware for cross-origin requests with origin validation
  - Request rate limiting with Redis backend
  - Input validation and sanitization with XSS prevention
  - SQL injection prevention with parameterized queries
```

## Enhanced API Design

### Modern FastAPI Architecture

#### Advanced Dependency Injection System
```python
from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.timezone_utils import get_utc_now, convert_to_utc

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency with async context management and connection pooling"""
    async with get_async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user with enhanced token validation"""
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={
                "verify_exp": True,
                "verify_iat": True,
                "require_exp": True,
                "require_iat": True,
            }
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token structure")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

#### Enhanced API Endpoints

**Authentication Endpoints**
```python
@router.post("/auth/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register new user with enhanced validation and background processing"""
    # Validate unique constraints
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Auto-generate username from email if not provided
    username = user_data.username or user_data.email.split('@')[0]
    
    if await get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user with timezone-aware timestamps
    db_user = User(
        email=user_data.email,
        username=username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role or UserRole.USER,
        created_at=get_utc_now(),
        subscription_plan_id=await get_default_subscription_plan_id(db)
    )
    
    # Add default models
    default_model = await get_default_model(db)
    if default_model:
        db_user.models.append(default_model)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Background task for user initialization
    background_tasks.add_task(initialize_user_resources, db_user.id)
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(db_user.id), "role": db_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced login with comprehensive user data and security logging"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Generate tokens
    access_token_expires = timedelta(minutes=settings.token_expiry_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Update last login timestamp
    user.last_login = get_utc_now()
    await db.commit()
    
    # Log successful login
    logger.info(f"Successful login for user: {user.username} (ID: {user.id})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.token_expiry_minutes * 60,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile with subscription details and preferences"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "role": current_user.role,
        "isActive": current_user.is_active,
        "subscriptionTier": current_user.subscription_tier,
        "createdAt": format_datetime_for_client(current_user.created_at),
        "lastLogin": format_datetime_for_client(current_user.last_login) if current_user.last_login else None
    }
```

**Conversation Management**
```python
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation thread with timezone awareness"""
    # Ensure timezone-aware timestamps
    created_at = convert_to_utc(conversation_data.created_at) if conversation_data.created_at else get_utc_now()
    updated_at = convert_to_utc(conversation_data.updated_at) if conversation_data.updated_at else get_utc_now()
    
    # Create conversation document in MongoDB
    conversation_dict = {
        "user_id": str(current_user.id),
        "title": conversation_data.title,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
        "metadata": conversation_data.metadata or {}
    }
    
    result = await mongodb.threads.insert_one(conversation_dict)
    conversation_dict["_id"] = str(result.inserted_id)
    conversation_dict["chat_id"] = str(result.inserted_id)
    
    # Update with chat_id
    await mongodb.threads.update_one(
        {"_id": result.inserted_id}, 
        {"$set": {"chat_id": str(result.inserted_id)}}
    )
    
    # Create metadata entry in PostgreSQL
    thread_metadata = ThreadMetadata(
        chat_id=conversation_dict["chat_id"],
        user_id=str(current_user.id),
        created_at=created_at,
        updated_at=updated_at
    )
    db.add(thread_metadata)
    await db.commit()
    await db.refresh(thread_metadata)
    
    return conversation_dict

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation messages with pagination and timezone formatting"""
    # Validate conversation ownership
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    conversation = await mongodb.threads.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get sub-threads (messages) with pagination
    sub_threads = conversation.get("sub_threads", [])
    total_messages = len(sub_threads)
    
    # Apply pagination
    paginated_messages = sub_threads[skip:skip + limit]
    
    # Format timestamps for client
    for message in paginated_messages:
        if "created_at" in message:
            message["created_at"] = format_datetime_for_client(
                datetime.fromisoformat(message["created_at"].replace('Z', '+00:00'))
            )
        if "updated_at" in message:
            message["updated_at"] = format_datetime_for_client(
                datetime.fromisoformat(message["updated_at"].replace('Z', '+00:00'))
            )
    
    return {
        "messages": paginated_messages,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total_messages,
            "has_more": skip + limit < total_messages
        }
    }
```

**Admin Endpoints**
```python
@router.post("/admin/reset_requests/{user_id}")
async def reset_requests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_role)
):
    """Reset a user's remaining request counters and related transaction stats (ADMIN only)"""
    # Ensure the current user is an admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reset requests"
        )

    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Reset the user's requests for each model to the model's default requests
    user_model_requests = db.query(UserModelRequest).filter(UserModelRequest.user_id == user.id).all()
    reset_count = 0
    
    for umr in user_model_requests:
        model = db.query(Model).filter(Model.id == umr.model_id).first()
        if model:
            old_requests = umr.remaining_requests
            umr.remaining_requests = model.default_requests
            reset_count += 1
            logger.info(f"Reset user {user_id} model {model.name} requests: {old_requests} -> {model.default_requests}")

    # Reset the transaction request count to 0
    transactions = db.query(RequestTransaction).filter(RequestTransaction.user_id == user.id).all()
    transaction_reset_count = 0
    
    for transaction in transactions:
        old_count = transaction.request_count
        transaction.request_count = 0
        transaction_reset_count += 1
        logger.info(f"Reset user {user_id} transaction {transaction.id}: {old_count} -> 0")

    db.commit()
    
    logger.info(f"Admin {current_user.username} reset requests for user {user.username} ({user_id}): {reset_count} models, {transaction_reset_count} transactions")

    return {
        "message": "User requests and transactions reset successfully",
        "user_id": user_id,
        "username": user.username,
        "models_reset": reset_count,
        "transactions_reset": transaction_reset_count,
        "reset_by": current_user.username,
        "reset_at": get_utc_now().isoformat()
    }

@router.post("/admin/add_models_to_user/{user_id}")
async def add_models_to_user(
    user_id: int,
    model_names: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_role)
):
    """Attach one or more models to a user and initialize model-specific request quotas (ADMIN only)"""
    # Ensure the current user is an admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add models to users"
        )

    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    added_models = []
    skipped_models = []
    failed_models = []

    # Add models to the user
    for model_name in model_names:
        try:
            model = db.query(Model).filter(Model.name == model_name).first()
            if not model:
                failed_models.append({"name": model_name, "reason": "Model not found"})
                continue
            
            if model in user.models:
                skipped_models.append({"name": model_name, "reason": "Already assigned"})
                continue
            
            # Add model to user
            user.models.append(model)
            
            # Initialize UserModelRequest for the new model
            user_model_request = UserModelRequest(
                user_id=user.id,
                model_id=model.id,
                remaining_requests=model.default_requests
            )
            db.add(user_model_request)
            
            added_models.append({
                "name": model_name,
                "id": model.id,
                "default_requests": model.default_requests
            })
            
            logger.info(f"Admin {current_user.username} added model {model_name} to user {user.username} ({user_id})")
            
        except Exception as e:
            failed_models.append({"name": model_name, "reason": str(e)})

    db.commit()
    
    logger.info(f"Admin {current_user.username} added models to user {user.username} ({user_id}): {len(added_models)} successful, {len(skipped_models)} skipped, {len(failed_models)} failed")

    return {
        "message": "Models processing completed",
        "user_id": user_id,
        "username": user.username,
        "added_models": added_models,
        "skipped_models": skipped_models,
        "failed_models": failed_models,
        "added_by": current_user.username,
        "added_at": get_utc_now().isoformat()
    }
```

## Database Architecture

### Enhanced PostgreSQL Schema Design

#### Core Tables with Advanced Features
```sql
-- Users table with enhanced fields and timezone support
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    role VARCHAR(20) DEFAULT 'user',
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_plan_id UUID REFERENCES subscription_plans(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Enhanced conversation threading with timezone awareness
CREATE TABLE thread_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    is_archived BOOLEAN DEFAULT false,
    message_count INTEGER DEFAULT 0
);

-- Request tracking for analytics and rate limiting
CREATE TABLE request_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    model_id UUID REFERENCES models(id),
    model_name VARCHAR(100),
    request_type VARCHAR(50),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    request_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- User model requests for quota management
CREATE TABLE user_model_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    model_id UUID NOT NULL REFERENCES models(id),
    remaining_requests INTEGER NOT NULL DEFAULT 0,
    total_requests INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, model_id)
);

-- Models table for AI model management
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    category VARCHAR(50),
    default_requests INTEGER DEFAULT 100,
    is_visible BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Advanced Database Features
- **UUID Primary Keys**: Better for distributed systems and security
- **JSONB Support**: Flexible metadata and configuration storage
- **Timezone Awareness**: All timestamps stored with timezone information
- **Strategic Indexes**: Optimized for common query patterns and performance
- **Foreign Key Constraints**: Data integrity enforcement with cascading deletes
- **Automatic Timestamps**: Created/updated tracking with timezone support

#### Performance Optimizations
```sql
-- Strategic indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role_active ON users(role, is_active);
CREATE INDEX idx_thread_metadata_user_id ON thread_metadata(user_id);
CREATE INDEX idx_thread_metadata_created_at ON thread_metadata(created_at DESC);
CREATE INDEX idx_request_transactions_user_id ON request_transactions(user_id);
CREATE INDEX idx_request_transactions_created_at ON request_transactions(created_at DESC);
CREATE INDEX idx_user_model_requests_user_id ON user_model_requests(user_id);

-- Partial indexes for active records
CREATE INDEX idx_users_active ON users(id) WHERE is_active = true;
CREATE INDEX idx_models_visible_active ON models(id) WHERE is_visible = true AND is_active = true;
```

### Alembic Migration System

#### Enhanced Migration Management
```python
# Enhanced migration with dependency checking and rollback support
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    """Add enhanced user management features with timezone support"""
    # Check for existing table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'users' not in inspector.get_table_names():
        # Create users table with all modern features
    op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
            sa.Column('username', sa.String(50), nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('first_name', sa.String(100)),
            sa.Column('last_name', sa.String(100)),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('role', sa.String(20), nullable=False, server_default=sa.text("'user'")),
            sa.Column('subscription_tier', sa.String(20), nullable=False, server_default=sa.text("'free'")),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('last_login', sa.TIMESTAMP(timezone=True)),
            sa.Column('preferences', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username')
        )
        
        # Create indexes for performance
        op.create_index('idx_users_email', 'users', ['email'])
        op.create_index('idx_users_username', 'users', ['username'])
        op.create_index('idx_users_role_active', 'users', ['role', 'is_active'])

def downgrade() -> None:
    """Rollback user management features"""
    op.drop_table('users')
```

## Authentication & Security

### Enhanced JWT Implementation

#### Advanced Token Management
```python
class EnhancedTokenManager:
    """Advanced JWT token management with security features"""
    
    def __init__(self):
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.secret_key = settings.jwt_secret_key
    
    async def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with enhanced security claims"""
    to_encode = data.copy()
        
        # Set expiration
    if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
    else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        # Enhanced token claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "nbf": datetime.now(timezone.utc),  # Not before
            "type": "access",
            "jti": str(uuid.uuid4()),  # JWT ID for revocation
            "iss": "cognivox-backend",  # Issuer
            "aud": ["cognivox-frontend", "cognivox-api"]  # Audience
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token with comprehensive validation"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "require_exp": True,
                    "require_iat": True,
                    "require_nbf": True,
                }
            )
            
            # Additional validations
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            if payload.get("iss") != "cognivox-backend":
                raise HTTPException(status_code=401, detail="Invalid token issuer")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.ImmatureSignatureError:
            raise HTTPException(status_code=401, detail="Token not yet valid")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token for token renewal"""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
```

### Enhanced Security Middleware

#### Comprehensive CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

# Enhanced CORS with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "https://cognivox.example.com"  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Request-ID",
        "X-Timezone"
    ],
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

#### Rate Limiting and Security Headers
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Enhanced rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/auth/token")
@limiter.limit("5/minute")  # Strict limit for authentication
async def login_with_rate_limit(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login endpoint with enhanced rate limiting"""
    pass

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add comprehensive security headers"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # Request tracking
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response.headers["X-Request-ID"] = request_id
    
    return response
```

## Service Integration

### Enhanced Memory Service Integration

#### Advanced Service Communication
```python
class MemoryServiceClient:
    """Enhanced client for Memory service integration with retry logic and health monitoring"""
    
    def __init__(self, base_url=None):
        # Enhanced service discovery
        if base_url:
            self.base_url = base_url
        else:
            memory_url = os.getenv("MEMORY_SERVICE_URL")
            memory_port = os.getenv("MEMORY_PORT", "8002")
            
            if memory_url:
                self.base_url = memory_url
            else:
                self.base_url = f"http://localhost:{memory_port}"
                
        self.timeout = aiohttp.ClientTimeout(total=300, connect=30)
        self.session = None
        self.retry_config = {
            "max_retries": 3,
            "backoff_factor": 0.3,
            "status_forcelist": [500, 502, 503, 504]
        }
    
    async def get_session(self):
        """Get or create HTTP session with connection pooling"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        return self.session
    
    async def send_request_with_retry(self, method: str, endpoint: str, **kwargs):
        """Send request with exponential backoff retry logic"""
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_config["max_retries"]):
            try:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status in self.retry_config["status_forcelist"]:
                        if attempt == self.retry_config["max_retries"] - 1:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
                        # Exponential backoff
                        delay = self.retry_config["backoff_factor"] * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        response.raise_for_status()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.retry_config["max_retries"] - 1:
                    raise
                delay = self.retry_config["backoff_factor"] * (2 ** attempt)
                await asyncio.sleep(delay)
    
    async def process_chat_message(
        self,
        user_id: str,
        message: str, 
        conversation_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Process chat message with enhanced error handling"""
        try:
            payload = {
                        "user_id": user_id,
                "message": message,
                        "conversation_id": conversation_id,
                "context": context or {},
                "timestamp": get_utc_now().isoformat()
            }
            
            response = await self.send_request_with_retry(
                "POST",
                "/api/agents/process",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Request-ID": str(uuid.uuid4())
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Memory service request failed: {str(e)}")
            # Fallback response
            return {
                "response": "I'm having trouble processing your request right now. Please try again.",
                "error": True,
                "fallback": True
            }
    
    async def check_health(self) -> bool:
        """Check Memory service health"""
        try:
            response = await self.send_request_with_retry(
                "GET",
                "/api/health",
                timeout=aiohttp.ClientTimeout(total=10)
            )
            return response.get("status") == "ok"
        except Exception:
            return False
```

### GraphRAG Service Integration

#### Enhanced Document Processing Integration
```python
class GraphRAGServiceClient:
    """Enhanced GraphRAG service client with caching and optimization"""
    
    def __init__(self, base_url=None):
        # Service discovery
        if base_url:
            self.base_url = base_url
        else:
            graphrag_url = os.getenv("GRAPHRAG_SERVICE_URL")
            graphrag_port = os.getenv("GRAPHRAG_PORT", "8003")
            
            if graphrag_url:
                self.base_url = graphrag_url
            else:
                self.base_url = f"http://localhost:{graphrag_port}"
        
        self.timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes for document processing
        self.session = None
    
    async def ingest_document(
        self,
        file_path: str,
        user_id: Optional[str] = None,
        extraction_method: str = "auto",
        force: bool = False
    ) -> Dict:
        """Ingest document with enhanced parameters and error handling"""
        try:
            session = await self.get_session()
            
            payload = {
                "pdf_path": file_path,
                "user_id": user_id,
                "extraction_method": extraction_method,
                "force": force,
                "use_llamaindex": True,  # Use modern LlamaIndex processing
                "generate_embeddings": True
            }
            
            async with session.post(
                f"{self.base_url}/ingest",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Request-ID": str(uuid.uuid4())
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Document ingested successfully: {file_path}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Document ingestion failed: {error_text}")
            raise HTTPException(
                        status_code=response.status,
                        detail=f"GraphRAG ingestion failed: {error_text}"
            )
                    
        except Exception as e:
            logger.error(f"GraphRAG service error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Document processing service unavailable: {str(e)}"
            )
    
    async def query_knowledge_graph(
        self,
        query: str,
        user_id: Optional[str] = None,
        mode: str = "hybrid",
        n_results: int = 5
    ) -> Dict:
        """Query knowledge graph with enhanced parameters"""
        try:
            session = await self.get_session()
            
            payload = {
                "query": query,
                "user_id": user_id,
                "mode": mode,
                "n_results": n_results,
                "include_sources": True,
                "include_metadata": True
            }
            
            async with session.post(
                f"{self.base_url}/query",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"GraphRAG query failed: {error_text}")
                    return {
                        "response": "Unable to search knowledge base at this time.",
                        "sources": [],
                        "error": True
                    }
                    
        except Exception as e:
            logger.error(f"GraphRAG query error: {str(e)}")
            return {
                "response": "Knowledge search service unavailable.",
                "sources": [],
                "error": True
            }
```

## Health Monitoring

### Comprehensive Health Check System

#### Enhanced Health Check Implementation
```python
@app.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check with dependency validation and performance metrics"""
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "service": "CogniVox Backend API",
        "version": "1.0.0",
        "timestamp": get_utc_now().isoformat(),
        "dependencies": {},
        "performance": {},
        "environment": {
            "python_version": sys.version,
            "fastapi_version": fastapi.__version__,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }
    
    # Check PostgreSQL with connection pool status
    pg_start = time.time()
    try:
        async with get_async_session() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))
            
            # Test table access
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            # Get connection pool stats
            pool = session.get_bind().pool
            health_status["dependencies"]["postgresql"] = {
                "status": "healthy",
                "response_time_ms": int((time.time() - pg_start) * 1000),
                "user_count": user_count,
                "connection_pool": {
                    "size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
            }
    except Exception as e:
        health_status["dependencies"]["postgresql"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - pg_start) * 1000)
        }
        health_status["status"] = "degraded"
    
    # Check MongoDB with detailed metrics
    mongo_start = time.time()
    try:
        # Test connection and ping
        await mongodb.admin.command('ping')
        
        # Get database statistics
        db_stats = await mongodb.command('dbStats')
        
        # Get collection information
        collections = await mongodb.list_collection_names()
        
        health_status["dependencies"]["mongodb"] = {
            "status": "healthy",
            "response_time_ms": int((time.time() - mongo_start) * 1000),
            "collections": len(collections),
            "database_size_mb": round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
            "documents": db_stats.get('objects', 0)
        }
    except Exception as e:
        health_status["dependencies"]["mongodb"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - mongo_start) * 1000)
        }
        health_status["status"] = "degraded"
    
    # Check Ollama LLM service
    ollama_start = time.time()
    try:
        ollama_url = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
        async with httpx.AsyncClient() as client:
            # Check service availability
            response = await client.get(f"{ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                health_status["dependencies"]["ollama"] = {
                    "status": "healthy",
                    "response_time_ms": int((time.time() - ollama_start) * 1000),
                    "available_models": len(models),
                    "models": [model.get('name') for model in models[:5]]  # First 5 models
                }
            else:
                health_status["dependencies"]["ollama"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": int((time.time() - ollama_start) * 1000)
                }
            health_status["status"] = "degraded"
    
    except Exception as e:
        health_status["dependencies"]["ollama"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - ollama_start) * 1000)
        }
        health_status["status"] = "degraded"
    
    # Check Memory service
    memory_start = time.time()
    try:
        memory_client = MemoryServiceClient()
        is_healthy = await memory_client.check_health()
        
        health_status["dependencies"]["memory_service"] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time_ms": int((time.time() - memory_start) * 1000),
            "url": memory_client.base_url
        }
        
        if not is_healthy:
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["dependencies"]["memory_service"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - memory_start) * 1000)
        }
        health_status["status"] = "degraded"
    
    # Check GraphRAG service
    graphrag_start = time.time()
    try:
        graphrag_client = GraphRAGServiceClient()
        is_healthy = await graphrag_client.check_health()
        
        health_status["dependencies"]["graphrag_service"] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time_ms": int((time.time() - graphrag_start) * 1000),
            "url": graphrag_client.base_url
        }
        
        if not is_healthy:
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["dependencies"]["graphrag_service"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - graphrag_start) * 1000)
        }
        health_status["status"] = "degraded"
    
    # Performance metrics
    total_time = time.time() - start_time
    health_status["performance"] = {
        "total_response_time_ms": int(total_time * 1000),
        "uptime_seconds": int(time.time() - app_start_time),
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "cpu_percent": psutil.Process().cpu_percent()
    }
    
    return health_status
```

## Timezone Management

### Comprehensive Timezone Utilities

The backend includes comprehensive timezone management utilities for consistent handling of datetime data across the system.

#### Core Timezone Functions
```python
# app/core/timezone_utils.py
from datetime import datetime, timezone
from typing import Union, Optional, Dict
from zoneinfo import ZoneInfo

def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)

def convert_to_utc(dt: Union[datetime, str], source_timezone: Optional[str] = None) -> datetime:
    """Convert a datetime to UTC timezone with comprehensive handling."""
    if isinstance(dt, str):
        # Parse ISO format string
        if dt.endswith('Z'):
            return datetime.fromisoformat(dt[:-1] + '+00:00')
        elif '+' in dt or dt.endswith(('UTC', 'GMT')):
            return datetime.fromisoformat(dt.replace('UTC', '+00:00').replace('GMT', '+00:00'))
        else:
            # Naive datetime string - apply source timezone
            parsed_dt = datetime.fromisoformat(dt)
            if source_timezone:
                source_tz = ZoneInfo(source_timezone)
                parsed_dt = parsed_dt.replace(tzinfo=source_tz)
            else:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            return parsed_dt.astimezone(timezone.utc)
    
    # Handle datetime objects
    if dt.tzinfo is None:
        # Naive datetime - apply source timezone or assume UTC
        if source_timezone:
            source_tz = ZoneInfo(source_timezone)
            dt = dt.replace(tzinfo=source_tz)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(timezone.utc)

def convert_from_utc(utc_dt: datetime, target_timezone: str) -> datetime:
    """Convert UTC datetime to target timezone."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    target_tz = ZoneInfo(target_timezone)
    return utc_dt.astimezone(target_tz)

def format_datetime_for_client(dt: datetime, client_timezone: Optional[str] = None) -> Dict:
    """Format datetime for client consumption with multiple timezone representations."""
    # Ensure UTC timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    
    result = {
        'utc': dt.isoformat(),
        'unix_timestamp': int(dt.timestamp()),
        'display_format': dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    }
    
    # Convert to client timezone if provided
    if client_timezone:
        try:
            local_dt = convert_from_utc(dt, client_timezone)
            result.update({
                'local': local_dt.isoformat(),
                'local_display': local_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'local_timezone': client_timezone
            })
        except Exception:
            # Fallback if timezone conversion fails
            result.update({
                'local': dt.isoformat(),
                'local_display': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'local_timezone': 'UTC'
            })
    
    return result

def validate_timezone(timezone_name: str) -> bool:
    """Validate if a timezone name is valid."""
    try:
        ZoneInfo(timezone_name)
        return True
    except Exception:
        return False

# Common timezone mappings for legacy support
TIMEZONE_MAPPINGS = {
    'EST': 'America/New_York',
    'PST': 'America/Los_Angeles',
    'GMT': 'UTC',
    'UTC': 'UTC',
    'CST': 'America/Chicago',
    'MST': 'America/Denver',
    'JST': 'Asia/Tokyo',
    'CET': 'Europe/Paris',
    'IST': 'Asia/Kolkata'
}

def normalize_timezone_name(timezone_input: str) -> str:
    """Normalize timezone name, handling common abbreviations."""
    # Check if it's already a valid timezone
    if validate_timezone(timezone_input):
        return timezone_input
    
    # Check timezone mappings
    normalized = TIMEZONE_MAPPINGS.get(timezone_input.upper())
    if normalized and validate_timezone(normalized):
        return normalized
    
    # Default to UTC if unable to normalize
    return 'UTC'
```

#### API Integration with Timezone Support
```python
@app.middleware("http")
async def timezone_middleware(request: Request, call_next):
    """Middleware to handle client timezone information"""
    # Get client timezone from headers
    client_timezone = request.headers.get('X-Timezone')
    
    if client_timezone:
        # Validate and normalize timezone
        normalized_tz = normalize_timezone_name(client_timezone)
        request.state.client_timezone = normalized_tz
    else:
        request.state.client_timezone = 'UTC'
    
    response = await call_next(request)
    
    # Add server timezone to response headers
    response.headers['X-Server-Timezone'] = 'UTC'
    response.headers['X-Client-Timezone'] = request.state.client_timezone
    
    return response

# Usage in API endpoints
@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get conversation with timezone-aware timestamps"""
    conversation = await get_conversation_by_id(conversation_id)
    
    # Format timestamps for client timezone
    client_tz = getattr(request.state, 'client_timezone', 'UTC')
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": format_datetime_for_client(conversation.created_at, client_tz),
        "updated_at": format_datetime_for_client(conversation.updated_at, client_tz),
        "message_count": conversation.message_count
    }
```

## Performance Optimization

### Database Performance Optimizations

#### Connection Pooling and Query Optimization
```python
# Enhanced database configuration
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool

# Optimized engine configuration
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Disable in production
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Query optimization with caching
from functools import lru_cache

@lru_cache(maxsize=100, typed=True)
async def get_user_by_id_cached(user_id: int) -> Optional[User]:
    """Cached user lookup for frequently accessed users"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# Batch operations for efficiency
async def create_multiple_user_model_requests(requests: List[UserModelRequestCreate]):
    """Batch create user model requests"""
    async with AsyncSessionLocal() as session:
        db_requests = [
            UserModelRequest(**request.dict()) 
            for request in requests
        ]
        session.add_all(db_requests)
        await session.commit()
        return db_requests
```

#### Response Caching and Optimization
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Initialize caching
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="cognivox-cache")

# Cache API responses
@router.get("/models")
@cache(expire=300)  # Cache for 5 minutes
async def get_available_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available models with caching"""
    result = await db.execute(
        select(Model).where(Model.is_active == True, Model.is_visible == True)
    )
    models = result.scalars().all()
    return [model.to_dict() for model in models]

# Background task processing
@router.post("/conversations/{conversation_id}/process")
async def process_conversation(
    conversation_id: str,
    message: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Process conversation with background task"""
    # Immediate response
    response = {"status": "processing", "conversation_id": conversation_id}
    
    # Add background processing
    background_tasks.add_task(
        process_message_background,
        conversation_id,
        message,
        current_user.id
    )
    
    return response

async def process_message_background(conversation_id: str, message: str, user_id: str):
    """Background task for message processing"""
    try:
        # Process with Memory service
        memory_client = MemoryServiceClient()
        result = await memory_client.process_chat_message(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id
        )
        
        # Store result in database
        async with AsyncSessionLocal() as session:
            # Update conversation with result
            await update_conversation_with_result(session, conversation_id, result)
            await session.commit()
            
    except Exception as e:
        logger.error(f"Background processing failed: {str(e)}")
```

### Memory and Resource Management
```python
import gc
import psutil
from contextlib import asynccontextmanager

@asynccontextmanager
async def memory_monitor():
    """Context manager for memory monitoring"""
    initial_memory = psutil.Process().memory_info().rss
    try:
        yield
    finally:
        final_memory = psutil.Process().memory_info().rss
        memory_diff = final_memory - initial_memory
        if memory_diff > 50 * 1024 * 1024:  # 50MB threshold
            logger.warning(f"High memory usage detected: {memory_diff / 1024 / 1024:.1f} MB")
            gc.collect()  # Force garbage collection

# Usage in endpoints
@router.post("/documents/process")
async def process_document(file: UploadFile):
    """Process document with memory monitoring"""
    async with memory_monitor():
        # Document processing logic
        result = await process_large_document(file)
        return result
```

---

## Conclusion

The CogniVox Agentic Backend represents a modern, production-ready API service that combines cutting-edge FastAPI features with comprehensive service integration, security, and performance optimization. This technical documentation provides the foundation for understanding, developing, and maintaining the backend component of the CogniVox ecosystem.

### Key Technical Achievements
- **UV Package Manager Integration**: Revolutionary setup speed with 10-100x faster dependency installation
- **Comprehensive Health Monitoring**: Real-time service discovery and dependency validation
- **Enhanced Security Framework**: JWT authentication, RBAC, rate limiting, and comprehensive input validation
- **Timezone Management**: Complete timezone awareness with client-side formatting support
- **Service Integration**: Robust integration with Memory and GraphRAG services with retry logic
- **Performance Optimization**: Database connection pooling, caching, and background task processing

### Production Readiness Features
- **Graceful Shutdown**: Clean service termination with state preservation
- **Error Handling**: Comprehensive error handling with detailed logging and recovery strategies
- **Monitoring Integration**: Built-in metrics collection and health check endpoints
- **Scalability**: Async operations, connection pooling, and horizontal scaling support
- **Security**: Multiple layers of security with authentication, authorization, and input validation

For detailed information about other system components, refer to:
- [Complete System Documentation](./CogniVox_Complete_System_Documentation.md)
- [Frontend Documentation](./CogniVox_Agentic_Frontend_Technical_Documentation.md)
- [Memory Service Documentation](./CogniVox_Agentic_Memory_Technical_Documentation.md)
- [GraphRAG Documentation](./CogniVox_Agentic_GraphRAG_Technical_Documentation.md) 