"""
Main FastAPI application for LogEverything Dashboard
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .config import get_connection_manager, get_settings
from .connection_routes import router as connection_router
from .services import MonitoringService, WebSocketManager

# Initialize FastAPI app
app = FastAPI(
    title="LogEverything Dashboard",
    description="Real-time monitoring dashboard for LogEverything systems",
    version=__version__,
)

# Include connection routes
app.include_router(connection_router)

# Get settings
settings = get_settings()

# Initialize services
monitoring_service = MonitoringService(settings)
websocket_manager = WebSocketManager()

# Setup static files and templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


def _page_context(request: Request) -> Dict[str, Any]:
    """Build common template context for all pages."""
    connection_manager = get_connection_manager()
    active_connection = connection_manager.get_active_connection()
    return {
        "request": request,
        "settings": settings,
        "active_connection": active_connection,
    }


@app.get("/", response_class=HTMLResponse)
async def overview_page(request: Request):
    """Overview page — summary cards, charts, quick analytics."""
    return templates.TemplateResponse("overview.html", _page_context(request))


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs page — filterable log table with flat/tree view toggle."""
    return templates.TemplateResponse("logs.html", _page_context(request))


@app.get("/operations", response_class=HTMLResponse)
async def operations_page(request: Request):
    """Operations page — operation analytics and table."""
    return templates.TemplateResponse("operations.html", _page_context(request))


@app.get("/system", response_class=HTMLResponse)
async def system_page(request: Request):
    """System page — detailed system metrics and trends."""
    return templates.TemplateResponse("system.html", _page_context(request))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}


@app.get("/api/system-stats")
async def get_system_stats():
    """Get current system statistics"""
    try:
        stats = await monitoring_service.get_system_stats()
        return stats.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring-stats")
async def get_monitoring_stats():
    """Get monitoring statistics"""
    try:
        stats = await monitoring_service.get_monitoring_stats()
        return stats.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/operations")
