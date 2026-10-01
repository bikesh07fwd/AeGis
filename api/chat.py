from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import get_db
from retrieval.semantic import semantic_search
import uuid
from graph.workflow import app as graph_app
from api.auth import verify_api_key
from fastapi.responses import StreamingResponse
import json
from langgraph.errors import GraphRecursionError

# Hard safety bound on agent-loop iterations (supervisor<->worker hops).
# Prevents a non-converging supervisor loop from running unbounded.
RECURSION_LIMIT = 25

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    chunk_text: str

@router.post("/search", response_model=list[SearchResult])
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search over indexed documents.
    Takes a query string and returns the most relevant chunks.
    """
    chunks = await semantic_search(query=request.query, db=db, limit=request.limit)
    
    results = [
        SearchResult(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            chunk_text=chunk.chunk_text
        )
        for chunk in chunks
    ]
    return results

class GenerateRequest(BaseModel):
    question: str
    conversation_id: str
    user_id: str

class GenerateResponse(BaseModel):
    answer: str
    trace_id: str

@router.post("/generate", response_model=GenerateResponse)
async def generate_answer(request: GenerateRequest):
    """
    Generate an answer using the LangGraph orchestrated RAG pipeline.
    """
    trace_id = str(uuid.uuid4())
    
    initial_state = {
        "conversation_id": request.conversation_id,
        "user_id": request.user_id,
        "question": request.question,
        "trace_id": trace_id,
        "query_plan": None,
        "recent_messages": [],
        "semantic_memories": [],
        "retrieved_chunks": [],
        "formatted_context": "",
        "answer": "",
        "extracted_facts": [],
        "messages": [],
        "metadata": {},
        "memory": {},
        "tool_calls": [],
        "errors": [],
        "revision_count": 0,
        "reflection_feedback": None,
        "reflection_status": None,
        "reflection_metrics": None,
        "next_agent": None,
        "node_latencies": {},
        "total_tokens": 0,
        "estimated_cost": 0.0
    }
    
    config = {"recursion_limit": RECURSION_LIMIT}

    try:
        result = await graph_app.ainvoke(initial_state, config=config)
    except GraphRecursionError:
        # The agent loop exhausted its iteration budget without reaching FINISH.
        # Return a controlled application-level failure: never a raw 500
        # traceback, and never a partial answer presented as success.
        from utils.logger import logger
        logger.error(f"Recursion limit exceeded for trace_id={trace_id} (limit={RECURSION_LIMIT})")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "recursion_limit_exceeded",
                "message": "Agent workflow exceeded the maximum reasoning budget without reaching a final answer.",
                "trace_id": trace_id,
                "max_iterations": RECURSION_LIMIT,
            },
        )
    except Exception as e:
        from utils.logger import logger
        logger.error(f"Error in generate_answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal AI Engine Error: {str(e)}")
    
    return GenerateResponse(
        answer=result.get("answer", ""),
        trace_id=trace_id
    )

@router.post("/stream")
async def chat_stream(request: GenerateRequest):
    """
    Streams the execution of the LangGraph in real-time using Server-Sent Events (SSE).
    """
    trace_id = str(uuid.uuid4())
    initial_state = {
        "conversation_id": request.conversation_id,
        "user_id": request.user_id,
        "question": request.question,
        "trace_id": trace_id,
        "query_plan": None,
        "recent_messages": [],
        "semantic_memories": [],
        "retrieved_chunks": [],
        "formatted_context": "",
        "answer": "",
        "extracted_facts": [],
        "messages": [],
        "metadata": {},
        "memory": {},
        "tool_calls": [],
        "errors": [],
        "revision_count": 0,
        "reflection_feedback": None,
        "reflection_status": None,
        "reflection_metrics": None,
        "next_agent": None,
        "node_latencies": {},
        "total_tokens": 0,
        "estimated_cost": 0.0
    }
    
    config = {"recursion_limit": RECURSION_LIMIT}

    async def event_generator():
        try:
            async for step in graph_app.astream(initial_state, config=config):
                for node, state_update in step.items():
                    msg = "Processing..."
                    if node == "query_planner":
                        msg = "Planning execution strategy..."
                    elif node == "supervisor":
                        msg = "Supervisor analyzing..."
                    elif node == "research_agent":
                        msg = "Research Agent gathering data..."
                    elif node == "math_agent":
                        msg = "Math Agent crunching numbers..."
                    elif node == "writing_agent":
                        msg = "Writing Agent drafting..."
                    elif node == "tool_executor":
                        msg = "Executing external tools..."
                    elif node == "reflection":
                        msg = "Reflecting and grading response..."
                    elif node == "memory_extractor":
                        msg = "Extracting persistent facts..."
                    
                    data = json.dumps({"status": msg, "node": node})
                    yield f"data: {data}\n\n"
                    
            yield f"data: {json.dumps({'status': 'Done', 'node': 'END'})}\n\n"
        except GraphRecursionError:
            yield f"data: {json.dumps({'status': 'error', 'error': 'recursion_limit_exceeded', 'message': 'Agent workflow exceeded the maximum reasoning budget without reaching a final answer.', 'trace_id': trace_id, 'node': 'END'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
