# Architecture Documentation

## Workflow Sequence (LangGraph)
The core intelligence of the OS is driven by a Multi-Agent Supervisor pattern implemented via LangGraph.

```mermaid
sequenceDiagram
    participant User
    participant Context Builder
    participant Supervisor
    participant Research Agent
    participant Math Agent
    participant Writing Agent
    participant Tool Executor
    participant Reflection
    participant Memory Extractor

    User->>Context Builder: Submit Query
    Context Builder->>Supervisor: Build Context & State
    
    loop Task Delegation
        Supervisor->>Research Agent: Delegate Search Task
        Research Agent->>Tool Executor: Execute Drive Search
        Tool Executor-->>Research Agent: Return Results
        Research Agent-->>Supervisor: Summarize Findings
        
        Supervisor->>Math Agent: Delegate Calculation
        Math Agent->>Tool Executor: Execute Calculator
        Tool Executor-->>Math Agent: Return Results
        Math Agent-->>Supervisor: Summarize Findings
    end
    
    Supervisor->>Writing Agent: Delegate Formatting
    Writing Agent-->>Reflection: Complete Draft
    
    Reflection->>Reflection: Grade Hallucinations & Groundedness
    
    alt Needs Revision
        Reflection-->>Writing Agent: Retry
    else Approved
        Reflection->>Memory Extractor: Final Answer
    end
    
    Memory Extractor->>Memory Extractor: Score Importance (>= 0.8)
    Memory Extractor-->>User: Return Output
```

## Database Schema (pgvector)
```mermaid
erDiagram
    LongTermMemory {
        int id PK
        uuid user_id
        text fact
        vector embedding
        timestamp created_at
    }
    
    ConversationMessage {
        int id PK
        uuid conversation_id
        uuid user_id
        varchar role
        text content
        jsonb metadata
        timestamp created_at
    }

    ConversationMessage }o--|| LongTermMemory : "Informs"
```

## Deployment Topology
```mermaid
graph TD
    Client[Web Browser / CLI] -->|HTTPS SSE| API[FastAPI Server]
    API -->|LLM Calls| Provider[Gemini / Claude / OpenAI]
    API -->|TCP/5432| DB[(PostgreSQL + pgvector)]
    
    subgraph Docker Network
        API
        DB
    end
```
