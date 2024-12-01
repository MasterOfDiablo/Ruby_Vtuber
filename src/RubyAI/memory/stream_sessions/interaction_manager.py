import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from enum import Enum
import json

class InteractionType(Enum):
    """Types of viewer interactions."""
    CHAT = "chat"
    COMMAND = "command"
    DONATION = "donation"
    FOLLOW = "follow"
    SUBSCRIPTION = "subscription"
    REACTION = "reaction"
    QUESTION = "question"
    GAME_SUGGESTION = "game_suggestion"
    STRATEGY_ADVICE = "strategy_advice"

@dataclass
class ViewerInteraction:
    """Represents a single viewer interaction."""
    timestamp: datetime
    viewer_id: str
    interaction_type: InteractionType
    content: str
    metadata: Dict[str, Any]
    sentiment_score: float = 0.0
    importance_score: float = 0.0
    context_tags: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'viewer_id': self.viewer_id,
            'type': self.interaction_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'sentiment_score': self.sentiment_score,
            'importance_score': self.importance_score,
            'context_tags': self.context_tags or []
        }

class InteractionManager:
    """
    Manages real-time viewer interactions during streams.
    Handles processing, prioritization, and context tracking of viewer interactions.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Real-time interaction buffers
        self.recent_interactions = deque(maxlen=100)  # Last 100 interactions
        self.active_conversations = {}  # Ongoing conversation threads
        self.viewer_states = {}  # Current state per viewer
        
        # Interaction patterns
        self.viewer_patterns = {}  # Patterns per viewer
        self.global_patterns = {}  # Overall interaction patterns
        
        # Context tracking
        self.current_context = {
            'topic': None,
            'mood': 'neutral',
            'engagement_level': 0.5,
            'active_viewers': set()
        }
        
        # Viewer relationship tracking
        self.viewer_relationships = {}
        
        # Priority queue for important interactions
        self.priority_queue = deque(maxlen=10)

    def process_interaction(self, viewer_id: str, interaction_type: InteractionType,
                          content: str, metadata: Dict[str, Any] = None) -> ViewerInteraction:
        """
        Process a new viewer interaction in real-time.
        
        Args:
            viewer_id: ID of the viewer
            interaction_type: Type of interaction
            content: Content of the interaction
            metadata: Additional interaction metadata
            
        Returns:
            Processed ViewerInteraction object
        """
        try:
            # Create interaction object
            interaction = ViewerInteraction(
                timestamp=datetime.now(),
                viewer_id=viewer_id,
                interaction_type=interaction_type,
                content=content,
                metadata=metadata or {},
                context_tags=self._extract_context_tags(content)
            )
            
            # Calculate sentiment and importance
            interaction.sentiment_score = self._analyze_sentiment(content)
            interaction.importance_score = self._calculate_importance(interaction)
            
            # Update buffers and patterns
            self._update_buffers(interaction)
            self._update_patterns(interaction)
            self._update_viewer_state(interaction)
            
            # Check for priority handling
            if interaction.importance_score > 0.7:
                self.priority_queue.append(interaction)
            
            return interaction
            
        except Exception as e:
            self.logger.error(f"Failed to process interaction: {e}")
            raise

    def get_recent_interactions(self, count: int = 10) -> List[ViewerInteraction]:
        """Get most recent interactions."""
        return list(self.recent_interactions)[-count:]

    def get_active_conversations(self) -> Dict[str, List[ViewerInteraction]]:
        """Get currently active conversation threads."""
        # Clean up old conversations
        current_time = datetime.now()
        active = {}
        
        for viewer, interactions in self.active_conversations.items():
            # Keep conversations active for last 5 minutes
            recent = [i for i in interactions 
                     if (current_time - i.timestamp).total_seconds() < 300]
            if recent:
                active[viewer] = recent
                
        self.active_conversations = active
        return active

    def get_viewer_context(self, viewer_id: str) -> Dict[str, Any]:
        """Get context for a specific viewer."""
        if viewer_id not in self.viewer_states:
            return self._create_new_viewer_state()
            
        return self.viewer_states[viewer_id]

    def update_stream_context(self, context_update: Dict[str, Any]) -> None:
        """Update current stream context."""
        self.current_context.update(context_update)
        
        # Update engagement metrics based on context
        if 'mood' in context_update:
            self._adjust_engagement_levels(context_update['mood'])

    def get_priority_interactions(self) -> List[ViewerInteraction]:
        """Get high-priority interactions that need immediate attention."""
        return list(self.priority_queue)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        return {
            'total_interactions': len(self.recent_interactions),
            'active_conversations': len(self.active_conversations),
            'unique_viewers': len(self.viewer_states),
            'priority_interactions': len(self.priority_queue),
            'engagement_level': self.current_context['engagement_level']
        }

    def _analyze_sentiment(self, content: str) -> float:
        """Analyze sentiment of interaction content."""
        # Simple keyword-based sentiment analysis
        positive_words = {'love', 'great', 'awesome', 'good', 'nice', 'thanks', 'pog', 'cool'}
        negative_words = {'bad', 'hate', 'awful', 'terrible', 'worst', 'stupid'}
        
        words = content.lower().split()
        sentiment = 0.0
        
        for word in words:
            if word in positive_words:
                sentiment += 0.2
            elif word in negative_words:
                sentiment -= 0.2
                
        return max(-1.0, min(1.0, sentiment))

    def _calculate_importance(self, interaction: ViewerInteraction) -> float:
        """Calculate importance score for an interaction."""
        importance = 0.0
        
        # Type-based importance
        type_weights = {
            InteractionType.DONATION: 0.8,
            InteractionType.SUBSCRIPTION: 0.7,
            InteractionType.QUESTION: 0.6,
            InteractionType.GAME_SUGGESTION: 0.5,
            InteractionType.STRATEGY_ADVICE: 0.5,
            InteractionType.CHAT: 0.3,
            InteractionType.REACTION: 0.2
        }
        importance += type_weights.get(interaction.interaction_type, 0.3)
        
        # Viewer relationship importance
        viewer_relationship = self.viewer_relationships.get(interaction.viewer_id, {})
        importance += viewer_relationship.get('trust_level', 0.0) * 0.2
        
        # Content-based importance
        if '?' in interaction.content:  # Questions are important
            importance += 0.2
        if '@Ruby' in interaction.content:  # Direct mentions
            importance += 0.3
            
        # Context-based importance
        if interaction.context_tags:
            if 'game_related' in interaction.context_tags:
                importance += 0.2
            if 'strategy' in interaction.context_tags:
                importance += 0.2
                
        return min(1.0, importance)

    def _extract_context_tags(self, content: str) -> List[str]:
        """Extract context tags from interaction content."""
        tags = []
        
        # Game-related context
        game_terms = {'play', 'game', 'level', 'boss', 'strategy'}
        if any(term in content.lower() for term in game_terms):
            tags.append('game_related')
            
        # Strategy context
        strategy_terms = {'try', 'should', 'maybe', 'better', 'instead'}
        if any(term in content.lower() for term in strategy_terms):
            tags.append('strategy')
            
        # Question context
        if '?' in content:
            tags.append('question')
            
        # Emotional context
        if any(emoji in content for emoji in ['😊', '😂', '❤️']):
            tags.append('emotional')
            
        return tags

    def _update_buffers(self, interaction: ViewerInteraction) -> None:
        """Update interaction buffers with new interaction."""
        # Add to recent interactions
        self.recent_interactions.append(interaction)
        
        # Update active conversations
        if interaction.viewer_id not in self.active_conversations:
            self.active_conversations[interaction.viewer_id] = []
        self.active_conversations[interaction.viewer_id].append(interaction)
        
        # Update active viewers
        self.current_context['active_viewers'].add(interaction.viewer_id)

    def _update_patterns(self, interaction: ViewerInteraction) -> None:
        """Update interaction patterns."""
        viewer = interaction.viewer_id
        
        # Initialize viewer patterns if needed
        if viewer not in self.viewer_patterns:
            self.viewer_patterns[viewer] = {
                'common_phrases': {},
                'interaction_times': [],
                'favorite_topics': set(),
                'interaction_frequency': {}
            }
        
        # Update patterns
        patterns = self.viewer_patterns[viewer]
        
        # Track common phrases
        words = interaction.content.lower().split()
        for word in words:
            patterns['common_phrases'][word] = patterns['common_phrases'].get(word, 0) + 1
            
        # Track interaction times
        patterns['interaction_times'].append(interaction.timestamp.hour)
        
        # Track topics
        if interaction.context_tags:
            patterns['favorite_topics'].update(interaction.context_tags)
            
        # Track interaction frequency
        interaction_type = interaction.interaction_type.value
        patterns['interaction_frequency'][interaction_type] = \
            patterns['interaction_frequency'].get(interaction_type, 0) + 1

    def _update_viewer_state(self, interaction: ViewerInteraction) -> None:
        """Update viewer state based on interaction."""
        viewer = interaction.viewer_id
        
        if viewer not in self.viewer_states:
            self.viewer_states[viewer] = self._create_new_viewer_state()
            
        state = self.viewer_states[viewer]
        
        # Update engagement
        state['last_interaction'] = interaction.timestamp
        state['interaction_count'] += 1
        
        # Update sentiment
        state['sentiment_history'].append(interaction.sentiment_score)
        if len(state['sentiment_history']) > 10:
            state['sentiment_history'] = state['sentiment_history'][-10:]
        
        # Update topics
        if interaction.context_tags:
            for tag in interaction.context_tags:
                state['topics'][tag] = state['topics'].get(tag, 0) + 1

    def _create_new_viewer_state(self) -> Dict[str, Any]:
        """Create initial state for a new viewer."""
        return {
            'first_seen': datetime.now(),
            'last_interaction': datetime.now(),
            'interaction_count': 0,
            'sentiment_history': [],
            'topics': {},
            'engagement_level': 0.0
        }

    def _adjust_engagement_levels(self, mood: str) -> None:
        """Adjust engagement levels based on stream mood."""
        adjustment = {
            'excited': 0.2,
            'happy': 0.1,
            'neutral': 0.0,
            'frustrated': -0.1,
            'bored': -0.2
        }.get(mood, 0.0)
        
        # Update global engagement
        self.current_context['engagement_level'] = max(0.0, min(1.0,
            self.current_context['engagement_level'] + adjustment))
        
        # Update individual viewer engagement
        for state in self.viewer_states.values():
            state['engagement_level'] = max(0.0, min(1.0,
                state['engagement_level'] + adjustment))
