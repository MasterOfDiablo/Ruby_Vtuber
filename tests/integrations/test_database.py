import pytest
import json
from datetime import datetime
from uuid import uuid4

from src.RubyAI.integration.database.db_manager import DatabaseManager
from src.RubyAI.integration.database.game_queries import GameQueries
from src.RubyAI.integration.database.stream_queries import StreamQueries

# Fixtures
@pytest.fixture(scope="session")
def db():
    """Database manager fixture."""
    return DatabaseManager()

@pytest.fixture(scope="session")
def game_queries():
    """Game queries fixture."""
    return GameQueries()

@pytest.fixture(scope="session")
def stream_queries():
    """Stream queries fixture."""
    return StreamQueries()

@pytest.fixture(autouse=True)
def cleanup_database(db):
    """Clean up database before each test."""
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE viewer_interactions")
            cursor.execute("TRUNCATE TABLE stream_highlights")
            cursor.execute("TRUNCATE TABLE stream_sessions")
            cursor.execute("TRUNCATE TABLE game_events")
            cursor.execute("TRUNCATE TABLE game_sessions")
            cursor.execute("TRUNCATE TABLE viewer_profiles")
            cursor.execute("TRUNCATE TABLE performance_analytics")
            cursor.execute("TRUNCATE TABLE learning_history")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

def test_database_connection(db):
    """Test database connection and basic operations."""
    assert db.health_check() is True
    result = db.execute_query("SELECT 1 as test")
    assert result[0]['test'] == 1

def test_game_session_lifecycle(db):
    """Test complete game session lifecycle."""
    # Create game session
    session_id = str(uuid4())
    query = """
        INSERT INTO game_sessions 
        (session_id, game_name, game_mode, difficulty, status)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_query(
        query, 
        (session_id, "Minecraft", "survival", "normal", "active"),
        fetch=False
    )

    # Log game event
    event_id = str(uuid4())
    event_query = """
        INSERT INTO game_events 
        (event_id, session_id, event_type, event_category, event_data, impact_score)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    event_data = json.dumps({"achievement": "First Cave", "location": "Underground"})
    db.execute_query(
        event_query,
        (event_id, session_id, "achievement", "exploration", event_data, 0.7),
        fetch=False
    )

    # Verify session exists
    session_query = "SELECT * FROM game_sessions WHERE session_id = %s"
    result = db.execute_query(session_query, (session_id,))
    assert result is not None
    assert result[0]['game_name'] == "Minecraft"
    assert result[0]['status'] == "active"

    # Verify event exists
    event_query = "SELECT * FROM game_events WHERE session_id = %s"
    events = db.execute_query(event_query, (session_id,))
    assert len(events) == 1
    assert events[0]['event_type'] == "achievement"
    assert events[0]['event_category'] == "exploration"

def test_stream_session_lifecycle(db):
    """Test complete stream session lifecycle."""
    # Create game session first
    game_session_id = str(uuid4())
    db.execute_query(
        "INSERT INTO game_sessions (session_id, game_name, status) VALUES (%s, %s, %s)",
        (game_session_id, "Minecraft", "active"),
        fetch=False
    )

    # Create stream session
    stream_session_id = str(uuid4())
    db.execute_query(
        """
        INSERT INTO stream_sessions 
        (session_id, title, category, game_session_id, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (stream_session_id, "First Minecraft Stream!", "Gaming", game_session_id, "active"),
        fetch=False
    )

    # Create viewer interaction
    interaction_id = str(uuid4())
    viewer_id = str(uuid4())
    context_tags = json.dumps({"greeting": True, "first_time": True})
    db.execute_query(
        """
        INSERT INTO viewer_interactions 
        (interaction_id, session_id, viewer_id, interaction_type, message,
         sentiment_score, impact_level, context_tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (interaction_id, stream_session_id, viewer_id, "chat", "Hello Ruby!",
         0.8, 5, context_tags),
        fetch=False
    )

    # Verify stream session
    session_query = "SELECT * FROM stream_sessions WHERE session_id = %s"
    result = db.execute_query(session_query, (stream_session_id,))
    assert result is not None
    assert result[0]['title'] == "First Minecraft Stream!"
    assert result[0]['status'] == "active"

    # Verify interaction
    interaction_query = "SELECT * FROM viewer_interactions WHERE session_id = %s"
    interactions = db.execute_query(interaction_query, (stream_session_id,))
    assert len(interactions) == 1
    assert interactions[0]['message'] == "Hello Ruby!"
    assert interactions[0]['sentiment_score'] == 0.8

def test_error_handling(db):
    """Test error handling in database operations."""
    # Test non-existent table
    with pytest.raises(Exception):
        db.execute_query("SELECT * FROM nonexistent_table")

    # Test foreign key constraint violation
    with pytest.raises(Exception):
        invalid_session_id = str(uuid4())
        db.execute_query(
            """
            INSERT INTO game_events 
            (event_id, session_id, event_type, event_category)
            VALUES (%s, %s, %s, %s)
            """,
            (str(uuid4()), invalid_session_id, "test", "test"),
            fetch=False
        )

def test_transaction_handling(db):
    """Test transaction management."""
    connection = db.begin_transaction()
    try:
        # Execute multiple operations
        cursor = connection.cursor(dictionary=True)
        
        # Create game session
        session_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO game_sessions (session_id, game_name, status)
            VALUES (%s, %s, %s)
            """,
            (session_id, "Minecraft", "active")
        )
        
        # Create event
        event_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO game_events 
            (event_id, session_id, event_type, event_category)
            VALUES (%s, %s, %s, %s)
            """,
            (event_id, session_id, "test", "test")
        )
        
        connection.commit()
        
        # Verify data was saved
        cursor.execute("SELECT COUNT(*) as count FROM game_events")
        count = cursor.fetchone()['count']
        assert count == 1
        
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
