"""
Connection management routes for LogEverything Dashboard
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from .config import ConnectionManager, get_connection_manager
from .services import MonitoringService

# Create router
router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.get("/")
async def list_connections(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """List all connections."""
    return {
        "connections": connection_manager.get_connections(),
        "active": connection_manager.get_active_connection(),
    }


@router.get("/active")
async def get_active_connection(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    """Get the active connection."""
    active = connection_manager.get_active_connection()
    if not active:
        raise HTTPException(status_code=404, detail="No active connection found")

    return active


@router.post("/")
async def create_connection(
    connection_data: Dict[str, Any],
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    """Create a new connection."""
    try:
        result = connection_manager.add_connection(connection_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{connection_id}")
async def update_connection(
    connection_id: str,
    connection_data: Dict[str, Any],
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    """Update an existing connection."""
    try:
        result = connection_manager.update_connection(connection_id, connection_data)
        if not result:
            raise HTTPException(status_code=404, detail="Connection not found")

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{connection_id}")
async def delete_connection(
    connection_id: str, connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """Delete a connection."""
    success = connection_manager.remove_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {"success": True}


@router.post("/{connection_id}/activate")
async def activate_connection(
    connection_id: str,
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    monitoring_service: MonitoringService = Depends(lambda: MonitoringService(None)),
):
    """Set a connection as active."""
    success = await monitoring_service.switch_connection(connection_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Connection not found or could not be activated"
        )

    return {"success": True, "active": connection_manager.get_active_connection()}


@router.post("/test")
async def test_connection(
    connection_data: Dict[str, Any],
    monitoring_service: MonitoringService = Depends(lambda: MonitoringService(None)),
):
    """Test a connection configuration."""
    try:
        # Test the connection
        success, message = await monitoring_service.test_connection(connection_data)

        if success:
            return {"success": True, "message": message or "Connection successful"}
        else:
            return {"success": False, "message": message or "Connection failed"}
    except Exception as e:
        return {"success": False, "message": f"Connection test error: {str(e)}"}
