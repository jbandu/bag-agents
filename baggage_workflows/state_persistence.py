"""
State Persistence Layer

Handles saving and loading orchestrator state checkpoints to/from database.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .orchestrator_state import OrchestratorState, CheckpointState


logger = logging.getLogger(__name__)


class StatePersistenceManager:
    """
    Manages persistence of orchestrator state to database.

    Provides checkpoint save/load, audit trail, and replay capabilities.
    """

    def __init__(self, db_manager):
        """
        Initialize state persistence manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    async def save_checkpoint(
        self,
        workflow_id: str,
        bag_id: str,
        node: str,
        state: OrchestratorState
    ) -> str:
        """
        Save a state checkpoint to database.

        Args:
            workflow_id: Unique workflow identifier
            bag_id: Bag identifier
            node: Current node name
            state: Complete orchestrator state

        Returns:
            Checkpoint ID
        """
        try:
            checkpoint_id = f"CHK-{workflow_id}-{node}"

            # Serialize state to JSON
            state_json = json.dumps(state, default=str)

            # Insert into database
            query = """
                INSERT INTO bag_state_checkpoints
                (checkpoint_id, workflow_id, bag_id, node, state, timestamp, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checkpoint_id)
                DO UPDATE SET
                    state = EXCLUDED.state,
                    timestamp = EXCLUDED.timestamp,
                    version = bag_state_checkpoints.version + 1
                RETURNING version
            """

            result = await self.db_manager.query_postgres(
                query,
                (
                    checkpoint_id,
                    workflow_id,
                    bag_id,
                    node,
                    state_json,
                    datetime.utcnow(),
                    state.get("bag", {}).get("version", 1)
                ),
                fetch_one=True
            )

            version = result[0] if result else 1

            self.logger.info(
                f"Saved checkpoint {checkpoint_id} (version {version}) for bag {bag_id}"
            )

            return checkpoint_id

        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}")
            raise

    async def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[OrchestratorState]:
        """
        Load a state checkpoint from database.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Orchestrator state or None if not found
        """
        try:
            query = """
                SELECT state, version
                FROM bag_state_checkpoints
                WHERE checkpoint_id = %s
            """

            result = await self.db_manager.query_postgres(
                query,
                (checkpoint_id,),
                fetch_one=True
            )

            if not result:
                self.logger.warning(f"Checkpoint {checkpoint_id} not found")
                return None

            state_json, version = result

            # Deserialize state
            state = json.loads(state_json)

            self.logger.info(f"Loaded checkpoint {checkpoint_id} (version {version})")

            return state

        except Exception as e:
            self.logger.error(f"Error loading checkpoint: {e}")
            raise

    async def load_latest_checkpoint(
        self,
        bag_id: str
    ) -> Optional[OrchestratorState]:
        """
        Load the most recent checkpoint for a bag.

        Args:
            bag_id: Bag identifier

        Returns:
            Latest orchestrator state or None
        """
        try:
            query = """
                SELECT state, checkpoint_id, node, timestamp
                FROM bag_state_checkpoints
                WHERE bag_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """

            result = await self.db_manager.query_postgres(
                query,
                (bag_id,),
                fetch_one=True
            )

            if not result:
                self.logger.info(f"No checkpoints found for bag {bag_id}")
                return None

            state_json, checkpoint_id, node, timestamp = result

            # Deserialize state
            state = json.loads(state_json)

            self.logger.info(
                f"Loaded latest checkpoint {checkpoint_id} "
                f"(node: {node}, time: {timestamp}) for bag {bag_id}"
            )

            return state

        except Exception as e:
            self.logger.error(f"Error loading latest checkpoint: {e}")
            raise

    async def get_checkpoint_history(
        self,
        bag_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get checkpoint history for a bag.

        Args:
            bag_id: Bag identifier
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint metadata
        """
        try:
            query = """
                SELECT checkpoint_id, workflow_id, node, timestamp, version
                FROM bag_state_checkpoints
                WHERE bag_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """

            results = await self.db_manager.query_postgres(
                query,
                (bag_id, limit)
            )

            checkpoints = []
            for row in results:
                checkpoints.append({
                    "checkpoint_id": row[0],
                    "workflow_id": row[1],
                    "node": row[2],
                    "timestamp": row[3].isoformat() if row[3] else None,
                    "version": row[4]
                })

            self.logger.info(f"Retrieved {len(checkpoints)} checkpoints for bag {bag_id}")

            return checkpoints

        except Exception as e:
            self.logger.error(f"Error getting checkpoint history: {e}")
            raise

    async def save_event(
        self,
        bag_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        source: str = "orchestrator"
    ) -> str:
        """
        Save a bag event to database.

        Args:
            bag_id: Bag identifier
            event_type: Type of event
            event_data: Event details
            source: Event source

        Returns:
            Event ID
        """
        try:
            import uuid
            event_id = str(uuid.uuid4())

            query = """
                INSERT INTO bag_events
                (event_id, bag_id, event_type, event_data, source, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            await self.db_manager.execute_postgres(
                query,
                (
                    event_id,
                    bag_id,
                    event_type,
                    json.dumps(event_data),
                    source,
                    datetime.utcnow()
                )
            )

            self.logger.info(f"Saved event {event_id} for bag {bag_id}")

            return event_id

        except Exception as e:
            self.logger.error(f"Error saving event: {e}")
            raise

    async def get_bag_events(
        self,
        bag_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get events for a bag.

        Args:
            bag_id: Bag identifier
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        try:
            query = """
                SELECT event_id, event_type, event_data, source, timestamp
                FROM bag_events
                WHERE bag_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """

            results = await self.db_manager.query_postgres(
                query,
                (bag_id, limit)
            )

            events = []
            for row in results:
                events.append({
                    "event_id": row[0],
                    "event_type": row[1],
                    "event_data": json.loads(row[2]) if row[2] else {},
                    "source": row[3],
                    "timestamp": row[4].isoformat() if row[4] else None
                })

            return events

        except Exception as e:
            self.logger.error(f"Error getting events: {e}")
            raise

    async def save_approval_request(
        self,
        workflow_id: str,
        bag_id: str,
        intervention_id: str,
        action: str,
        reason: str,
        approver_role: str,
        timeout_minutes: int = 30
    ) -> str:
        """
        Save an approval request to database.

        Args:
            workflow_id: Workflow identifier
            bag_id: Bag identifier
            intervention_id: Intervention identifier
            action: Action requiring approval
            reason: Reason for approval
            approver_role: Role of required approver
            timeout_minutes: Minutes until auto-approval

        Returns:
            Approval request ID
        """
        try:
            import uuid
            approval_id = str(uuid.uuid4())

            timeout_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

            query = """
                INSERT INTO approval_requests
                (approval_id, workflow_id, bag_id, intervention_id,
                 action, reason, approver_role, status, timeout_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            await self.db_manager.execute_postgres(
                query,
                (
                    approval_id,
                    workflow_id,
                    bag_id,
                    intervention_id,
                    action,
                    reason,
                    approver_role,
                    "pending",
                    timeout_at,
                    datetime.utcnow()
                )
            )

            self.logger.info(f"Created approval request {approval_id}")

            return approval_id

        except Exception as e:
            self.logger.error(f"Error saving approval request: {e}")
            raise

    async def update_approval_status(
        self,
        approval_id: str,
        status: str,
        approved_by: Optional[str] = None,
        comments: Optional[str] = None
    ) -> bool:
        """
        Update approval status.

        Args:
            approval_id: Approval request ID
            status: New status (approved, rejected, timeout)
            approved_by: Who approved/rejected
            comments: Optional comments

        Returns:
            True if updated successfully
        """
        try:
            query = """
                UPDATE approval_requests
                SET status = %s,
                    approved_by = %s,
                    comments = %s,
                    resolved_at = %s
                WHERE approval_id = %s
            """

            await self.db_manager.execute_postgres(
                query,
                (
                    status,
                    approved_by,
                    comments,
                    datetime.utcnow(),
                    approval_id
                )
            )

            self.logger.info(f"Updated approval {approval_id} to {status}")

            return True

        except Exception as e:
            self.logger.error(f"Error updating approval: {e}")
            raise

    async def get_pending_approvals(
        self,
        approver_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending approval requests.

        Args:
            approver_role: Filter by approver role (optional)

        Returns:
            List of pending approvals
        """
        try:
            if approver_role:
                query = """
                    SELECT approval_id, workflow_id, bag_id, intervention_id,
                           action, reason, approver_role, timeout_at, created_at
                    FROM approval_requests
                    WHERE status = 'pending' AND approver_role = %s
                    ORDER BY created_at ASC
                """
                params = (approver_role,)
            else:
                query = """
                    SELECT approval_id, workflow_id, bag_id, intervention_id,
                           action, reason, approver_role, timeout_at, created_at
                    FROM approval_requests
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                """
                params = ()

            results = await self.db_manager.query_postgres(query, params)

            approvals = []
            for row in results:
                approvals.append({
                    "approval_id": row[0],
                    "workflow_id": row[1],
                    "bag_id": row[2],
                    "intervention_id": row[3],
                    "action": row[4],
                    "reason": row[5],
                    "approver_role": row[6],
                    "timeout_at": row[7].isoformat() if row[7] else None,
                    "created_at": row[8].isoformat() if row[8] else None
                })

            return approvals

        except Exception as e:
            self.logger.error(f"Error getting pending approvals: {e}")
            raise

    async def cleanup_old_checkpoints(
        self,
        days_to_keep: int = 30
    ) -> int:
        """
        Clean up old checkpoints.

        Args:
            days_to_keep: Number of days of checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            query = """
                DELETE FROM bag_state_checkpoints
                WHERE timestamp < %s
            """

            deleted = await self.db_manager.execute_postgres(
                query,
                (cutoff_date,)
            )

            self.logger.info(f"Cleaned up {deleted} old checkpoints")

            return deleted

        except Exception as e:
            self.logger.error(f"Error cleaning up checkpoints: {e}")
            raise


async def create_checkpoint_tables(db_manager):
    """
    Create necessary database tables for state persistence.

    Args:
        db_manager: Database manager instance
    """
    # Checkpoint table
    checkpoint_table = """
        CREATE TABLE IF NOT EXISTS bag_state_checkpoints (
            checkpoint_id VARCHAR(255) PRIMARY KEY,
            workflow_id VARCHAR(255) NOT NULL,
            bag_id VARCHAR(100) NOT NULL,
            node VARCHAR(50) NOT NULL,
            state JSONB NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_checkpoints_bag_id
        ON bag_state_checkpoints(bag_id, timestamp DESC);

        CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id
        ON bag_state_checkpoints(workflow_id);
    """

    # Events table
    events_table = """
        CREATE TABLE IF NOT EXISTS bag_events (
            event_id VARCHAR(255) PRIMARY KEY,
            bag_id VARCHAR(100) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            event_data JSONB,
            source VARCHAR(50),
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_events_bag_id
        ON bag_events(bag_id, timestamp DESC);
    """

    # Approvals table
    approvals_table = """
        CREATE TABLE IF NOT EXISTS approval_requests (
            approval_id VARCHAR(255) PRIMARY KEY,
            workflow_id VARCHAR(255) NOT NULL,
            bag_id VARCHAR(100) NOT NULL,
            intervention_id VARCHAR(255) NOT NULL,
            action VARCHAR(255) NOT NULL,
            reason TEXT,
            approver_role VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            approved_by VARCHAR(100),
            comments TEXT,
            timeout_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_approvals_status
        ON approval_requests(status, created_at);

        CREATE INDEX IF NOT EXISTS idx_approvals_bag_id
        ON approval_requests(bag_id);
    """

    try:
        await db_manager.execute_postgres(checkpoint_table)
        await db_manager.execute_postgres(events_table)
        await db_manager.execute_postgres(approvals_table)

        logger.info("Created checkpoint persistence tables")

    except Exception as e:
        logger.error(f"Error creating checkpoint tables: {e}")
        raise
