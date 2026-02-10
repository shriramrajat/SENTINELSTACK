import asyncio
from typing import List, Dict
from sqlalchemy import insert
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.logging.models import RequestLog

# Configuration
BATCH_SIZE = 100
FLUSH_INTERVAL = 5.0 # Seconds

class LogService:
    def __init__(self):
        self.queue: asyncio.Queue[Dict] = asyncio.Queue()
        self.is_running = False

    def log_request(self, log_data: Dict):
        """Non-blocking add to queue"""
        try:
            self.queue.put_nowait(log_data)
        except asyncio.QueueFull:
            # Trade-off: Drop logs if queue makes us crash (documented behavior)
            pass

    async def worker(self):
        """Background task to drain queue"""
        self.is_running = True
        print("INFO:    Log Worker Started")
        
        while self.is_running:
            batch = []
            try:
                # 1. Wait for at least one item (with timeout)
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=FLUSH_INTERVAL)
                    batch.append(item)
                    self.queue.task_done()
                except asyncio.TimeoutError:
                    pass # Continue to flush any remaining items or retry
                
                # 2. Drain whatever else is immediately available up to BATCH_SIZE
                while not self.queue.empty() and len(batch) < BATCH_SIZE:
                    batch.append(self.queue.get_nowait())
                    self.queue.task_done()
                
                # 3. Write Batch to DB
                if batch:
                    await self._flush_batch(batch)
                    
            except Exception as e:
                print(f"ERROR:   Log Worker Failed: {e}")
                # Don't crash the loop, just log error

    async def _flush_batch(self, batch: List[Dict]):
        async with AsyncSessionLocal() as db:
            try:
                # Efficient Bulk Insert
                await db.execute(insert(RequestLog).values(batch))
                await db.commit()
            except Exception as e:
                print(f"ERROR:   DB Insert Failed: {e}")
                await db.rollback()

# Global Instance
log_service = LogService()