import json
import os

import pytest

from smartgraph.checkpoint_manager import Checkpoint, CheckpointManager


@pytest.fixture
def checkpoint_manager():
    manager = CheckpointManager("test_checkpoints")
    yield manager
    # Cleanup
    for file in os.listdir("test_checkpoints"):
        os.remove(os.path.join("test_checkpoints", file))
    os.rmdir("test_checkpoints")


@pytest.mark.asyncio
async def test_save_and_get_checkpoint(checkpoint_manager):
    checkpoint = Checkpoint(node_id="node1", state={"key": "value"}, next_nodes=["node2"])
    await checkpoint_manager.save_checkpoint("thread1", checkpoint)

    retrieved = await checkpoint_manager.get_checkpoint("thread1", "node1")
    assert retrieved == checkpoint


@pytest.mark.asyncio
async def test_get_latest_checkpoint(checkpoint_manager):
    checkpoints = [
        Checkpoint(node_id=f"node{i}", state={"key": f"value{i}"}, next_nodes=[f"node{i+1}"])
        for i in range(3)
    ]
    for cp in checkpoints:
        await checkpoint_manager.save_checkpoint("thread1", cp)

    latest = await checkpoint_manager.get_latest_checkpoint("thread1")
    assert latest == checkpoints[-1]


@pytest.mark.asyncio
async def test_save_to_disk_and_load_from_disk(checkpoint_manager):
    checkpoint = Checkpoint(node_id="node1", state={"key": "value"}, next_nodes=["node2"])
    await checkpoint_manager.save_checkpoint("thread1", checkpoint)

    # Create a new checkpoint manager to load from disk
    new_manager = CheckpointManager("test_checkpoints")
    retrieved = await new_manager.get_checkpoint("thread1", "node1")
    assert retrieved == checkpoint


@pytest.mark.asyncio
async def test_clear_checkpoints(checkpoint_manager):
    checkpoint = Checkpoint(node_id="node1", state={"key": "value"}, next_nodes=["node2"])
    await checkpoint_manager.save_checkpoint("thread1", checkpoint)

    await checkpoint_manager.clear_checkpoints("thread1")

    latest = await checkpoint_manager.get_latest_checkpoint("thread1")
    assert latest is None
    assert not os.path.exists(os.path.join("test_checkpoints", "thread1.json"))
