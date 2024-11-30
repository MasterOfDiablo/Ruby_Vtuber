import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from .db_manager import DatabaseManager

class StreamQueries:
    """Handles all stream-related database queries."""

    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)

    def create_session(self, title: str, category: str, 
                      game_session_id: Optional[UUID] = None) -> Optional[UUID]:
        """
        Create a new stream session.
        
        Args:
            title: Stream title
            category: Stream category
            game_session_id: Optional UUID of associated game session
            
        Returns:
            UUID of created session or None if creation failed
        """
        try:
            query = """
                INSERT INTO stream_sessions 
                (title, category, game_session_id, status)
                VALUES (%s, %s, %s, 'active')
                RETURNING session_id
            """
            result = self.db.execute_query(query, (title, category, game_session_id))
            return result[0]['session_id'] if result else None
        except Exception as e:
            self.logger.error(f"Failed to create stream session: {e}")
            raise

    def end_session(self, session_id: UUID, metrics: Dict[str, Any]) -> None:
        """
        End a stream session and update its metrics.
        
        Args:
            session_id: UUID of the session to end
            metrics: Session metrics including viewer stats, engagement, etc.
        """
        try:
            query = """
                UPDATE stream_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    status = 'completed',
                    session_metrics = %s
                WHERE session_id = %s
            """
            self.db.execute_query(query, (json.dumps(metrics), session_id), fetch=False)
        except Exception as e:
            self.logger.error(f"Failed to end stream session: {e}")
            raise

    def log_interaction(self, session_id: UUID, viewer_id: UUID,
                       interaction_type: str, message: str,
                       sentiment_score: float, impact_level: int,
                       context_tags: Dict[str, Any]) -> None:
        """
        Log a viewer interaction.
        
        Args:
            session_id: UUID of the active stream session
            viewer_id: UUID of the viewer
            interaction_type: Type of interaction
            message: Content of the interaction
            sentiment_score: Sentiment analysis score
            impact_level: Importance level (1-10)
            context_tags: Contextual information about the interaction
        """
        try:
            query = """
                INSERT INTO viewer_interactions 
                (session_id, viewer_id, interaction_type, message,
                 sentiment_score, impact_level, context_tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(query, (session_id, viewer_id, interaction_type,
                                        message, sentiment_score, impact_level,
                                        json.dumps(context_tags)), fetch=False)
        except Exception as e:
            self.logger.error(f"Failed to log viewer interaction: {e}")
            raise

    def log_highlight(self, session_id: UUID, highlight_type: str,
                     description: str, viewer_impact: Dict[str, Any],
                     significance: float) -> None:
        """
        Log a stream highlight.
        
        Args:
            session_id: UUID of the stream session
            highlight_type: Type of highlight
            description: Description of the highlight
            viewer_impact: Data about viewer reactions
            significance: Importance score (0.0 to 1.0)
        """
        try:
            query = """
                INSERT INTO stream_highlights 
                (session_id, highlight_type, description,
                 viewer_impact, significance_score)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(query, (session_id, highlight_type, description,
                                        json.dumps(viewer_impact), significance),
                                fetch=False)
        except Exception as e:
            self.logger.error(f"Failed to log stream highlight: {e}")
            raise

    def get_session_interactions(self, session_id: UUID, 
                               interaction_type: str = None) -> List[Dict[str, Any]]:
        """
        Get interactions for a specific stream session.
        
        Args:
            session_id: UUID of the stream session
            interaction_type: Optional interaction type filter
            
        Returns:
            List of interaction dictionaries
        """
        try:
            if interaction_type:
                query = """
                    SELECT * FROM viewer_interactions
                    WHERE session_id = %s AND interaction_type = %s
                    ORDER BY timestamp DESC
                """
                return self.db.execute_query(query, (session_id, interaction_type)) or []
            else:
                query = """
                    SELECT * FROM viewer_interactions
                    WHERE session_id = %s
                    ORDER BY timestamp DESC
                """
                return self.db.execute_query(query, (session_id,)) or []
        except Exception as e:
            self.logger.error(f"Failed to get session interactions: {e}")
            raise

    def get_session_highlights(self, session_id: UUID) -> List[Dict[str, Any]]:
        """
        Get highlights for a specific stream session.
        
        Args:
            session_id: UUID of the stream session
            
        Returns:
            List of highlight dictionaries
        """
        try:
            query = """
                SELECT * FROM stream_highlights
                WHERE session_id = %s
                ORDER BY significance_score DESC, timestamp DESC
            """
            return self.db.execute_query(query, (session_id,)) or []
        except Exception as e:
            self.logger.error(f"Failed to get session highlights: {e}")
            raise

    def get_viewer_history(self, viewer_id: UUID) -> List[Dict[str, Any]]:
        """
        Get interaction history for a specific viewer.
        
        Args:
            viewer_id: UUID of the viewer
            
        Returns:
            List of interaction dictionaries
        """
        try:
            query = """
                SELECT 
                    vi.*,
                    ss.title as stream_title,
                    ss.category as stream_category
                FROM viewer_interactions vi
                JOIN stream_sessions ss ON vi.session_id = ss.session_id
                WHERE vi.viewer_id = %s
                ORDER BY vi.timestamp DESC
            """
            return self.db.execute_query(query, (viewer_id,)) or []
        except Exception as e:
            self.logger.error(f"Failed to get viewer history: {e}")
            raise

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all currently active stream sessions.
        
        Returns:
            List of active session dictionaries
        """
        try:
            query = """
                SELECT * FROM stream_sessions
                WHERE status = 'active'
                ORDER BY start_time DESC
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            raise

    def get_session_analytics(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a stream session.
        
        Args:
            session_id: UUID of the stream session
            
        Returns:
            Dictionary containing session analytics
        """
        try:
            query = """
                SELECT 
                    ss.*,
                    COUNT(DISTINCT vi.viewer_id) as unique_viewers,
                    COUNT(vi.interaction_id) as total_interactions,
                    AVG(vi.sentiment_score) as avg_sentiment,
                    COUNT(sh.highlight_id) as highlight_count,
                    AVG(sh.significance_score) as avg_highlight_significance
                FROM stream_sessions ss
                LEFT JOIN viewer_interactions vi ON ss.session_id = vi.session_id
                LEFT JOIN stream_highlights sh ON ss.session_id = sh.session_id
                WHERE ss.session_id = %s
                GROUP BY ss.session_id
            """
            result = self.db.execute_query(query, (session_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get session analytics: {e}")
            raise
