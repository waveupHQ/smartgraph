import json
import os
from typing import Any, Dict, Optional

import aiofiles
from pydantic import BaseModel, Field

from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

class Checkpoint(BaseModel):
    node_id: str
    state: str
    next_nodes: list[str]

class CheckpointManager:
    def __init__(self, storage_path: str = "checkpoints"):
        self.storage_path = storage_path
        self.checkpoints: Dict[str, Dict[str, Checkpoint]] = {}
        os.makedirs(storage_path, exist_ok=True)

    async def save_checkpoint(self, thread_id: str, checkpoint: Checkpoint) -> None:
        if thread_id not in self.checkpoints:
            self.checkpoints[thread_id] = {}
        self.checkpoints[thread_id][checkpoint.node_id] = checkpoint
        await self._save_to_disk(thread_id)

    async def get_checkpoint(self, thread_id: str, node_id: str) -> Optional[Checkpoint]:
        if thread_id not in self.checkpoints:
            await self.load_from_disk(thread_id)
        return self.checkpoints.get(thread_id, {}).get(node_id)

    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Checkpoint]:
        if thread_id not in self.checkpoints:
            await self.load_from_disk(thread_id)
        thread_checkpoints = self.checkpoints.get(thread_id, {})
        if not thread_checkpoints:
            return None
        return max(thread_checkpoints.values(), key=lambda c: c.node_id)

    async def _save_to_disk(self, thread_id: str) -> None:
        file_path = os.path.join(self.storage_path, f"{thread_id}.json")
        data = {node_id: cp.dict() for node_id, cp in self.checkpoints[thread_id].items()}
        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def load_from_disk(self, thread_id: str) -> None:
        file_path = os.path.join(self.storage_path, f"{thread_id}.json")
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                if not content.strip():  # Check if file is empty
                    logger.warning(f"Checkpoint file for thread {thread_id} is empty.")
                    self.checkpoints[thread_id] = {}
                    return
                data = json.loads(content)
            self.checkpoints[thread_id] = {
                node_id: Checkpoint(**cp_data) for node_id, cp_data in data.items()
            }
        except FileNotFoundError:
            logger.info(f"No checkpoint file found for thread {thread_id}.")
            self.checkpoints[thread_id] = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding checkpoint file for thread {thread_id}: {str(e)}")
            self.checkpoints[thread_id] = {}
        except Exception as e:
            logger.error(f"Error loading checkpoint for thread {thread_id}: {str(e)}")
            self.checkpoints[thread_id] = {}

    async def clear_checkpoints(self, thread_id: str) -> None:
        if thread_id in self.checkpoints:
            del self.checkpoints[thread_id]
        file_path = os.path.join(self.storage_path, f"{thread_id}.json")
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
