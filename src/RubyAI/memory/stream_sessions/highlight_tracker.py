import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from enum import Enum

class HighlightType(Enum):
    """Types of stream highlights."""
    ACHIEVEMENT = "achievement"
    EPIC_MOMENT = "epic_moment"
    FUNNY_MOMENT = "funny_moment"
    HIGH_ENGAGEMENT = "high_engagement"
    EMOTIONAL_MOMENT = "emotional_moment"
    VIEWER_MILESTONE = "viewer_milestone"
    GAME_PROGRESS = "game_progress"
    COMMUNITY_MOMENT = "community_moment"

@dataclass
class StreamHighlight:
    """Represents a significant moment during the stream."""
    timestamp: datetime
    highlight_type: HighlightType
    description: str
    importance: float
    context: Dict[str, Any]
    viewer_reactions: List[Dict[str, Any]] = None
    clip_timestamp: Optional[str] = None
    tags: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert highlight to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'type': self.highlight_type.value,
            'description': self.description,
            'importance': self.importance,
            'context': self.context,
            'viewer_reactions': self.viewer_reactions,
            'clip_timestamp': self.clip_timestamp,
            'tags': self.tags or []
        }

class HighlightTracker:
    """
    Tracks and analyzes significant moments during streams.
    Identifies, categorizes, and stores stream highlights based on various triggers.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Highlight storage
        self.highlights: List[StreamHighlight] = []
        self.recent_events = deque(maxlen=50)  # Buffer for recent events
        
        # Engagement tracking
        self.engagement_buffer = deque(maxlen=300)  # 5 minutes at 1-second intervals
        self.viewer_reactions = {}  # Reactions per highlight
        
        # Pattern recognition
        self.highlight_patterns = {}  # Patterns in highlight generation
        self.viewer_preferences = {}  # What viewers find highlight-worthy
        
        # Context tracking
        self.current_context = {
            'game_state': None,
            'mood': 'neutral',
            'engagement_level': 0.5,
            'recent_achievements': []
        }

    def process_event(self, event_type: str, details: Dict[str, Any],
                     viewer_reactions: List[Dict[str, Any]] = None) -> Optional[StreamHighlight]:
        """
        Process a stream event and determine if it's highlight-worthy.
        
        Args:
            event_type: Type of event
            details: Event details
            viewer_reactions: Related viewer reactions as dictionaries
            
        Returns:
            StreamHighlight if event is significant, None otherwise
        """
        try:
            # Add to recent events
            self.recent_events.append({
                'type': event_type,
                'details': details,
                'timestamp': datetime.now()
            })
            
            # Calculate highlight potential
            importance = self._calculate_highlight_importance(event_type, details, viewer_reactions)
            
            # Create highlight if significant enough
            if importance > 0.7:  # Highlight threshold
                highlight = StreamHighlight(
                    timestamp=datetime.now(),
                    highlight_type=self._determine_highlight_type(event_type, details),
                    description=self._generate_description(event_type, details),
                    importance=importance,
                    context=self.current_context.copy(),
                    viewer_reactions=viewer_reactions,
                    tags=self._generate_tags(event_type, details)
                )
                
                self.highlights.append(highlight)
                self._update_patterns(highlight)
                
                return highlight
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to process event for highlights: {e}")
            raise

    def update_context(self, context_update: Dict[str, Any]) -> None:
        """Update current stream context."""
        self.current_context.update(context_update)

    def get_recent_highlights(self, count: int = 5) -> List[StreamHighlight]:
        """Get most recent highlights."""
        return sorted(self.highlights, key=lambda h: h.timestamp, reverse=True)[:count]

    def get_top_highlights(self, count: int = 5) -> List[StreamHighlight]:
        """Get top highlights by importance."""
        return sorted(self.highlights, key=lambda h: h.importance, reverse=True)[:count]

    def _calculate_highlight_importance(self, event_type: str, 
                                     details: Dict[str, Any],
                                     viewer_reactions: List[Dict[str, Any]] = None) -> float:
        """Calculate importance score for potential highlight."""
        importance = 0.0
        
        # Event type importance
        type_weights = {
            'achievement': 0.8,
            'boss_victory': 0.9,
            'funny_moment': 0.7,
            'skill_display': 0.8,
            'emotional_moment': 0.7,
            'community_event': 0.6
        }
        importance += type_weights.get(event_type, 0.5)
        
        # Viewer reaction importance
        if viewer_reactions:
            # Calculate reaction intensity
            reaction_count = len(viewer_reactions)
            positive_reactions = sum(1 for r in viewer_reactions 
                                  if r.get('type') == 'cheer' or r.get('count', 0) > 0)
            reaction_ratio = positive_reactions / reaction_count if reaction_count > 0 else 0
            
            importance += min(0.3, reaction_count / 20)  # Cap at 0.3 for 20+ reactions
            importance += reaction_ratio * 0.2
        
        # Context importance
        if self.current_context['engagement_level'] > 0.7:
            importance += 0.2
            
        # Rarity importance
        if event_type in self.highlight_patterns:
            frequency = self.highlight_patterns[event_type]['frequency']
            if frequency < 3:  # Rare events are more important
                importance += 0.2
                
        return min(1.0, importance)

    def _determine_highlight_type(self, event_type: str, 
                                details: Dict[str, Any]) -> HighlightType:
        """Determine the type of highlight."""
        if 'achievement' in event_type.lower():
            return HighlightType.ACHIEVEMENT
        elif 'boss' in event_type.lower() or 'victory' in event_type.lower():
            return HighlightType.EPIC_MOMENT
        elif 'funny' in event_type.lower() or 'laugh' in str(details).lower():
            return HighlightType.FUNNY_MOMENT
        elif 'viewer' in event_type.lower() or 'community' in event_type.lower():
            return HighlightType.COMMUNITY_MOMENT
        elif 'emotional' in event_type.lower():
            return HighlightType.EMOTIONAL_MOMENT
        elif 'progress' in event_type.lower():
            return HighlightType.GAME_PROGRESS
        elif self.current_context['engagement_level'] > 0.8:
            return HighlightType.HIGH_ENGAGEMENT
        else:
            return HighlightType.EPIC_MOMENT

    def _generate_description(self, event_type: str, details: Dict[str, Any]) -> str:
        """Generate human-readable description of the highlight."""
        # Start with event type
        description = event_type.replace('_', ' ').title()
        
        # Add relevant details
        if 'achievement' in details:
            description += f": Achieved {details['achievement']}"
        elif 'boss' in details:
            description += f": Defeated {details['boss']}"
        elif 'milestone' in details:
            description += f": {details['milestone']}"
            
        # Add context if relevant
        if self.current_context['game_state']:
            description += f" during {self.current_context['game_state']}"
            
        return description

    def _generate_tags(self, event_type: str, details: Dict[str, Any]) -> List[str]:
        """Generate relevant tags for the highlight."""
        tags = [event_type]  # Always include event type
        
        # Add game-related tags
        if 'game' in self.current_context:
            tags.append(self.current_context['game'])
        
        # Add mood-related tags
        if self.current_context['mood'] != 'neutral':
            tags.append(self.current_context['mood'])
            
        # Add detail-specific tags
        for key, value in details.items():
            if isinstance(value, str):
                tags.append(value.lower())
                
        # Add engagement tag if high
        if self.current_context['engagement_level'] > 0.7:
            tags.append('high_engagement')
            
        return list(set(tags))  # Remove duplicates

    def _update_patterns(self, highlight: StreamHighlight) -> None:
        """Update highlight patterns with new highlight."""
        highlight_type = highlight.highlight_type.value
        
        # Initialize pattern tracking if needed
        if highlight_type not in self.highlight_patterns:
            self.highlight_patterns[highlight_type] = {
                'frequency': 0,
                'avg_importance': 0.0,
                'common_tags': {},
                'viewer_engagement': []
            }
            
        pattern = self.highlight_patterns[highlight_type]
        
        # Update frequency
        pattern['frequency'] += 1
        
        # Update average importance
        old_avg = pattern['avg_importance']
        pattern['avg_importance'] = old_avg + (highlight.importance - old_avg) / pattern['frequency']
        
        # Update tag frequencies
        if highlight.tags:
            for tag in highlight.tags:
                pattern['common_tags'][tag] = pattern['common_tags'].get(tag, 0) + 1
                
        # Update viewer engagement
        if highlight.viewer_reactions:
            engagement = len(highlight.viewer_reactions)
            pattern['viewer_engagement'].append(engagement)
            
            # Keep only recent engagement data
            if len(pattern['viewer_engagement']) > 10:
                pattern['viewer_engagement'] = pattern['viewer_engagement'][-10:]

    def analyze_highlight_trends(self) -> Dict[str, Any]:
        """Analyze trends in stream highlights."""
        if not self.highlights:
            return {}
            
        analysis = {
            'total_highlights': len(self.highlights),
            'highlight_frequency': {},  # Highlights per hour
            'popular_types': {},        # Most common types
            'engagement_correlation': {},  # Correlation with viewer engagement
            'peak_times': []            # Times with most highlights
        }
        
        # Calculate highlight frequency
        stream_hours = (self.highlights[-1].timestamp - 
                       self.highlights[0].timestamp).total_seconds() / 3600
        if stream_hours > 0:
            analysis['highlight_frequency'] = len(self.highlights) / stream_hours
            
        # Analyze types
        type_counts = {}
        for highlight in self.highlights:
            type_counts[highlight.highlight_type.value] = \
                type_counts.get(highlight.highlight_type.value, 0) + 1
                
        analysis['popular_types'] = dict(sorted(
            type_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        # Analyze engagement correlation
        for highlight_type in type_counts:
            relevant_highlights = [h for h in self.highlights 
                                 if h.highlight_type.value == highlight_type]
            if relevant_highlights:
                avg_reactions = sum(
                    len(h.viewer_reactions) if h.viewer_reactions else 0 
                    for h in relevant_highlights
                ) / len(relevant_highlights)
                analysis['engagement_correlation'][highlight_type] = avg_reactions
                
        # Find peak times
        hour_counts = {}
        for highlight in self.highlights:
            hour = highlight.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
        analysis['peak_times'] = sorted(
            hour_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return analysis
