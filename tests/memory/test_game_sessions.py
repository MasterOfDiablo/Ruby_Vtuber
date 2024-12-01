import pytest
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

from src.RubyAI.memory.game_sessions.event_tracker import EventTracker, EventPriority
from src.RubyAI.memory.game_sessions.session_manager import GameSessionManager
from src.RubyAI.memory.game_sessions.analytics import GameAnalytics

@pytest.fixture
def event_tracker():
    """Create a fresh event tracker for each test."""
    return EventTracker()

@pytest.fixture
def session_manager():
    """Create a fresh session manager for each test."""
    return GameSessionManager()

@pytest.fixture
def analytics(session_manager):
    """Create analytics with session manager."""
    return GameAnalytics(session_manager)

def test_event_processing(event_tracker):
    """Test real-time event processing."""
    # Process a significant event
    event = event_tracker.process_event(
        event_type="achievement",
        details={"name": "First Victory", "difficulty": 0.8},
        context={"game_mode": "survival"}
    )
    
    # Verify event priority calculation
    assert event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]
    
    # Verify emotional impact
    assert event.emotional_impact > 0
    
    # Verify event is in attention buffer
    current_focus = event_tracker.get_current_focus()
    assert current_focus is not None
    assert current_focus.event_type == "achievement"

def test_memory_formation(session_manager):
    """Test memory formation from events."""
    # Start a game session
    session_id = session_manager.start_session(
        game_name="Minecraft",
        context={"mode": "survival", "difficulty": "normal"}
    )
    
    # Process multiple events
    events = [
        ("block_break", {"block": "stone", "tool": "iron_pickaxe"}),
        ("achievement", {"name": "First Diamond", "rarity": "rare"}),
        ("combat", {"enemy": "creeper", "outcome": "victory"})
    ]
    
    for event_type, details in events:
        session_manager.process_event(event_type, details)
    
    # Verify memory formation
    assert len(session_manager.short_term) > 0
    assert len(session_manager.long_term) > 0
    
    # Verify important event became long-term memory
    achievement_memories = [
        m for m in session_manager.long_term.values()
        if m.core_event.event_type == "achievement"
    ]
    assert len(achievement_memories) > 0
    assert achievement_memories[0].importance > 0.5

def test_memory_associations(session_manager):
    """Test memory association formation."""
    session_manager.start_session(
        game_name="Minecraft",
        context={"mode": "survival"}
    )
    
    # Create related events
    session_manager.process_event(
        "mining",
        {"location": "cave", "found": "diamond"}
    )
    
    session_manager.process_event(
        "achievement",
        {"name": "Diamond Hunter", "location": "cave"}
    )
    
    # Verify associations formed
    memories = list(session_manager.long_term.values())
    if len(memories) >= 2:
        assert len(memories[0].associated_memories) > 0
        assert len(memories[1].associated_memories) > 0

def test_emotional_processing(event_tracker):
    """Test emotional processing of events."""
    # Process events with different emotional impacts
    event_tracker.process_event(
        "achievement",
        {"name": "Victory", "difficulty": 0.9},
        {"mood": "excited"}
    )
    
    event_tracker.process_event(
        "death",
        {"cause": "fall", "items_lost": True},
        {"mood": "frustrated"}
    )
    
    # Verify emotional state changes
    emotional_state = event_tracker.get_emotional_state()
    assert emotional_state['excitement'] > 0
    assert emotional_state['frustration'] > 0

def test_memory_analytics(session_manager, analytics):
    """Test memory analytics and learning patterns."""
    session_manager.start_session(
        game_name="Minecraft",
        context={"mode": "survival"}
    )
    
    # Generate some gameplay data
    for _ in range(5):
        session_manager.process_event(
            "mining",
            {"success": True, "efficiency": 0.8}
        )
        analytics.update_success_rate("mining", True)
    
    # Test analytics
    memory_analysis = analytics.analyze_memory_formation()
    learning_analysis = analytics.analyze_learning_patterns()
    
    assert memory_analysis['total_memories'] > 0
    assert 'mining' in learning_analysis['learning_progress']

def test_pattern_recognition(event_tracker):
    """Test pattern recognition in event sequences."""
    # Create a sequence of related events
    events = [
        ("explore", {"biome": "cave"}),
        ("mining", {"ore": "iron"}),
        ("craft", {"item": "iron_pickaxe"}),
        ("mining", {"ore": "diamond"})
    ]
    
    for event_type, details in events:
        event_tracker.process_event(
            event_type, details, {"sequence": "resource_gathering"}
        )
    
    # Verify patterns were recognized
    patterns = event_tracker.get_recent_patterns()
    assert len(patterns) > 0
    assert "mining" in patterns

def test_memory_recall(session_manager):
    """Test memory recall and reinforcement."""
    session_manager.start_session(
        game_name="Minecraft",
        context={"mode": "survival"}
    )
    
    # Create a significant memory
    session_manager.process_event(
        "boss_fight",
        {"boss": "ender_dragon", "outcome": "victory"}
    )
    
    # Get a memory to recall
    memory = next(iter(session_manager.long_term.values()))
    initial_strength = memory.reinforcement_level
    
    # Recall the memory multiple times
    for _ in range(3):
        session_manager.recall_memory(memory.id)
    
    # Verify reinforcement
    assert memory.reinforcement_level > initial_strength
    assert memory.recall_count == 3

def test_emotional_intelligence(analytics):
    """Test emotional intelligence analysis."""
    # Generate emotional data
    for _ in range(5):
        analytics.session_manager.event_tracker.process_event(
            "interaction",
            {"type": "friendly", "outcome": "positive"},
            {"emotional_state": "happy"}
        )
    
    # Analyze emotional intelligence
    ei_analysis = analytics.analyze_emotional_intelligence()
    
    assert ei_analysis['emotional_stability'] >= 0
    assert len(ei_analysis['emotional_growth']) > 0
    assert 'current_state' in ei_analysis

def test_decision_making(analytics):
    """Test decision-making analysis."""
    # Generate decision-related data
    session = analytics.session_manager
    session.start_session(
        game_name="Minecraft",
        context={"mode": "survival"}
    )
    
    # Process events that require decisions
    events = [
        ("combat_choice", {"option": "fight", "outcome": "success"}),
        ("resource_choice", {"option": "mine", "outcome": "success"}),
        ("build_choice", {"option": "shelter", "outcome": "success"})
    ]
    
    for event_type, details in events:
        session.process_event(event_type, details)
        analytics.update_success_rate(event_type, True)
    
    # Analyze decision making
    decision_analysis = analytics.analyze_decision_making()
    
    assert len(decision_analysis['decision_factors']) > 0
    assert 'emotional_weight' in decision_analysis['decision_factors']
    assert 'experience_weight' in decision_analysis['decision_factors']
