"""Task manager for handling background tasks with Valkey."""

import json
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from fastapi import BackgroundTasks
from tmt import Logger
from valkey import Valkey

from tmt_web import settings

# Type for function results
T = TypeVar("T")

# Task status constants
PENDING = "PENDING"
STARTED = "STARTED"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"

# Default task expiration time (24 hours)
DEFAULT_TASK_EXPIRY = 60 * 60 * 24


class TaskManager:
    """Manager for background tasks using Valkey for state storage."""

    def __init__(self) -> None:
        """Initialize task manager with Valkey connection."""
        self.logger = Logger(logging.getLogger("tmt-web-tasks"))
        self.client = Valkey.from_url(settings.VALKEY_URL)
        self.logger.debug(f"Connected to Valkey at {settings.VALKEY_URL}")

    def _get_task_key(self, task_id: str) -> str:
        """Get the Valkey key for a task."""
        return f"task:{task_id}"

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        task_key = self._get_task_key(task_id)

        # Store initial task info
        task_info = {
            "id": task_id,
            "status": PENDING,
            "created_at": datetime.now(tz=UTC).isoformat(),
            "result": None,
            "error": None,
        }

        # Store in Valkey with expiration
        self.client.set(task_key, json.dumps(task_info), ex=DEFAULT_TASK_EXPIRY)

        return task_id

    def get_task_info(self, task_id: str) -> dict[str, Any]:
        """Get information about a task."""
        task_key = self._get_task_key(task_id)
        task_data = self.client.get(task_key)

        if not task_data:
            self.logger.fail(f"Task {task_id} not found")
            return {
                "id": task_id,
                "status": FAILURE,
                "error": "Task not found",
                "result": None,
            }

        return json.loads(task_data)

    def update_task(
        self, task_id: str, status: str, result: Any = None, error: str | None = None
    ) -> None:
        """Update task status and result."""
        task_key = self._get_task_key(task_id)
        task_data = self.client.get(task_key)

        if not task_data:
            self.logger.warning(f"Trying to update non-existent task {task_id}")
            return

        try:
            task_info = json.loads(task_data)
            task_info["status"] = status

            if result is not None:
                task_info["result"] = result

            if error is not None:
                task_info["error"] = error

            # Update timestamp
            task_info["updated_at"] = datetime.now(tz=UTC).isoformat()

            # Store updated info
            self.client.set(task_key, json.dumps(task_info), ex=DEFAULT_TASK_EXPIRY)
        except json.JSONDecodeError:
            self.logger.fail(f"Failed to decode task data for {task_id}")
        except (TypeError, ValueError) as e:
            self.logger.fail(f"Failed to encode task data for {task_id}: {e}")

    def execute_task(
        self,
        background_tasks: BackgroundTasks,
        func: Callable[..., T],
        **kwargs: Any,
    ) -> str:
        """Schedule a function to run as a background task.

        Args:
            background_tasks: FastAPI BackgroundTasks object
            func: Function to be executed
            **kwargs: Arguments to pass to the function

        Returns:
            Task ID for tracking the task
        """
        task_id = self.create_task()

        # Define wrapper function to update task state
        def task_wrapper() -> None:
            try:
                self.update_task(task_id, STARTED)
                self.logger.debug(f"Starting task {task_id}")

                # Execute function
                result = func(**kwargs)

                # Update task with success result
                self.update_task(task_id, SUCCESS, result=result)
                self.logger.debug(f"Task {task_id} completed successfully")

            except Exception as exc:
                # Update task with error information
                error_message = str(exc)
                self.logger.fail(f"Task {task_id} failed: {error_message}")
                self.update_task(task_id, FAILURE, error=error_message)

        # Add task to background tasks
        background_tasks.add_task(task_wrapper)
        return task_id


# Global task manager instance
task_manager = TaskManager()
