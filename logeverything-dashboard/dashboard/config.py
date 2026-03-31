"""
Dashboard Configuration
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings

from .connections import ApiConnection, ConnectionsStore, LocalConnection


class Settings(BaseSettings):
    """Dashboard configuration settings."""

    # Data source configuration
    monitoring_data_dir: str = "../sample_monitoring_data"
    api_url: Optional[str] = None

    # Dashboard configuration
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 3000
    debug: bool = True

    # UI configuration
    page_title: str = "LogEverything Dashboard"
    theme: str = "dark"
    refresh_interval: int = 5  # seconds
    websocket_update_interval: int = 5  # seconds

    # Connections configuration
    connections_file: str = "connections.json"

    # Alias host/port for uvicorn compatibility
    @property
    def host(self) -> str:
        return self.dashboard_host

    @property
    def port(self) -> int:
        return self.dashboard_port

    class Config:
        env_file = ".env"
        env_prefix = "DASHBOARD_"


class ConnectionManager:
    """Manager for LogEverything connections."""

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.store = ConnectionsStore()
        self._load_connections()

    def _get_connections_path(self) -> Path:
        """Get the path to the connections file."""
        # Store in user data directory
        data_dir = Path.home() / ".logeverything-dashboard"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / self.settings.connections_file

    def _load_connections(self) -> None:
        """Load connections from file."""
        file_path = self._get_connections_path()

        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.store = ConnectionsStore.parse_obj(data)
            except Exception as e:
                print(f"Error loading connections: {e}")
                self._create_default_connection()
        else:
            self._create_default_connection()

    def _create_default_connection(self) -> None:
        """Create default connection from environment settings."""
        # Create a default local connection from settings
        connection_id = str(uuid.uuid4())
        connection = LocalConnection(
            id=connection_id,
            name="Default Connection",
            description="Default local connection from environment settings",
            data_dir=self.settings.monitoring_data_dir,
        )

        self.store.add_connection(connection)
        self.store.active_connection_id = connection_id

        # Save to file
        self._save_connections()

    def _save_connections(self) -> None:
        """Save connections to file."""
        file_path = self._get_connections_path()

        try:
            with open(file_path, "w") as f:
                # Convert to dict first and then use standard json module
                import json

                json_data = json.dumps(self.store.dict(), indent=2)
                f.write(json_data)
        except Exception as e:
            print(f"Error saving connections: {e}")

    def get_connections(self) -> List[Dict[str, Any]]:
        """Get all connections."""
        return [conn.dict() for conn in self.store.connections]

    def get_active_connection(self) -> Optional[Dict[str, Any]]:
        """Get the active connection."""
        conn = self.store.get_active_connection()
        return conn.dict() if conn else None

    def add_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new connection."""
        # Generate ID if not provided
        if "id" not in connection_data:
            connection_data["id"] = str(uuid.uuid4())

        # Create the appropriate connection type
        conn_type = connection_data.get("type", "local")

        if conn_type == "api":
            connection = ApiConnection(**connection_data)
        else:
            # Default to local
            connection = LocalConnection(**connection_data)

        # Add to store
        self.store.add_connection(connection)
        self._save_connections()

        return connection.dict()

    def update_connection(
        self, connection_id: str, connection_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing connection."""
        # Ensure ID matches
        connection_data["id"] = connection_id

        # Get existing connection
        existing = self.store.get_connection(connection_id)
        if not existing:
            return None

        # Create updated connection
        conn_type = connection_data.get("type", existing.type)

        if conn_type == "api":
            connection = ApiConnection(**connection_data)
        else:
            # Default to local
            connection = LocalConnection(**connection_data)

        # Update in store
        self.store.add_connection(connection)
        self._save_connections()

        return connection.dict()

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection."""
        result = self.store.remove_connection(connection_id)
        if result:
            self._save_connections()
        return result

    def set_active_connection(self, connection_id: str) -> bool:
        """Set the active connection."""
        result = self.store.set_active_connection(connection_id)
        if result:
            self._save_connections()
        return result


def get_settings() -> Settings:
    """Get dashboard settings."""
    return Settings()


def get_connection_manager() -> ConnectionManager:
    """Get connection manager singleton."""
    settings = get_settings()
    return ConnectionManager(settings)


def get_settings() -> Settings:
    """Get dashboard settings."""
    return Settings()
