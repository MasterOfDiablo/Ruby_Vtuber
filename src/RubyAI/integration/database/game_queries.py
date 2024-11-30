import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from .db_manager import DatabaseManager

class GameQueries:
    """Handles all game-related database queries."""

    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)

    def create_session(self, game_name: str, game_mode: str = None, 
                      difficulty: str = None) -> Optional[UUID]:
        """
        Create a new game session.
        
        Args:
            game_name: Name of the game being played
            game_mode: Game mode (e.g., survival, creative)
            difficulty: Game difficulty setting
            
        Returns:
            UUID of created session or None if creation failed
        """
        try:
            query = """
                INSERT INTO game_sessions 
                (game_name, game_mode, difficulty, status)
                VALUES (%s, %s, %s, 'active')
                RETURNING session_id
            """
            result = self.db.execute_query(query, (game_name, game_mode, difficulty))
            return result[0]['session_id'] if result else None
        except Exception as e:
            self.logger.error(f"Failed to create game session: {e}")
            raise

    def end_session(self, session_id: UUID, summary: Dict[str, Any]) -> None:
        """
        End a game session and update its summary.
        
        Args:
            session_id: UUID of the session to end
            summary: Session summary data including achievements, stats, etc.
        """
        try:
            query = """
                UPDATE game_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    status = 'completed',
                    session_summary = %s
                WHERE session_id = %s
            """
            self.db.execute_query(query, (json.dumps(summary), session_id), fetch=False)
        except Exception as e:
            self.logger.error(f"Failed to end game session: {e}")
            raise

    def log_event(self, session_id: UUID, event_type: str, category: str,
                 data: Dict[str, Any], impact_score: float = 0.0) -> None:
        """
        Log a game event.
        
        Args:
            session_id: UUID of the active game session
            event_type: Type of event (e.g., achievement, death, milestone)
            category: Event category (e.g., combat, exploration)
            data: Detailed event data
            impact_score: Significance of the event (0.0 to 1.0)
        """
        try:
            query = """
                INSERT INTO game_events 
                (session_id, event_type, event_category, event_data, impact_score)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(query, (session_id, event_type, category,
                                        json.dumps(data), impact_score), fetch=False)
        except Exception as e:
            self.logger.error(f"Failed to log game event: {e}")
            raise

    def get_session_events(self, session_id: UUID, 
                          category: str = None) -> List[Dict[str, Any]]:
        """
        Get events for a specific game session.
        
        Args:
            session_id: UUID of the game session
            category: Optional category filter
            
        Returns:
            List of event dictionaries
        """
        try:
            if category:
                query = """
                    SELECT * FROM game_events
                    WHERE session_id = %s AND event_category = %s
                    ORDER BY timestamp DESC
                """
                return self.db.execute_query(query, (session_id, category)) or []
            else:
                query = """
                    SELECT * FROM game_events
                    WHERE session_id = %s
                    ORDER BY timestamp DESC
                """
                return self.db.execute_query(query, (session_id,)) or []
        except Exception as e:
            self.logger.error(f"Failed to get session events: {e}")
            raise

    def get_session_summary(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get complete summary of a game session.
        
        Args:
            session_id: UUID of the game session
            
        Returns:
            Dictionary containing session details and events
        """
        try:
            query = """
                SELECT 
                    gs.*,
                    COALESCE(
                        json_arrayagg(
                            json_object(
                                'event_type', ge.event_type,
                                'category', ge.event_category,
                                'data', ge.event_data,
                                'timestamp', ge.timestamp,
                                'impact_score', ge.impact_score
                            )
                        ),
                        '[]'
                    ) as events
                FROM game_sessions gs
                LEFT JOIN game_events ge ON gs.session_id = ge.session_id
                WHERE gs.session_id = %s
                GROUP BY gs.session_id
            """
            result = self.db.execute_query(query, (session_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get session summary: {e}")
            raise

    def get_game_statistics(self, game_name: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a specific game.
        
        Args:
            game_name: Name of the game
            
        Returns:
            Dictionary containing game statistics
        """
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT gs.session_id) as total_sessions,
                    SUM(TIMESTAMPDIFF(SECOND, gs.start_time, 
                        COALESCE(gs.end_time, CURRENT_TIMESTAMP))) as total_playtime_seconds,
                    COUNT(ge.event_id) as total_events,
                    AVG(ge.impact_score) as avg_event_impact
                FROM game_sessions gs
                LEFT JOIN game_events ge ON gs.session_id = ge.session_id
                WHERE gs.game_name = %s
                GROUP BY gs.game_name
            """
            result = self.db.execute_query(query, (game_name,))
            return result[0] if result else {
                'total_sessions': 0,
                'total_playtime_seconds': 0,
                'total_events': 0,
                'avg_event_impact': 0.0
            }
        except Exception as e:
            self.logger.error(f"Failed to get game statistics: {e}")
            raise

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all currently active game sessions.
        
        Returns:
            List of active session dictionaries
        """
        try:
            query = """
                SELECT * FROM game_sessions
                WHERE status = 'active'
                ORDER BY start_time DESC
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            raise
