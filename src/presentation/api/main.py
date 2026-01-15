"""
FastAPI Application

Main application entry point for the Transformas Medical Transport Agent API.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ...infrastructure.config.settings import settings
from ...agent.langgraph_orchestrator import LangGraphOrchestrator
from ...infrastructure.persistence.redis.client import create_redis_client
from ...infrastructure.persistence.redis.session_store import RedisSessionStore
from ...infrastructure.persistence.excel_service import ExcelOutboundService

# Import routers
from .v1.endpoints import conversation, health, calls


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="API para agente conversacional de coordinación de transporte médico",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(conversation.router, prefix=settings.API_PREFIX)
    app.include_router(calls.router, prefix=settings.API_PREFIX)

    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        # Initialize Excel service first (if path is provided)
        excel_service = None
        if settings.EXCEL_PATH and os.path.exists(settings.EXCEL_PATH):
            try:
                excel_service = ExcelOutboundService(
                    excel_path=settings.EXCEL_PATH,
                    backup_folder=settings.EXCEL_BACKUP_FOLDER
                )
                print(f" Excel service initialized: {settings.EXCEL_PATH}")
            except Exception as e:
                print(f"  Warning: Could not initialize Excel service: {str(e)}")
                excel_service = None
        else:
            if settings.EXCEL_PATH:
                print(f"  Warning: Excel file not found at {settings.EXCEL_PATH}")

        app.state.excel_service = excel_service

        # Initialize Redis and session store
        redis_client = create_redis_client(settings)
        app.state.redis = redis_client
        app.state.session_store = RedisSessionStore(redis_client, ttl_seconds=settings.SESSION_TTL_SECONDS)

        # Initialize LangGraph orchestrator
        app.state.call_orchestrator = LangGraphOrchestrator(
            settings=settings,
            store=app.state.session_store,
            excel_service=excel_service
        )

        print(f" {settings.APP_NAME} v{settings.APP_VERSION} starting...")
        print(f" Environment: {settings.ENVIRONMENT}")
        print(f" Agent: {settings.AGENT_NAME}")
        print(f" Company: {settings.COMPANY_NAME}")
        print(f" Orchestrator: LangGraph (LLM-based)")
        print(f" API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler"""
        redis_client = getattr(app.state, "redis", None)
        if redis_client is not None:
            await redis_client.close()
        print(f" {settings.APP_NAME} shutting down...")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
