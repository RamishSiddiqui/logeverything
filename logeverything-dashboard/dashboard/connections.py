"""
Connection models for LogEverything Dashboard
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ConnectionConfig(BaseModel):
    """Connection configuration for LogEverything data sources."""

    id: str
    name: str
    type: str = Field(..., description="Type of connection: 'local', 'api', 'database'")
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    enabled: bool = True

    # Common settings
    refresh_interval: int = 5  # seconds

    class Config:
        use_enum_values = True


class LocalConnection(ConnectionConfig):
    """Local file-based connection."""

    type: str = "local"
    data_dir: str
    logs_pattern: str = "*.jsonl"
    database_file: Optional[str] = "monitoring.db"
    session_file: Optional[str] = "session_info.json"


class ApiConnection(ConnectionConfig):
    """Remote API connection."""

    type: str = "api"
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 10  # seconds


class DatabaseConnection(ConnectionConfig):
    """Direct database connection."""

    type: str = "database"
    connection_string: str
    table_prefix: Optional[str] = None
    query_timeout: int = 30  # seconds


class ConnectionsStore(BaseModel):
    """Store for all connections."""

    connections: List[ConnectionConfig] = []
    active_connection_id: Optional[str] = None

    def add_connection(self, connection: ConnectionConfig) -> None:
        """Add a new connection."""
        # Check if connection with same ID already exists
        for i, conn in enumerate(self.connections):
            if conn.id == connection.id:
                # Replace existing connection
                self.connections[i] = connection
                return

        # Add new connection
        self.connections.append(connection)

        # Set as active if it's the first one
        if not self.active_connection_id and self.connections:
            self.active_connection_id = connection.id

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection by ID."""
        for i, conn in enumerate(self.connections):
            if conn.id == connection_id:
                self.connections.pop(i)

                # Update active connection if needed
                if self.active_connection_id == connection_id:
                    self.active_connection_id = self.connections[0].id if self.connections else None

                return True
        return False

    def get_connection(self, connection_id: str) -> Optional[ConnectionConfig]:
        """Get a connection by ID."""
        for conn in self.connections:
            if conn.id == connection_id:
                return conn
        return None

    def set_active_connection(self, connection_id: str) -> bool:
        """Set the active connection."""
        for conn in self.connections:
            if conn.id == connection_id:
                self.active_connection_id = connection_id
                conn.last_accessed = datetime.now()
                return True
        return False

    def get_active_connection(self) -> Optional[ConnectionConfig]:
        """Get the active connection."""
        if not self.active_connection_id:
            return None

        for conn in self.connections:
            if conn.id == self.active_connection_id:
                return conn

        # Reset active connection if not found
        self.active_connection_id = None
        return None