async def get_operations(limit: int = 50, offset: int = 0):
    """Get recent operations"""
    try:
        operations = await monitoring_service.get_operations(limit=limit, offset=offset)
        return {"operations": [op.dict() for op in operations]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None,
    correlation_id: Optional[str] = None,
    source: Optional[str] = None,
):
    """Get recent log entries with optional filters."""
    try:
        logs = await monitoring_service.get_logs(
            limit=limit, level=level, correlation_id=correlation_id, source=source
        )
        return {"logs": [log.dict() if hasattr(log, "dict") else log for log in logs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/logs")
async def ingest_logs(request: Request):
    """Receive batched logs from remote transport handlers.

    Expected JSON body::

        {"logs": [...], "source": "worker-1"}
    """
    try:
        body = await request.json()
        logs = body.get("logs", [])
        source = body.get("source", "unknown")

        if not logs:
            return {"accepted": 0}

        # Store via service
        count = await monitoring_service.store_ingested_logs(logs, source)

        # Broadcast to connected WebSockets for real-time display
        try:
            await websocket_manager.broadcast_json(
                {
                    "type": "log_batch",
                    "logs": logs[-10:],  # send last 10 to avoid flooding
                    "source": source,
                }
            )
        except Exception:
            pass  # Don't fail ingestion if WS broadcast fails

        return {"accepted": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/trace/{correlation_id}")
async def get_log_trace(correlation_id: str):
    """Get all log entries for a specific correlation / request ID."""
    try:
        logs = await monitoring_service.get_logs_by_correlation(correlation_id)
        return {"correlation_id": correlation_id, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# HTMX Partial Endpoints
@app.get("/partials/system-stats", response_class=HTMLResponse)
async def system_stats_partial(request: Request):
    """HTMX partial for system stats"""
    try:
        stats = await monitoring_service.get_system_stats()
        return templates.TemplateResponse(
            "partials/system_stats.html", {"request": request, "stats": stats}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/partials/monitoring-stats", response_class=HTMLResponse)
async def monitoring_stats_partial(request: Request):
    """HTMX partial for monitoring stats"""
    try:
        stats = await monitoring_service.get_monitoring_stats()
        return templates.TemplateResponse(
            "partials/monitoring_stats.html", {"request": request, "stats": stats}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/partials/operations", response_class=HTMLResponse)
async def operations_partial(
    request: Request,
    limit: int = 10,
    hours: Optional[int] = None,
    operation_name: Optional[str] = None,
):
    """HTMX partial for operations list"""
    try:
        operations = await monitoring_service.get_operations(
            limit=limit, hours=hours, operation_name=operation_name
        )
        return templates.TemplateResponse(
            "partials/operations_list.html", {"request": request, "operations": operations}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/partials/logs", response_class=HTMLResponse)
async def logs_partial(
    request: Request,
    limit: int = 25,
    offset: int = 0,
    level: Optional[str] = None,
    correlation_id: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    hours: Optional[int] = None,
):
    """HTMX partial for logs list with optional filters and pagination"""
    try:
        # Fetch all matching logs (up to a high cap) for total count
        all_logs = await monitoring_service.get_logs(
            limit=10000,
            level=level,
            correlation_id=correlation_id,
            source=source,
            search=q,
            hours=hours,
        )
        total_count = len(all_logs)

        # Apply pagination (limit=0 means ALL)
        if limit > 0:
            logs = all_logs[offset : offset + limit]
        else:
            logs = all_logs

        return templates.TemplateResponse(
            "partials/logs_list.html",
            {
                "request": request,
                "logs": logs,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/api/logs/tree")
async def get_logs_tree_api(
    hours: int = 24,
    execution_id: Optional[str] = None,
    limit: int = 500,
):
    """API endpoint returning hierarchical log tree as JSON."""
    try:
        tree = await monitoring_service.get_logs_tree(
            hours=hours, execution_id=execution_id, limit=limit
        )
        return JSONResponse(content={"tree": tree})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/partials/logs-tree", response_class=HTMLResponse)
async def logs_tree_partial(
    request: Request,
    hours: Optional[int] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    correlation_id: Optional[str] = None,
    q: Optional[str] = None,
):
    """HTMX partial for hierarchical log tree view."""
    try:
        tree = await monitoring_service.get_logs_tree(
            hours=hours or 24,
            level=level,
            source=source,
            correlation_id=correlation_id,
            search=q,
        )
        return templates.TemplateResponse(
            "partials/logs_tree.html",
            {
                "request": request,
                "tree": tree,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "error": str(e),
            },
        )


@app.get("/partials/trace/{correlation_id}", response_class=HTMLResponse)
async def trace_partial(request: Request, correlation_id: str):
    """HTMX partial for request trace timeline"""
    try:
        logs = await monitoring_service.get_logs_by_correlation(correlation_id)
        return templates.TemplateResponse(
            "partials/trace_view.html",
            {
                "request": request,
                "correlation_id": correlation_id,
                "logs": logs,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/partials/logs-stats", response_class=HTMLResponse)
async def logs_stats_partial(request: Request):
    """HTMX partial for logs summary card"""
    try:
        stats = await monitoring_service.get_log_stats()
        return templates.TemplateResponse(
            "partials/logs_stats.html",
            {
                "request": request,
                "stats": stats,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@app.get("/partials/operations-summary-card", response_class=HTMLResponse)
async def operations_summary_card_partial(request: Request):
    """HTMX partial for operations quick-stats card"""
    try:
        summary = await monitoring_service.get_operation_summary(hours=24)
        return templates.TemplateResponse(
            "partials/operations_summary_card.html",
            {
                "request": request,
                "summary": summary,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "error": str(e),
            },
        )


# --- New Analytics & History API routes ---


@app.get("/api/system-metrics-history")
async def system_metrics_history(hours: int = 24, max_points: int = 200):
    """Get historical system metrics for charting."""
    try:
        data = await monitoring_service.get_system_stats_history(hours=hours, max_points=max_points)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system-detail")
async def system_detail():
    """Get detailed system metrics."""
    try:
        data = await monitoring_service.get_detailed_system_stats()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/operations/summary")
async def operations_summary(hours: int = 24):
    """Get aggregated operation analytics."""
    try:
        data = await monitoring_service.get_operation_summary(hours=hours)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/log-level-distribution")
async def log_level_distribution(hours: Optional[int] = None):
    """Get log level distribution counts."""
    try:
        data = await monitoring_service.get_log_level_distribution(hours=hours)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session-info")
async def session_info():
    """Get current session info."""
    try:
        data = monitoring_service.get_session_info()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export")
async def export_data(hours: int = 24):
    """Export all dashboard data as a JSON download."""
    try:
        data = await monitoring_service.get_export_data(hours=hours)
        content = json.dumps(data, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=logeverything-export-{hours}h.json"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- New HTMX partial routes ---


@app.get("/partials/operation-analytics", response_class=HTMLResponse)
async def operation_analytics_partial(request: Request, hours: int = 24):
    """HTMX partial for operation analytics."""
    try:
        summary = await monitoring_service.get_operation_summary(hours=hours)
        return templates.TemplateResponse(
            "partials/operation_analytics.html",
            {
                "request": request,
                "summary": summary,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "error": str(e),
            },
        )


@app.get("/partials/system-detail", response_class=HTMLResponse)
async def system_detail_partial(request: Request):
    """HTMX partial for detailed system metrics."""
    try:
        detail = await monitoring_service.get_detailed_system_stats()
        session = monitoring_service.get_session_info()
        return templates.TemplateResponse(
            "partials/system_detail.html",
            {
                "request": request,
                "detail": detail,
                "session": session,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "error": str(e),
            },
        )


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            system_stats = await monitoring_service.get_system_stats()
            monitoring_stats = await monitoring_service.get_monitoring_stats()

            await websocket_manager.send_personal_message(
                {
                    "type": "stats_update",
                    "system_stats": system_stats,  # Already a dict
                    "monitoring_stats": monitoring_stats,  # Already a dict
                    "timestamp": datetime.utcnow().isoformat(),
                },
                websocket,
            )

            await asyncio.sleep(settings.websocket_update_interval)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)


# Background task for monitoring
@app.on_event("startup")
async def startup_event():
    """Initialize monitoring on startup"""
    print("Starting LogEverything Dashboard...")
    await monitoring_service.initialize()
    print(f"Dashboard starting on {settings.dashboard_host}:{settings.dashboard_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down LogEverything Dashboard...")
    await monitoring_service.cleanup()


if __name__ == "__main__":
    uvicorn.run(
        "dashboard.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )
