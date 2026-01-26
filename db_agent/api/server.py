"""
SQL Tuning AI Agent - FastAPI Service
RESTful API服务
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime
from db_agent.core import SQLTuningAgent
from db_agent.llm import LLMClientFactory
from db_agent.i18n import t
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SQL Tuning AI Agent API",
    description="PostgreSQL性能调优AI Agent RESTful API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Agent实例存储
agents: Dict[str, SQLTuningAgent] = {}

# Pydantic模型
class AgentConfig(BaseModel):
    """Agent配置"""
    db_host: str = Field(default="localhost", description="数据库主机")
    db_port: int = Field(default=5432, description="数据库端口")
    db_name: str = Field(..., description="数据库名")
    db_user: str = Field(..., description="数据库用户")
    db_password: str = Field(..., description="数据库密码")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key(如果不提供则使用环境变量)")

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    config: AgentConfig

class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    created_at: str
    message_count: int

class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    response: str
    timestamp: str

# API端点

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "SQL Tuning AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create_session": "POST /api/v1/sessions",
            "chat": "POST /api/v1/chat",
            "get_sessions": "GET /api/v1/sessions",
            "get_history": "GET /api/v1/sessions/{session_id}/history",
            "delete_session": "DELETE /api/v1/sessions/{session_id}"
        }
    }

@app.post("/api/v1/sessions", response_model=SessionInfo)
async def create_session(request: CreateSessionRequest):
    """
    创建新的Agent会话

    返回session_id,后续chat需要使用此ID
    """
    try:
        # 生成session ID
        session_id = str(uuid.uuid4())

        # API Key
        api_key = request.config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=t("api_no_api_key")
            )

        # 数据库配置
        db_config = {
            "host": request.config.db_host,
            "port": request.config.db_port,
            "database": request.config.db_name,
            "user": request.config.db_user,
            "password": request.config.db_password
        }

        # 创建LLM客户端
        llm_client = LLMClientFactory.create(
            provider="claude",
            api_key=api_key
        )

        # 创建Agent
        agent = SQLTuningAgent(
            llm_client=llm_client,
            db_config=db_config
        )

        # 测试数据库连接
        test_result = agent.db_tools.execute_safe_query("SELECT 1;")
        if test_result["status"] != "success":
            raise HTTPException(
                status_code=500,
                detail=t("api_db_connection_failed", error=test_result.get('error'))
            )

        # 存储Agent
        agents[session_id] = agent

        logger.info(f"创建会话: {session_id}")

        return SessionInfo(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            message_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与Agent对话

    发送消息并获取Agent的响应
    """
    try:
        # 获取Agent
        agent = agents.get(request.session_id)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=t("api_session_not_found", session_id=request.session_id)
            )

        logger.info(f"会话 {request.session_id} 收到消息")

        # Agent处理
        response = agent.chat(request.message)

        return ChatResponse(
            session_id=request.session_id,
            response=response,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    列出所有活跃会话
    """
    sessions = []
    for session_id, agent in agents.items():
        history = agent.get_conversation_history()
        sessions.append(SessionInfo(
            session_id=session_id,
            created_at="unknown",  # 简化实现,未存储创建时间
            message_count=len([m for m in history if m["role"] == "user"])
        ))

    return sessions

@app.get("/api/v1/sessions/{session_id}/history")
async def get_history(session_id: str):
    """
    获取会话历史
    """
    agent = agents.get(session_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=t("api_session_not_found", session_id=session_id)
        )

    history = agent.get_conversation_history()

    # 简化历史记录(只返回用户和文本响应)
    simplified_history = []
    for message in history:
        if message["role"] == "user" and isinstance(message["content"], str):
            simplified_history.append({
                "role": "user",
                "content": message["content"]
            })
        elif message["role"] == "assistant" and isinstance(message["content"], str):
            simplified_history.append({
                "role": "assistant",
                "content": message["content"]
            })

    return {
        "session_id": session_id,
        "history": simplified_history
    }

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    if session_id in agents:
        del agents[session_id]
        logger.info(f"删除会话: {session_id}")
        return {"message": t("api_session_deleted"), "session_id": session_id}
    else:
        raise HTTPException(
            status_code=404,
            detail=t("api_session_not_found", session_id=session_id)
        )

@app.post("/api/v1/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """
    重置会话历史
    """
    agent = agents.get(session_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=t("api_session_not_found", session_id=session_id)
        )

    agent.reset_conversation()
    logger.info(f"重置会话: {session_id}")

    return {"message": t("api_session_reset"), "session_id": session_id}

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "active_sessions": len(agents),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    logger.info(f"启动API服务: port={port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
