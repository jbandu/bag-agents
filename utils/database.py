"""
Database connection management for Neon (PostgreSQL) and Neo4j.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from neo4j import GraphDatabase, AsyncGraphDatabase
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class DatabaseConfig(BaseSettings):
    """Database configuration from environment variables."""

    # Option 1: Use full DATABASE_URL
    database_url: Optional[str] = None

    # Option 2: Use individual Neon PostgreSQL settings
    neon_db_host: Optional[str] = None
    neon_db_port: int = 5432
    neon_db_name: Optional[str] = None
    neon_db_user: Optional[str] = None
    neon_db_password: Optional[str] = None
    neon_db_sslmode: str = "require"

    # Neo4j (optional)
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_postgres_params(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection parameters.

        Parses DATABASE_URL if provided, otherwise uses individual settings.

        Returns:
            Dictionary with connection parameters
        """
        # If DATABASE_URL is provided, parse it
        if self.database_url:
            parsed = urlparse(self.database_url)
            return {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/').split('?')[0],
                'user': parsed.username,
                'password': parsed.password,
                'sslmode': 'require' if 'sslmode=require' in self.database_url else self.neon_db_sslmode
            }

        # Otherwise use individual settings
        return {
            'host': self.neon_db_host,
            'port': self.neon_db_port,
            'database': self.neon_db_name,
            'user': self.neon_db_user,
            'password': self.neon_db_password,
            'sslmode': self.neon_db_sslmode
        }


class DatabaseManager:
    """
    Manages connections to both Neon (PostgreSQL) and Neo4j databases.

    Provides connection pooling and utilities for querying both databases.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connections.

        Args:
            config: Database configuration (loaded from env if not provided)
        """
        self.config = config or DatabaseConfig()
        self.pg_pool: Optional[SimpleConnectionPool] = None
        self.neo4j_driver = None
        self.logger = logging.getLogger(__name__)

    def connect_postgres(self, min_connections: int = 1, max_connections: int = 10):
        """
        Create PostgreSQL connection pool.

        Args:
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        try:
            params = self.config.get_postgres_params()
            self.pg_pool = SimpleConnectionPool(
                min_connections,
                max_connections,
                **params
            )
            self.logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise

    def connect_neo4j(self):
        """Create Neo4j driver connection (optional)."""
        # Skip if Neo4j credentials not provided
        if not all([self.config.neo4j_uri, self.config.neo4j_user, self.config.neo4j_password]):
            self.logger.warning("Neo4j credentials not provided, skipping Neo4j connection")
            return

        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            self.logger.info("Neo4j driver created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create Neo4j driver: {e}")
            # Don't raise - Neo4j is optional
            self.logger.warning("Continuing without Neo4j support")

    def close_all(self):
        """Close all database connections."""
        if self.pg_pool:
            self.pg_pool.closeall()
            self.logger.info("PostgreSQL connection pool closed")

        if self.neo4j_driver:
            self.neo4j_driver.close()
            self.logger.info("Neo4j driver closed")

    @asynccontextmanager
    async def get_pg_connection(self):
        """
        Context manager for PostgreSQL connections.

        Yields:
            PostgreSQL connection from the pool
        """
        if not self.pg_pool:
            raise ValueError("PostgreSQL pool not initialized. Call connect_postgres() first.")

        conn = self.pg_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"PostgreSQL transaction error: {e}")
            raise
        finally:
            self.pg_pool.putconn(conn)

    async def query_postgres(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False
    ) -> Any:
        """
        Execute a PostgreSQL query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: If True, fetch only one row

        Returns:
            Query results (list of tuples or single tuple if fetch_one=True)
        """
        async with self.get_pg_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()

    async def execute_postgres(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> int:
        """
        Execute a PostgreSQL INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        async with self.get_pg_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount

    async def query_neo4j(
        self,
        cypher_query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Neo4j Cypher query.

        Args:
            cypher_query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        if not self.neo4j_driver:
            raise ValueError("Neo4j driver not initialized. Call connect_neo4j() first.")

        async with self.neo4j_driver.session() as session:
            result = await session.run(cypher_query, parameters or {})
            records = await result.data()
            return records

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of database connections.

        Returns:
            Dictionary with health status for each database
        """
        health = {
            "postgres": False,
            "neo4j": False
        }

        # Check PostgreSQL
        try:
            await self.query_postgres("SELECT 1", fetch_one=True)
            health["postgres"] = True
        except Exception as e:
            self.logger.error(f"PostgreSQL health check failed: {e}")

        # Check Neo4j
        try:
            await self.query_neo4j("RETURN 1")
            health["neo4j"] = True
        except Exception as e:
            self.logger.error(f"Neo4j health check failed: {e}")

        return health


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create the singleton DatabaseManager instance.

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.connect_postgres()
        _db_manager.connect_neo4j()
    return _db_manager
