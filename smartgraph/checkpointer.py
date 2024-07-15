# smartgraph/checkpointer.py

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Checkpoint(BaseModel):
    node_id: str
    state: Dict[str, Any]
    next_nodes: List[str]


class Checkpointer:
    def __init__(self, storage_path: str = "checkpoints.json"):
        self.storage_path = storage_path
        self.checkpoints: Dict[str, Dict[str, Checkpoint]] = {}

    def save_checkpoint(self, thread_id: str, checkpoint: Checkpoint):
        if thread_id not in self.checkpoints:
            self.checkpoints[thread_id] = {}
        self.checkpoints[thread_id][checkpoint.node_id] = checkpoint
        self._save_to_disk()

    def get_checkpoint(self, thread_id: str, node_id: str) -> Optional[Checkpoint]:
        return self.checkpoints.get(thread_id, {}).get(node_id)

    def get_latest_checkpoint(self, thread_id: str) -> Optional[Checkpoint]:
        thread_checkpoints = self.checkpoints.get(thread_id, {})
        if not thread_checkpoints:
            return None
        return max(thread_checkpoints.values(), key=lambda c: c.node_id)

    def _save_to_disk(self):
        with open(self.storage_path, "w") as f:
            json.dump(
                {
                    tid: {nid: cp.dict() for nid, cp in thread.items()}
                    for tid, thread in self.checkpoints.items()
                },
                f,
            )

    def load_from_disk(self):
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.checkpoints = {
                    tid: {nid: Checkpoint(**cp) for nid, cp in thread.items()}
                    for tid, thread in data.items()
                }
        except FileNotFoundError:
            self.checkpoints = {}
