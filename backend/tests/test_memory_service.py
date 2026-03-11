import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from db.models import BehavioralPattern, InterventionHistory
from services.memory_service import MemoryService

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def memory_svc():
    with patch("services.memory_service.Memory.from_config") as mock_mem0:
        svc = MemoryService()
        svc.mem0 = MagicMock()
        return svc

@pytest.mark.asyncio
async def test_add_conversation_memory(memory_svc):
    memory_svc.add_conversation_memory("user123", "I'm procrastinating", "Vent session")
    memory_svc.mem0.add.assert_called_once_with(
        "I'm procrastinating", 
        user_id="user123", 
        metadata={"type": "conversation", "context": "Vent session"}
    )

@pytest.mark.asyncio
@patch("services.memory_service.pattern_repo", new_callable=AsyncMock)
async def test_add_pattern_memory(mock_repo, memory_svc, mock_db_session):
    # Mock pattern repo creation
    mock_pattern = BehavioralPattern(id="123", pattern_type="distraction", description="test")
    mock_repo.create.return_value = mock_pattern
    
    result = await memory_svc.add_pattern_memory(
        mock_db_session, 
        pattern_type="distraction", 
        description="Frequent context switching", 
        confidence=0.9
    )
    
    # Assert Layer 2 (DB) was called
    mock_repo.create.assert_called_once()
    
    # Assert Layer 1 (Mem0) was also called due to high confidence
    memory_svc.mem0.add.assert_called_once()
    
    assert result == mock_pattern

@pytest.mark.asyncio
@patch("services.memory_service.pattern_repo", new_callable=AsyncMock)
async def test_get_intervention_history(mock_repo, memory_svc, mock_db_session):
    mock_history = [InterventionHistory(id="1")]
    mock_repo.get_intervention_history.return_value = mock_history
    
    result = await memory_svc.get_intervention_history(mock_db_session, limit=5)
    
    mock_repo.get_intervention_history.assert_called_once_with(
        db=mock_db_session, limit=5, intervention_type=None
    )
    assert result == mock_history
