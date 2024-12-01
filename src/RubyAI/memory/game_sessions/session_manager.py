import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
from collections import deque
import json

from ...integration.database.game_queries import GameQueries
from .event_tracker import EventTracker, GameEvent, EventPriority

class Memory:
    """Represents a formed memory from game experiences."""
    def __init__(self, event: GameEvent, importance: float):
        self.id = uuid4()
        self.core_event = event
        self.importance = importance
        self.recall_count = 0
        self.last_recalled = None
        self.associated_memories: set[UUID] = set()
        self.emotional_context = {}
        self.reinforcement_level = 1.0  # Starts strong, decays over time
        self.created_at = datetime.now()

    def reinforce(self, strength: float = 0.2) -> None:
        """
        Strengthen the memory through recall or related experiences.
        Increases reinforcement level by the given strength.
        """
        self.recall_count += 1
        self.last_recalled = datetime.now()
        # Allow reinforcement to exceed 1.0 to show improvement
        self.reinforcement_level += strength

    def decay(self, factor: float = 0.01) -> None:
        """Natural memory decay over time."""
        time_since_recall = datetime.now() - (self.last_recalled or self.created_at)
        decay_amount = factor * time_since_recall.total_seconds() / 86400  # Daily decay
        self.reinforcement_level = max(0.1, self.reinforcement_level - decay_amount)

