import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from ...integration.database.stream_queries import StreamQueries
from .interaction_manager import InteractionManager, InteractionType
from .highlight_tracker import HighlightTracker, HighlightType
from .analytics import StreamAnalytics

class StreamSessionManager:
    """
    Manages stream sessions and coordinates between different components.
    Acts as the main interface for stream-related operations.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = StreamQueries()
        
        # Component managers
        self.interaction_manager = InteractionManager()
        self.highlight_tracker = HighlightTracker()
        self.analytics = StreamAnalytics()
        
        # Active session tracking
        self.current_session_id: Optional[UUID] = None
        self.session_data: Dict[str, Any] = {}
        self.game_session_id: Optional[UUID] = None

    def start_session(self, title: str, category: str, 
                     game_session_id: Optional[UUID] = None) -> UUID:
        """
        Start a new stream session.
        
        Args:
            title: Stream title
            category: Stream category
            game_session_id: Optional UUID of associated game session
            
        Returns:
            UUID of created session
        """
        try:
            # Create session in database
            session_id = self.db.create_session(title, category, game_session_id)
            if not session_id:
                raise ValueError("Failed to create stream session")
                
            # Initialize session state
            self.current_session_id = session_id
            self.game_session_id = game_session_id
            self.session_data = {
                'session_id': session_id,
                'title': title,
                'category': category,
                'game_session_id': game_session_id,
                'start_time': datetime.now(),
                'status': 'active'
            }
            
            # Initialize components
            self.interaction_manager = InteractionManager()
            self.highlight_tracker = HighlightTracker()
            self.analytics = StreamAnalytics()
            
            self.logger.info(f"Started stream session: {title}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to start stream session: {e}")
            raise

    def end_session(self, session_id: UUID, metrics: Dict[str, Any]) -> None:
        """
        End a stream session.
        
        Args:
            session_id: UUID of session to end
            metrics: Session metrics
        """
        try:
            if session_id != self.current_session_id:
                raise ValueError("Session ID mismatch")
                
            # Enrich metrics with component data
            metrics.update({
                'interaction_stats': self.interaction_manager.get_session_stats(),
                'highlights': [h.__dict__ for h in self.highlight_tracker.get_recent_highlights()],
                'analytics': self.analytics.get_session_summary()
            })
            
            # Update database
            self.db.end_session(session_id, metrics)
            
            # Clear session state
            self.current_session_id = None
            self.session_data = {}
            self.game_session_id = None
            
            self.logger.info(f"Ended stream session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to end stream session: {e}")
            raise

    def process_interaction(self, viewer_id: UUID, interaction_type: str,
                          content: str, metadata: Dict[str, Any] = None) -> None:
        """
        Process a viewer interaction.
        
        Args:
            viewer_id: UUID of the viewer
            interaction_type: Type of interaction
            content: Interaction content
            metadata: Additional interaction metadata
        """
        try:
            if not self.current_session_id:
                raise ValueError("No active stream session")
                
            # Process through interaction manager
            interaction = self.interaction_manager.process_interaction(
                viewer_id=viewer_id,
                interaction_type=interaction_type,
                content=content,
                metadata=metadata
            )
            
            # Log to database
            self.db.log_interaction(
                session_id=self.current_session_id,
                viewer_id=viewer_id,
                interaction_type=interaction_type,
                message=content,
                sentiment_score=interaction.sentiment_score,
                impact_level=int(interaction.importance_score * 10),
                context_tags=interaction.metadata
            )
            
            # Update analytics
            self.analytics.track_interaction(interaction)
            
            # Check for highlight-worthy interactions
            if interaction.importance_score > 0.7:
                self._consider_interaction_highlight(interaction)
                
        except Exception as e:
            self.logger.error(f"Failed to process interaction: {e}")
            raise

    def process_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Process a stream event.
        
        Args:
            event_type: Type of event
            details: Event details
        """
        try:
            if not self.current_session_id:
                raise ValueError("No active stream session")
                
            # Get recent interactions for context
            recent_interactions = self.interaction_manager.get_recent_interactions()
            
            # Process through highlight tracker
            highlight = self.highlight_tracker.process_event(
                event_type=event_type,
                details=details,
                viewer_reactions=recent_interactions
            )
            
            # Log significant highlights
            if highlight and highlight.importance > 0.5:
                self.db.log_highlight(
                    session_id=self.current_session_id,
                    highlight_type=highlight.highlight_type.value,
                    description=highlight.description,
                    viewer_impact={'reactions': len(recent_interactions)},
                    significance=highlight.importance
                )
                
        except Exception as e:
            self.logger.error(f"Failed to process event: {e}")
            raise

    def get_session_data(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get data for a specific session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Session data dictionary
        """
        try:
            # Return current session data if requested
            if session_id == self.current_session_id:
                return self.session_data.copy()
                
            # Query database for historical session data
            analytics = self.db.get_session_analytics(session_id)
            if not analytics:
                raise ValueError(f"Session not found: {session_id}")
                
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get session data: {e}")
            raise

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all currently active stream sessions.
        
        Returns:
            List of active session dictionaries
        """
        try:
            return self.db.get_active_sessions()
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            raise

    def _consider_interaction_highlight(self, interaction) -> None:
        """Consider whether an interaction should create a highlight."""
        # Check if interaction is highlight-worthy
        if (interaction.interaction_type in 
            [InteractionType.DONATION, InteractionType.SUBSCRIPTION]):
            self.highlight_tracker.process_event(
                event_type="viewer_milestone",
                details={
                    'type': interaction.interaction_type.value,
                    'viewer': interaction.viewer_name,
                    'content': interaction.content
                },
                viewer_reactions=self.interaction_manager.get_recent_interactions()
            )
