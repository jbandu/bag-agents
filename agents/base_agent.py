"""
Base Agent Class

Provides a standard interface and common functionality for all agents.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from prometheus_client import Counter, Histogram


class BaseAgent(ABC):
    """
    Base class for all baggage operations agents.

    Provides:
    - Standard interface (execute method)
    - Logging capabilities
    - Error handling
    - Performance metrics
    - Common utilities
    """

    # Prometheus metrics
    agent_requests = Counter(
        'agent_requests_total',
        'Total number of agent requests',
        ['agent_name', 'status']
    )

    agent_duration = Histogram(
        'agent_duration_seconds',
        'Time spent processing agent requests',
        ['agent_name']
    )

    def __init__(
        self,
        agent_name: str,
        llm_client: Any = None,
        db_connection: Any = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_name: Unique identifier for the agent
            llm_client: LLM client instance (Claude/OpenAI)
            db_connection: Database connection pool
            config: Additional configuration parameters
        """
        self.agent_name = agent_name
        self.llm_client = llm_client
        self.db_connection = db_connection
        self.config = config or {}

        # Set up logging
        self.logger = logging.getLogger(f"agents.{agent_name}")
        self.logger.setLevel(logging.INFO)

        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent.

        This method must be implemented by all concrete agent classes.

        Args:
            input_data: Dictionary containing input parameters for the agent

        Returns:
            Dictionary containing the agent's output

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper method that adds logging, error handling, and metrics.

        Args:
            input_data: Dictionary containing input parameters

        Returns:
            Dictionary containing execution results and metadata
        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting execution for {self.agent_name}")
            self.logger.debug(f"Input data: {input_data}")

            # Execute the agent's main logic
            result = await self.execute(input_data)

            # Add metadata
            duration = time.time() - start_time
            result['metadata'] = {
                'agent_name': self.agent_name,
                'execution_time': duration,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'success'
            }

            # Record metrics
            self.agent_requests.labels(
                agent_name=self.agent_name,
                status='success'
            ).inc()
            self.agent_duration.labels(
                agent_name=self.agent_name
            ).observe(duration)

            self.logger.info(
                f"Completed execution for {self.agent_name} in {duration:.2f}s"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            self.agent_requests.labels(
                agent_name=self.agent_name,
                status='error'
            ).inc()

            self.logger.error(
                f"Error in {self.agent_name}: {str(e)}",
                exc_info=True
            )

            return {
                'error': str(e),
                'error_type': type(e).__name__,
                'metadata': {
                    'agent_name': self.agent_name,
                    'execution_time': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'error'
                }
            }

    def validate_input(
        self,
        input_data: Dict[str, Any],
        required_fields: list
    ) -> None:
        """
        Validate that required fields are present in input data.

        Args:
            input_data: Input dictionary to validate
            required_fields: List of required field names

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [
            field for field in required_fields
            if field not in input_data
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    async def query_database(self, query: str, params: Optional[tuple] = None) -> Any:
        """
        Execute a database query.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Query results
        """
        if not self.db_connection:
            raise ValueError("No database connection available")

        self.logger.debug(f"Executing query: {query}")

        # Implementation will depend on actual DB connection type
        # This is a placeholder
        async with self.db_connection.cursor() as cursor:
            await cursor.execute(query, params or ())
            return await cursor.fetchall()

    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Make a call to the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for the LLM

        Returns:
            LLM response text
        """
        if not self.llm_client:
            raise ValueError("No LLM client available")

        self.logger.debug(f"Calling LLM with prompt: {prompt[:100]}...")

        # This is a generic implementation
        # Specific implementations will vary by LLM provider
        return await self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
