import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from enum import Enum

class EventPriority(Enum):
    """Priority levels for events affecting memory formation."""
    LOW = 1      # Routine events
    MEDIUM = 2   # Notable events
    HIGH = 3     # Important events
    CRITICAL = 4 # Must-remember events

@dataclass
class GameEvent:
    """Represents a single game event with context."""
    timestamp: datetime
    event_type: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    priority: EventPriority
    emotional_impact: float  # -1.0 to 1.0
    related_events: List[str] = None

class EventTracker:
    """
    Tracks and processes game events in real-time, similar to human attention and immediate memory.
    This is the first stage of memory formation, handling events before they become short or long-term memories.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Immediate sensory buffer (like human sensory memory)
        self.sensory_buffer = deque(maxlen=20)  # Very short-term, raw events
        
        # Active attention buffer (like human attention span)
        self.attention_buffer = deque(maxlen=5)  # Currently focused events
        
        # Recent event patterns (for quick pattern recognition)
        self.pattern_buffer: Dict[str, List[GameEvent]] = {}
        
        # Event importance tracking
        self.event_frequency: Dict[str, int] = {}
        self.event_patterns: Dict[str, List[Tuple[str, datetime]]] = {}
        
        # Emotional state influence
        self.current_emotional_state: Dict[str, float] = {
            'excitement': 0.0,
            'frustration': 0.0,
            'satisfaction': 0.0,
            'curiosity': 0.0
        }

        # Event type priority mappings
        self.event_priorities = {
            'achievement': EventPriority.HIGH,
            'boss_fight': EventPriority.CRITICAL,
            'death': EventPriority.HIGH,
            'discovery': EventPriority.MEDIUM,
            'combat': EventPriority.MEDIUM,
            'interaction': EventPriority.MEDIUM,
            'mining': EventPriority.LOW,
            'crafting': EventPriority.LOW,
            'movement': EventPriority.LOW
        }

        # Emotional history for tracking growth
        self.emotional_history: List[Tuple[datetime, Dict[str, float]]] = []

        # Current goals and focus
        self.current_goals: List[str] = []
        self.current_focus: Optional[str] = None

    def process_event(self, event_type: str, details: Dict[str, Any], 
                     context: Dict[str, Any]) -> GameEvent:
        """Process an incoming game event in real-time."""
        # Calculate event priority based on multiple factors
        priority = self._calculate_priority(event_type, details, context)
        
        # Calculate emotional impact
        emotional_impact = self._calculate_emotional_impact(event_type, details)
        
        # Create event object
        event = GameEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            details=details,
            context=context,
            priority=priority,
            emotional_impact=emotional_impact,
            related_events=self._find_related_events(event_type, details)
        )
        
        # Add to sensory buffer
        self.sensory_buffer.append(event)
        
        # Update attention buffer based on priority
        if priority.value >= EventPriority.MEDIUM.value:
            self.attention_buffer.append(event)
        
        # Update pattern recognition
        self._update_patterns(event)
        
        # Update emotional state
        self._update_emotional_state(event_type, emotional_impact)
        
        return event

    def _calculate_priority(self, event_type: str, details: Dict[str, Any],
                          context: Dict[str, Any]) -> EventPriority:
        """Calculate event priority based on multiple factors."""
        # Base priority from event type
        base_priority = self.event_priorities.get(event_type, EventPriority.LOW)
        
        # Adjust based on details
        if 'difficulty' in details and details['difficulty'] > 0.7:
            base_priority = EventPriority(min(4, base_priority.value + 1))
        if 'rarity' in details and details.get('rarity') == 'rare':
            base_priority = EventPriority(min(4, base_priority.value + 1))
        if 'first_time' in details and details['first_time']:
            base_priority = EventPriority(min(4, base_priority.value + 1))
            
        # Context adjustments
        if context.get('critical_moment'):
            base_priority = EventPriority(min(4, base_priority.value + 1))
        if context.get('goal_related'):
            base_priority = EventPriority(min(4, base_priority.value + 1))
            
        return base_priority

    def _calculate_emotional_impact(self, event_type: str, 
                                  details: Dict[str, Any]) -> float:
        """Calculate the emotional impact of an event."""
        impact = 0.0
        
        # Event-specific impacts
        if event_type == 'achievement':
            impact += 0.7
        elif event_type == 'death':
            impact -= 0.6
        elif event_type == 'discovery':
            impact += 0.4
        elif event_type == 'combat':
            impact += 0.3 if details.get('outcome') == 'victory' else -0.3
        elif event_type == 'boss_fight':
            impact += 0.8 if details.get('outcome') == 'victory' else -0.5
        elif event_type == 'interaction':
            impact += 0.4 if details.get('outcome') == 'positive' else -0.2
        
        # Detail-specific impacts
        if 'difficulty' in details:
            impact += details['difficulty'] * 0.2
        if 'reward' in details:
            impact += 0.3
        if details.get('items_lost'):
            impact -= 0.4
            
        return max(-1.0, min(1.0, impact))

    def _calculate_novelty(self, event_type: str) -> float:
        """Calculate how novel an event is based on frequency."""
        frequency = self.event_frequency.get(event_type, 0)
        if frequency == 0:
            return 1.0  # First time seeing this event
        return 1.0 / (1.0 + frequency * 0.1)  # Decay with frequency

    def _calculate_context_relevance(self, context: Dict[str, Any]) -> float:
        """Calculate how relevant an event is to current context."""
        relevance = 0.0
        
        # Goal relevance
        if any(goal in str(context) for goal in self.current_goals):
            relevance += 0.4
            
        # Focus relevance
        if self.current_focus and self.current_focus in str(context):
            relevance += 0.3
            
        # Emotional state relevance
        if 'emotional_state' in context:
            current_emotions = set(k for k, v in self.current_emotional_state.items() if v > 0.5)
            context_emotions = set(str(context['emotional_state']).split())
            emotion_overlap = len(current_emotions & context_emotions)
            relevance += 0.3 * (emotion_overlap / max(1, len(current_emotions)))
            
        # Critical moment
        if context.get('critical_moment'):
            relevance += 0.4
            
        return min(1.0, relevance)

    def _update_emotional_state(self, event_type: str, impact: float) -> None:
        """Update emotional state based on event and impact."""
        # Excitement changes
        if event_type in ['achievement', 'discovery', 'boss_fight']:
            self.current_emotional_state['excitement'] = min(1.0, 
                self.current_emotional_state['excitement'] + abs(impact) * 0.5)
        
        # Frustration changes
        if impact < 0 or event_type in ['death', 'failure']:
            self.current_emotional_state['frustration'] = min(1.0,
                self.current_emotional_state['frustration'] + abs(impact) * 0.4)
        
        # Satisfaction changes
        if impact > 0:
            self.current_emotional_state['satisfaction'] = min(1.0,
                self.current_emotional_state['satisfaction'] + impact * 0.3)
        
        # Curiosity changes
        if event_type in ['discovery', 'exploration']:
            self.current_emotional_state['curiosity'] = min(1.0,
                self.current_emotional_state['curiosity'] + 0.2)

        # Natural decay
        for emotion in self.current_emotional_state:
            if emotion != 'frustration' or impact >= 0:  # Don't decay frustration on negative events
                self.current_emotional_state[emotion] *= 0.95

        # Record emotional state for history
        self.emotional_history.append((datetime.now(), self.current_emotional_state.copy()))

    def _update_patterns(self, event: GameEvent) -> None:
        """Update pattern recognition based on new event."""
        event_key = event.event_type
        
        if event_key not in self.pattern_buffer:
            self.pattern_buffer[event_key] = []
            
        self.pattern_buffer[event_key].append(event)
        
        # Update event frequency for novelty calculation
        self.event_frequency[event_key] = self.event_frequency.get(event_key, 0) + 1
        
        # Maintain pattern buffer size
        if len(self.pattern_buffer[event_key]) > 10:
            self.pattern_buffer[event_key].pop(0)
            
        # Look for sequences
        self._analyze_event_sequence(event)

    def _analyze_event_sequence(self, event: GameEvent) -> None:
        """Analyze event sequences for pattern recognition."""
        recent_events = list(self.sensory_buffer)
        if len(recent_events) >= 3:
            sequence = tuple(e.event_type for e in recent_events[-3:])
            if sequence not in self.event_patterns:
                self.event_patterns[sequence] = []
            self.event_patterns[sequence].append((event.event_type, event.timestamp))

    def get_current_focus(self) -> Optional[GameEvent]:
        """Get the current focus of attention."""
        return self.attention_buffer[-1] if self.attention_buffer else None

    def get_recent_patterns(self) -> Dict[str, List[GameEvent]]:
        """Get recently recognized patterns."""
        return self.pattern_buffer

    def get_emotional_state(self) -> Dict[str, float]:
        """Get current emotional state."""
        return self.current_emotional_state.copy()

    def get_emotional_history(self) -> List[Tuple[datetime, Dict[str, float]]]:
        """Get emotional state history."""
        return self.emotional_history.copy()

    def _find_related_events(self, event_type: str, 
                           details: Dict[str, Any]) -> List[str]:
        """Find events related to the current event."""
        related = []
        for past_event in self.sensory_buffer:
            if past_event.event_type == event_type:
                continue
            if any(key in past_event.details for key in details.keys()):
                related.append(past_event.event_type)
        return related[:5]  # Limit to 5 most recent related events

    def set_current_goals(self, goals: List[str]) -> None:
        """Set current goals for context relevance calculation."""
        self.current_goals = goals

    def set_current_focus(self, focus: str) -> None:
        """Set current focus for context relevance calculation."""
        self.current_focus = focus
