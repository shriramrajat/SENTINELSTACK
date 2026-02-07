from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sentinelstack.config import settings

# 1. Create the Async Engine
# echo=True means all SQL queries will be logged to the console (good for debugging)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True if you want to see SQL queries
    future=True
)

# 2. Create the Session Factory
# This is what we use to talk to the DB in every request
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 3. Base Class for Models
# All our models will inherit from this
Base = declarative_base()

# 4. Dependency Injection
# This functions gives a DB session to a FastAPI route and closes it afterwards 
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()