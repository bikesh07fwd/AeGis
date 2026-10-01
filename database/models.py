from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database.postgres import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    users = relationship("User", back_populates="tenant", cascade="all, delete")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    username = Column(String, unique=True, index=True)
    role = Column(String)  # e.g., "Admin", "Analyst"
    permissions = Column(JSON, default=list)
    
    tenant = relationship("Tenant", back_populates="users")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True, nullable=True, default=1)
    filename = Column(String, index=True)
    content = Column(Text)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True, nullable=True, default=1)
    chunk_text = Column(Text)
    chunk_index = Column(Integer)
    embedding = Column(Vector(768))

    document = relationship("Document", back_populates="chunks")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True, nullable=True, default=1)
    conversation_id = Column(String, index=True)
    message_id = Column(String, unique=True, index=True)
    role = Column(String)  # "user" or "ai"
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    token_count = Column(Integer, nullable=True)
    model_name = Column(String, nullable=True)
    metadata_json = Column(JSON, default={})

class LongTermMemory(Base):
    __tablename__ = "long_term_memories"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True, nullable=True, default=1)
    user_id = Column(String, index=True)
    fact = Column(Text)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(JSON, default={})

