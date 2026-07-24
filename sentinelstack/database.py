from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sentinelstack.config import settings

# Detect if SSL is required.
# Supabase and most cloud Postgres providers mandate SSL connections.
# We enable it when the host is a known cloud provider or ENV is production
# and the host is not localhost/127.0.0.1.
_is_cloud_db = (
    "supabase.co" in settings.DATABASE_URL
    or (
        settings.ENV == "production"
        and "localhost" not in settings.DATABASE_URL
        and "127.0.0.1" not in settings.DATABASE_URL
    )
)

# 1. Create the Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # asyncpg requires ssl=True to be passed as a connect_arg, not in the URL.
    # We also MUST disable statement caching because Supabase PgBouncer (Transaction Pooler)
    # does not support prepared statements properly.
    connect_args={
        "ssl": "require" if _is_cloud_db else False,
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

# 2. Create the Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 3. Base Class for Models
Base = declarative_base()

# 4. Dependency Injection
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()