import pytest
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

from src.RubyAI.memory.stream_sessions.session_manager import StreamSessionManager
from src.RubyAI.memory.stream_sessions.interaction_manager import InteractionManager, InteractionType
from src.RubyAI.memory.stream_sessions.highlight_tracker import HighlightTracker, HighlightType
from src.RubyAI.memory.stream_sessions.analytics import StreamAnalytics
from src.RubyAI.integration.database.game_queries import GameQueries

@pytest.fixture
def session_manager():
    return StreamSessionManager()

@pytest.fixture
def interaction_manager():
    return InteractionManager()

@pytest.fixture
def highlight_tracker():
    return HighlightTracker()

@pytest.fixture
def analytics():
    return StreamAnalytics()

@pytest.fixture
def game_queries():
    return GameQueries()

def test_session_management(session_manager):
    """Test stream session creation and management."""
    # Start a stream session
    session_id = session_manager.start_session(
        title="Test Stream",
        category="Gaming",
        game_session_id=None
    )
    assert session_id is not None

    # Verify session is active
    active_sessions = session_manager.get_active_sessions()
    assert len(active_sessions) > 0
    assert active_sessions[0]['session_id'] == session_id

    # End session
    metrics = {
        'duration': 3600,  # 1 hour
        'peak_viewers': 100,
        'avg_engagement': 0.75
    }
    session_manager.end_session(session_id, metrics)

    # Verify session ended
    active_sessions = session_manager.get_active_sessions()
    assert len([s for s in active_sessions if s['session_id'] == session_id]) == 0

def test_interaction_processing(interaction_manager):
    """Test viewer interaction processing."""
    # Process a chat message
    interaction = interaction_manager.process_interaction(
        viewer_id=uuid4(),
        interaction_type=InteractionType.CHAT,
        content="Hello Ruby!",
        metadata={'emotes': ['👋']}
    )
    assert interaction is not None
    assert interaction.sentiment_score >= -1.0 and interaction.sentiment_score <= 1.0

    # Get active conversations
    conversations = interaction_manager.get_active_conversations()
    assert len(conversations) > 0

    # Test context tracking
    context = interaction_manager.get_viewer_context(interaction.viewer_id)
    assert 'engagement_level' in context
    assert 'topics' in context

def test_highlight_tracking(highlight_tracker):
    """Test stream highlight tracking."""
    # Create a highlight-worthy event
    highlight = highlight_tracker.process_event(
        event_type="achievement",
        details={
            'name': "Boss Victory",
            'difficulty': "Hard"
        },
        viewer_reactions=[{
            'type': 'cheer',
            'count': 10
        }]
    )
    assert highlight is not None
    assert highlight.importance > 0.7

    # Get recent highlights
    recent = highlight_tracker.get_recent_highlights()
    assert len(recent) > 0
    assert recent[0].highlight_type == HighlightType.ACHIEVEMENT

def test_stream_analytics(analytics, session_manager):
    """Test stream analytics processing."""
    session_id = session_manager.start_session(
        title="Analytics Test",
        category="Gaming"
    )

    # Generate some test data
    for _ in range(5):
        analytics.track_interaction({
            'type': 'chat',
            'sentiment': 0.8,
            'engagement': 0.7
        })

    # Test analytics
    analysis = analytics.analyze_session(session_id)
    assert 'viewer_engagement' in analysis
    assert 'interaction_patterns' in analysis
    assert 'highlight_distribution' in analysis

def test_viewer_relationship_tracking(interaction_manager):
    """Test viewer relationship and engagement tracking."""
    viewer_id = uuid4()
    
    # Process multiple interactions from same viewer
    for _ in range(3):
        interaction_manager.process_interaction(
            viewer_id=viewer_id,
            interaction_type=InteractionType.CHAT,
            content="Great stream!",
            metadata={'mood': 'positive'}
        )

    # Check viewer state
    viewer_state = interaction_manager.get_viewer_context(viewer_id)
    assert viewer_state['interaction_count'] == 3
    assert len(viewer_state['sentiment_history']) > 0

def test_highlight_analysis(highlight_tracker):
    """Test highlight analysis and pattern recognition."""
    # Generate multiple highlights
    events = [
        ("achievement", {'name': "Speed Run"}),
        ("funny_moment", {'trigger': "Game Bug"}),
        ("achievement", {'name': "Perfect Score"})
    ]

    for event_type, details in events:
        highlight_tracker.process_event(event_type, details)

    # Analyze trends
    trends = highlight_tracker.analyze_highlight_trends()
    assert 'highlight_frequency' in trends
    assert 'popular_types' in trends
    assert 'peak_times' in trends

def test_engagement_tracking(analytics):
    """Test engagement level tracking and analysis."""
    # Track engagement over time
    timestamps = []
    for i in range(5):
        analytics.track_engagement_level(0.5 + i * 0.1)
        timestamps.append(datetime.now())

    # Analyze engagement
    engagement_analysis = analytics.analyze_engagement_trends()
    assert 'average_engagement' in engagement_analysis
    assert 'peak_times' in engagement_analysis
    assert 'trend' in engagement_analysis

def test_context_awareness(session_manager, interaction_manager):
    """Test context awareness and adaptation."""
    session_id = session_manager.start_session(
        title="Context Test",
        category="Gaming"
    )

    # Update context
    interaction_manager.update_stream_context({
        'game_state': 'boss_fight',
        'mood': 'excited',
        'engagement_level': 0.8
    })

    # Process interaction with context
    interaction = interaction_manager.process_interaction(
        viewer_id=uuid4(),
        interaction_type=InteractionType.STRATEGY_ADVICE,
        content="Try using the special attack!",
        metadata={'context': 'boss_fight'}
    )

    assert interaction.importance_score > 0.5  # Context should increase importance

def test_memory_integration(session_manager, game_queries):
    """Test integration with game session memory."""
    # First create a game session
    game_session_id = game_queries.create_session(
        game_name="Minecraft",
        game_mode="survival",
        difficulty="normal"
    )
    assert game_session_id is not None

    # Start stream with linked game session
    session_id = session_manager.start_session(
        title="Memory Test",
        category="Gaming",
        game_session_id=game_session_id
    )

    # Verify game context is accessible
    session_data = session_manager.get_session_data(session_id)
    assert session_data['game_session_id'] == game_session_id
