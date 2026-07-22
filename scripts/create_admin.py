import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add parent directory to path to import sentinelstack
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sentinelstack.config import settings
from sentinelstack.auth.models import User

async def make_admin(email: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Error: User with email {email} not found.")
            await engine.dispose()
            return
            
        user.role = "admin"
        await session.commit()
        print(f"Success: Promoted {email} to admin!")
    
    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_admin.py <email>")
        sys.exit(1)
    
    asyncio.run(make_admin(sys.argv[1]))