class GameSessionManager:
    """Manages Ruby's game session memories and experiences."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = GameQueries()
        self.event_tracker = EventTracker()
        
        # Memory Systems
        self.working_memory = deque(maxlen=5)     # Current focus
        self.short_term = deque(maxlen=50)        # Recent experiences
        self.long_term: Dict[UUID, Memory] = {}   # Consolidated memories
        
        # Active Session
        self.current_session_id: Optional[UUID] = None
        self.session_start: Optional[datetime] = None
        self.session_context: Dict[str, Any] = {}

    def start_session(self, game_name: str, context: Dict[str, Any]) -> UUID:
        """Start a new game session."""
        try:
            # Create database record
            self.current_session_id = self.db.create_session(
                game_name=game_name,
                game_mode=context.get('mode'),
                difficulty=context.get('difficulty')
            )
            
            # Initialize session state
            self.session_start = datetime.now()
            self.session_context = context
            
            # Clear working and short-term memory for new session
            self.working_memory.clear()
            self.short_term.clear()
            
            self.logger.info(f"Started new game session: {game_name}")
            return self.current_session_id
            
        except Exception as e:
            self.logger.error(f"Failed to start game session: {e}")
            raise

    def process_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Process a game event and form memories."""
        try:
            # Add current context to event
            context = {
                'session_id': self.current_session_id,
                'game_context': self.session_context,
                'emotional_state': self.event_tracker.get_emotional_state(),
                'current_focus': [e.event_type for e in self.working_memory]
            }
            
            # Process through event tracker
            event = self.event_tracker.process_event(event_type, details, context)
            
            # Update working memory based on priority
            if event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]:
                self.working_memory.append(event)
            
            # Add to short-term memory
            self.short_term.append(event)
            
            # Consider for long-term memory formation
            self._form_memories(event)
            
            # Log to database if significant
            if event.priority.value >= EventPriority.MEDIUM.value:
                self.db.log_event(
                    session_id=self.current_session_id,
                    event_type=event_type,
                    category=event.priority.name,
                    data=details,
                    impact_score=event.emotional_impact
                )
                
        except Exception as e:
            self.logger.error(f"Failed to process event: {e}")
            raise

    def _form_memories(self, event: GameEvent) -> None:
        """Form long-term memories from experiences."""
        try:
            # Calculate memory importance
            importance = self._calculate_memory_importance(event)
            
            # Form long-term memory if important enough
            if importance >= 0.3:  # Memory formation threshold
                memory = Memory(event, importance)
                
                # Add emotional context
                memory.emotional_context = self.event_tracker.get_emotional_state()
                
                # Find and link associated memories
                self._form_associations(memory)
                
                # Store in long-term memory
                self.long_term[memory.id] = memory
                
        except Exception as e:
            self.logger.error(f"Failed to form memory: {e}")
            raise

    def _calculate_memory_importance(self, event: GameEvent) -> float:
        """Calculate how important an event is for memory formation."""
        importance = 0.0
        
        # Event priority contribution
        importance += event.priority.value * 0.25
        
        # Emotional impact contribution
        importance += abs(event.emotional_impact) * 0.25
        
        # Novelty contribution (from event tracker)
        novelty = self.event_tracker._calculate_novelty(event.event_type)
        importance += novelty * 0.25
        
        # Context relevance
        context_relevance = self.event_tracker._calculate_context_relevance(event.context)
        importance += context_relevance * 0.25
        
        return min(1.0, importance)

    def _form_associations(self, memory: Memory) -> None:
        """Form associations between memories."""
        for existing_id, existing_memory in self.long_term.items():
            similarity = self._calculate_memory_similarity(memory, existing_memory)
            if similarity >= 0.5:  # Association threshold
                memory.associated_memories.add(existing_id)
                existing_memory.associated_memories.add(memory.id)

    def _calculate_memory_similarity(self, memory1: Memory, memory2: Memory) -> float:
        """Calculate similarity between two memories."""
        similarity = 0.0
        
        # Event type similarity
        if memory1.core_event.event_type == memory2.core_event.event_type:
            similarity += 0.3
            
        # Context similarity
        common_context = set(memory1.core_event.context.keys()) & set(memory2.core_event.context.keys())
        similarity += len(common_context) * 0.1
        
        # Emotional similarity
        emotional_diff = sum(abs(memory1.emotional_context.get(k, 0) - memory2.emotional_context.get(k, 0))
                           for k in set(memory1.emotional_context) | set(memory2.emotional_context))
        similarity += (1 - emotional_diff/4) * 0.3  # Normalize by number of emotions
        
        # Temporal proximity
        time_diff = abs((memory1.created_at - memory2.created_at).total_seconds())
        if time_diff < 3600:  # Within an hour
            similarity += 0.3 * (1 - time_diff/3600)
            
        return min(1.0, similarity)

    def recall_memory(self, memory_id: UUID) -> Optional[Memory]:
        """Recall a specific memory, reinforcing it."""
        memory = self.long_term.get(memory_id)
        if memory:
            memory.reinforce()
            # Also reinforce associated memories, but weaker
            for associated_id in memory.associated_memories:
                if associated_memory := self.long_term.get(associated_id):
                    associated_memory.reinforce(strength=0.1)
            return memory
        return None

    def get_associated_memories(self, memory_id: UUID) -> List[Memory]:
        """Get memories associated with a specific memory."""
        memory = self.long_term.get(memory_id)
        if not memory:
            return []
        return [self.long_term[m_id] for m_id in memory.associated_memories
                if m_id in self.long_term]

    def get_recent_memories(self, count: int = 5) -> List[Memory]:
        """Get most recent memories."""
        return sorted(self.long_term.values(), 
                     key=lambda m: m.created_at,
                     reverse=True)[:count]

    def get_strongest_memories(self, count: int = 5) -> List[Memory]:
        """Get strongest memories based on reinforcement and importance."""
        return sorted(self.long_term.values(),
                     key=lambda m: m.reinforcement_level * m.importance,
                     reverse=True)[:count]

    def end_session(self) -> None:
        """End the current game session."""
        if not self.current_session_id:
            return
            
        try:
            # Calculate session summary
            summary = {
                'duration': (datetime.now() - self.session_start).total_seconds(),
                'memory_count': len(self.long_term),
                'significant_events': len([m for m in self.long_term.values() 
                                        if m.importance > 0.7]),
                'emotional_journey': self.event_tracker.get_emotional_state(),
                'key_memories': [
                    {
                        'type': m.core_event.event_type,
                        'importance': m.importance,
                        'emotional_impact': m.core_event.emotional_impact
                    }
                    for m in self.get_strongest_memories(3)
                ]
            }
            
            # Update database
            self.db.end_session(self.current_session_id, summary)
            
            # Clear session state
            self.current_session_id = None
            self.session_start = None
            self.session_context = {}
            
            self.logger.info("Game session ended successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to end game session: {e}")
            raise
