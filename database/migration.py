import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from sqlalchemy import text
from database.postgres import engine, Base
from database.models import Tenant, User, Document, Chunk, ConversationMessage, LongTermMemory
from utils.logger import logger

async def run_migrations():
    logger.info("Starting database migrations...")
    try:
        async with engine.begin() as conn:
            # Create the pgvector extension if it doesn't exist
            logger.info("Ensuring pgvector extension is enabled...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Create all tables defined in Base
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Create default tenant if not exists
            logger.info("Ensuring default tenant exists...")
            await conn.execute(text("INSERT INTO tenants (id, name) VALUES (1, 'Default Tenant') ON CONFLICT (id) DO NOTHING"))
            
            # Ensure tenant_id columns in all tables are nullable and default to 1
            logger.info("Ensuring tenant_id columns allow nulls and default to 1...")
            for table in ["conversation_messages", "long_term_memories", "documents", "chunks"]:
                await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP NOT NULL"))
                await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT 1"))
            
        logger.info("Database migrations completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migrations())
