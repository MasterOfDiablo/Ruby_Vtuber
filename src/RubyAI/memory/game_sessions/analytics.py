import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from uuid import UUID

from .session_manager import GameSessionManager, Memory
from .event_tracker import EventPriority, GameEvent

class GameAnalytics:
    """
    Analyzes Ruby's game memories and learning patterns.
    Helps understand how Ruby's experiences shape her behavior and decision-making.
    """

    def __init__(self, session_manager: GameSessionManager):
        self.logger = logging.getLogger(__name__)
        self.session_manager = session_manager
        
        # Analytics Storage
        self.learning_patterns: Dict[str, List[float]] = defaultdict(list)
        self.emotional_trends: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.memory_formation_rates: List[Tuple[datetime, int]] = []
        self.event_correlations: Dict[Tuple[str, str], float] = {}
        
        # Performance Metrics
        self.success_rates: Dict[str, List[float]] = defaultdict(list)
        self.adaptation_scores: Dict[str, float] = {}
        self.engagement_levels: List[Tuple[datetime, float]] = []

        # Response pattern tracking
        self.emotional_responses: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

        # Decision tracking
        self.decision_outcomes: Dict[str, List[bool]] = defaultdict(list)
        self.decision_contexts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def analyze_memory_formation(self) -> Dict[str, Any]:
        """Analyze how Ruby forms and retains memories."""
        memories = list(self.session_manager.long_term.values())
        
        # Memory formation analysis
        formation_analysis = {
            'total_memories': len(memories),
            'memory_importance_distribution': self.analyze_importance_distribution(memories),
            'retention_rates': self.analyze_retention_rates(memories),
            'emotional_impact': self.analyze_emotional_impact(memories),
            'memory_categories': self.analyze_memory_categories(memories)
        }
        
        # Track formation rate
        self.memory_formation_rates.append(
            (datetime.now(), len(memories))
        )
        
        return formation_analysis

    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """Analyze how Ruby learns and adapts from experiences."""
        # Analyze success rates over time
        learning_progress = {}
        for event_type, rates in self.success_rates.items():
            if len(rates) < 2:
                continue
            
            learning_progress[event_type] = {
                'initial_success': rates[0],
                'current_success': rates[-1],
                'improvement': rates[-1] - rates[0],
                'trend': self.calculate_trend(rates),
                'consistency': 1.0 - float(np.std(rates))
            }

        # Analyze adaptation scores
        adaptation_metrics = {
            event_type: {
                'score': score,
                'relative_performance': score / max(self.adaptation_scores.values())
                if self.adaptation_scores else 0.0
            }
            for event_type, score in self.adaptation_scores.items()
        }

        # Analyze behavior changes
        behavior_changes = {}
        for event_type, contexts in self.decision_contexts.items():
            if len(contexts) < 2:
                continue
            
            # Extract strategy changes
            strategies = [ctx.get('strategy', 'unknown') for ctx in contexts]
            strategy_changes = sum(1 for i in range(len(strategies)-1) 
                                if strategies[i] != strategies[i+1])
            
            # Calculate adaptation rate
            outcomes = self.decision_outcomes.get(event_type, [])
            if outcomes:
                success_after_change = sum(1 for i in range(len(strategies)-1)
                                         if strategies[i] != strategies[i+1] 
                                         and i+1 < len(outcomes) and outcomes[i+1])
                adaptation_success = (success_after_change / strategy_changes 
                                   if strategy_changes > 0 else 0.0)
            else:
                adaptation_success = 0.0
            
            behavior_changes[event_type] = {
                'strategy_changes': strategy_changes,
                'adaptation_success': adaptation_success,
                'learning_rate': self.calculate_trend(
                    [ctx.get('success_rate', 0.0) for ctx in contexts]
                )
            }

        return {
            'learning_progress': learning_progress,
            'adaptation_metrics': adaptation_metrics,
            'behavior_changes': behavior_changes,
            'identified_patterns': self.analyze_event_patterns()
        }

    def analyze_event_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in event sequences."""
        patterns = {}
        event_tracker = self.session_manager.event_tracker
        
        # Analyze patterns from event tracker
        for event_type, events in event_tracker.pattern_buffer.items():
            if len(events) < 2:
                continue
            
            # Calculate time intervals between events
            intervals = []
            for i in range(1, len(events)):
                interval = (events[i].timestamp - events[i-1].timestamp).total_seconds()
                intervals.append(interval)
            
            patterns[event_type] = {
                'frequency': len(events),
                'average_interval': float(np.mean(intervals)) if intervals else 0,
                'consistency': float(np.std(intervals)) if intervals else 0,
                'trend': self.calculate_trend([e.emotional_impact for e in events])
            }
        
        return patterns

    def analyze_importance_distribution(self, memories: List[Memory]) -> Dict[str, float]:
        """Analyze the distribution of memory importance."""
        if not memories:
            return {}
            
        importance_values = [m.importance for m in memories]
        return {
            'mean': float(np.mean(importance_values)),
            'median': float(np.median(importance_values)),
            'std': float(np.std(importance_values)),
            'quartiles': [float(q) for q in np.percentile(importance_values, [25, 50, 75])]
        }

    def analyze_retention_rates(self, memories: List[Memory]) -> Dict[str, float]:
        """Analyze how well memories are retained over time."""
        if not memories:
            return {}
            
        retention_levels = [m.reinforcement_level for m in memories]
        time_periods = [(datetime.now() - m.created_at).total_seconds() / 86400 
                       for m in memories]  # Convert to days
        
        return {
            'average_retention': float(np.mean(retention_levels)),
            'retention_by_age': self.calculate_retention_by_age(
                retention_levels, time_periods
            ),
            'decay_rate': self.calculate_decay_rate(retention_levels, time_periods)
        }

    def calculate_retention_by_age(self, retention_levels: List[float],
                                 time_periods: List[float]) -> Dict[str, float]:
        """Calculate retention rates by memory age."""
        if not retention_levels or not time_periods:
            return {}
            
        # Group memories by age
        age_groups = {
            'recent': [],    # Less than 1 day
            'short': [],     # 1-7 days
            'medium': [],    # 7-30 days
            'long': []       # More than 30 days
        }
        
        for retention, age in zip(retention_levels, time_periods):
            if age < 1:
                age_groups['recent'].append(retention)
            elif age < 7:
                age_groups['short'].append(retention)
            elif age < 30:
                age_groups['medium'].append(retention)
            else:
                age_groups['long'].append(retention)
                
        return {
            age: float(np.mean(rates)) if rates else 0.0
            for age, rates in age_groups.items()
        }

    def calculate_decay_rate(self, retention_levels: List[float],
                           time_periods: List[float]) -> float:
        """Calculate the rate of memory decay over time."""
        if len(retention_levels) < 2 or len(time_periods) < 2:
            return 0.0
            
        # Use exponential decay model
        x = np.array(time_periods)
        y = np.array(retention_levels)
        
        # ln(y) = ln(y0) - λt
        log_y = np.log(y + 1e-10)  # Add small constant to avoid log(0)
        slope, _ = np.polyfit(x, log_y, 1)
        
        return float(-slope)  # Return decay rate λ

    def calculate_trend(self, values: List[float]) -> float:
        """Calculate the trend in a series of values."""
        if len(values) < 2:
            return 0.0
            
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return float(slope)

    def analyze_emotional_impact(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze the emotional impact of memories."""
        emotional_impacts = [m.core_event.emotional_impact for m in memories]
        emotional_contexts = [m.emotional_context for m in memories]
        
        return {
            'impact_distribution': {
                'positive': len([i for i in emotional_impacts if i > 0]),
                'neutral': len([i for i in emotional_impacts if i == 0]),
                'negative': len([i for i in emotional_impacts if i < 0])
            },
            'average_impact': float(np.mean(emotional_impacts)) if emotional_impacts else 0,
            'emotional_complexity': self.calculate_emotional_complexity(
                emotional_contexts
            )
        }

    def analyze_memory_categories(self, memories: List[Memory]) -> Dict[str, Any]:
        """Categorize memories by type, priority, and impact."""
        categories = defaultdict(int)
        priority_dist = defaultdict(int)
        impact_dist = {
            'high_impact': 0,
            'medium_impact': 0,
            'low_impact': 0
        }
        
        for memory in memories:
            # Categorize by event type
            event_type = memory.core_event.event_type
            categories[event_type] += 1
            
            # Categorize by priority
            priority_dist[memory.core_event.priority.name] += 1
            
            # Categorize by impact
            impact = abs(memory.core_event.emotional_impact)
            if impact > 0.7:
                impact_dist['high_impact'] += 1
            elif impact > 0.3:
                impact_dist['medium_impact'] += 1
            else:
                impact_dist['low_impact'] += 1
        
        return {
            'event_types': dict(categories),
            'priority_distribution': dict(priority_dist),
            'impact_distribution': impact_dist
        }

    def analyze_emotional_intelligence(self) -> Dict[str, Any]:
        """Analyze Ruby's emotional understanding and responses."""
        current_state = self.session_manager.event_tracker.get_emotional_state()
        emotional_history = self.session_manager.event_tracker.get_emotional_history()
        
        # Calculate emotional growth
        emotional_growth = {}
        if emotional_history:
            for emotion in current_state.keys():
                values = [state[emotion] for _, state in emotional_history]
                if len(values) >= 2:
                    emotional_growth[emotion] = {
                        'start_value': values[0],
                        'current_value': values[-1],
                        'change': values[-1] - values[0],
                        'volatility': float(np.std(values)),
                        'trend': self.calculate_trend(values)
                    }
        
        return {
            'current_state': current_state,
            'emotional_stability': self.calculate_emotional_stability(emotional_history),
            'emotional_growth': emotional_growth,
            'response_patterns': self.analyze_emotional_responses()
        }

    def analyze_decision_making(self) -> Dict[str, Any]:
        """Analyze how memories influence Ruby's decisions."""
        # Initialize with default values
        self.decision_outcomes.setdefault('general', [True])  # Ensure at least one outcome exists
        self.decision_contexts.setdefault('general', [{'experience_level': 0.5}])
        
        return {
            'decision_factors': self.analyze_decision_factors(),
            'memory_influence': self.analyze_memory_influence(),
            'confidence_levels': self.analyze_confidence_levels(),
            'risk_assessment': self.analyze_risk_patterns()
        }

    def analyze_emotional_responses(self) -> Dict[str, Any]:
        """Analyze patterns in emotional responses to different events."""
        response_analysis = {}
        
        # Get recent emotional responses
        for event_type, responses in self.emotional_responses.items():
            if len(responses) < 2:
                continue
                
            # Calculate response consistency
            emotions, intensities = zip(*responses)
            unique_emotions = len(set(emotions))
            avg_intensity = float(np.mean(intensities))
            intensity_std = float(np.std(intensities))
            
            response_analysis[event_type] = {
                'primary_emotion': max(set(emotions), key=emotions.count),
                'response_variety': unique_emotions,
                'average_intensity': avg_intensity,
                'consistency': 1.0 - (intensity_std / max(1.0, avg_intensity)),
                'recent_trend': self.calculate_trend(intensities)
            }
            
        return response_analysis

    def analyze_decision_factors(self) -> Dict[str, float]:
        """Analyze factors influencing decisions."""
        if not self.decision_contexts:
            return {}
            
        factors = {
            'emotional_weight': 0.0,
            'experience_weight': 0.0,
            'context_weight': 0.0,
            'success_weight': 0.0
        }
        
        total_decisions = sum(len(outcomes) for outcomes in self.decision_outcomes.values())
        if total_decisions == 0:
            return factors
            
        # Calculate weights based on decision outcomes
        for decision_type, outcomes in self.decision_outcomes.items():
            contexts = self.decision_contexts[decision_type]
            if not contexts or not outcomes:
                continue
                
            # Emotional influence
            emotional_states = [ctx.get('emotional_state', {}) for ctx in contexts]
            emotional_correlation = self.calculate_correlation(
                [sum(state.values()) for state in emotional_states],
                outcomes
            )
            factors['emotional_weight'] += abs(emotional_correlation)
            
            # Experience influence
            experience_levels = [ctx.get('experience_level', 0) for ctx in contexts]
            experience_correlation = self.calculate_correlation(experience_levels, outcomes)
            factors['experience_weight'] += abs(experience_correlation)
            
            # Context influence
            context_richness = [len(ctx) for ctx in contexts]
            context_correlation = self.calculate_correlation(context_richness, outcomes)
            factors['context_weight'] += abs(context_correlation)
            
            # Success history influence
            success_rates = self.success_rates.get(decision_type, [])
            if success_rates:
                factors['success_weight'] += sum(success_rates) / len(success_rates)
        
        # Normalize weights
        total_weight = sum(factors.values()) or 1.0
        return {k: v / total_weight for k, v in factors.items()}

    def analyze_memory_influence(self) -> Dict[str, float]:
        """Analyze how memories influence decision making."""
        memories = list(self.session_manager.long_term.values())
        if not memories:
            return {}
            
        influence_scores = {
            'recent_weight': self.calculate_recency_influence(memories),
            'emotional_weight': self.calculate_emotional_influence(memories),
            'success_weight': self.calculate_success_influence(memories),
            'pattern_weight': self.calculate_pattern_influence(memories)
        }
        
        # Normalize scores
        total = sum(influence_scores.values()) or 1.0
        return {k: v / total for k, v in influence_scores.items()}

    def analyze_confidence_levels(self) -> Dict[str, float]:
        """Analyze confidence in different types of decisions."""
        confidence_levels = {}
        
        for decision_type, outcomes in self.decision_outcomes.items():
            if not outcomes:
                continue
                
            # Calculate base confidence from success rate
            success_rate = sum(outcomes) / len(outcomes)
            
            # Adjust for experience
            experience_factor = len(outcomes) / 10  # Increases with more decisions
            
            # Adjust for consistency
            consistency = 1.0 - float(np.std(outcomes))
            
            confidence_levels[decision_type] = min(1.0, 
                success_rate * 0.4 + experience_factor * 0.3 + consistency * 0.3)
            
        return confidence_levels

    def analyze_risk_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in risk-taking behavior."""
        risk_analysis = {}
        
        for decision_type, contexts in self.decision_contexts.items():
            if not contexts or decision_type not in self.decision_outcomes:
                continue
                
            outcomes = self.decision_outcomes[decision_type]
            
            # Calculate risk levels from contexts
            risk_levels = [ctx.get('risk_level', 0.5) for ctx in contexts]
            
            risk_analysis[decision_type] = {
                'average_risk_level': float(np.mean(risk_levels)),
                'risk_success_correlation': self.calculate_correlation(risk_levels, outcomes),
                'risk_trend': self.calculate_trend(risk_levels),
                'adaptivity': self.calculate_risk_adaptivity(risk_levels, outcomes)
            }
            
        return risk_analysis

    def calculate_correlation(self, values1: List[float], values2: List[bool]) -> float:
        """Calculate correlation between a list of values and boolean outcomes."""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
            
        values1_arr = np.array(values1)
        values2_arr = np.array(values2, dtype=float)
        
        try:
            correlation = float(np.corrcoef(values1_arr, values2_arr)[0, 1])
            return 0.0 if np.isnan(correlation) else correlation
        except:
            return 0.0

    def calculate_recency_influence(self, memories: List[Memory]) -> float:
        """Calculate the influence of recent memories."""
        if not memories:
            return 0.0
            
        recall_times = [(m.last_recalled or m.created_at) for m in memories]
        time_diffs = [(datetime.now() - t).total_seconds() for t in recall_times]
        
        # More recent recalls have more influence
        recency_scores = [1.0 / (1.0 + td/3600) for td in time_diffs]  # Decay over hours
        return float(np.mean(recency_scores))

    def calculate_emotional_influence(self, memories: List[Memory]) -> float:
        """Calculate the influence of emotional memories."""
        if not memories:
            return 0.0
            
        emotional_impacts = [abs(m.core_event.emotional_impact) for m in memories]
        return float(np.mean(emotional_impacts))

    def calculate_success_influence(self, memories: List[Memory]) -> float:
        """Calculate the influence of successful outcomes."""
        if not memories:
            return 0.0
            
        success_scores = [
            1.0 if 'success' in str(m.core_event.details).lower() else 0.0
            for m in memories
        ]
        return float(np.mean(success_scores))

    def calculate_pattern_influence(self, memories: List[Memory]) -> float:
        """Calculate the influence of recognized patterns."""
        if not memories:
            return 0.0
            
        pattern_scores = [len(m.associated_memories) / 10 for m in memories]
        return float(np.mean(pattern_scores))

    def calculate_risk_adaptivity(self, risk_levels: List[float], 
                                outcomes: List[bool]) -> float:
        """Calculate how well risk-taking adapts to outcomes."""
        if len(risk_levels) < 2 or len(outcomes) < 2:
            return 0.0
            
        # Calculate risk level changes after outcomes
        adaptivity_scores = []
        for i in range(len(risk_levels) - 1):
            if not outcomes[i]:  # Failed outcome
                # Good adaptation: decreased risk after failure
                if risk_levels[i+1] < risk_levels[i]:
                    adaptivity_scores.append(1.0)
                else:
                    adaptivity_scores.append(0.0)
            else:  # Successful outcome
                # Good adaptation: maintained or slightly increased risk after success
                if risk_levels[i+1] >= risk_levels[i]:
                    adaptivity_scores.append(1.0)
                else:
                    adaptivity_scores.append(0.0)
                    
        return float(np.mean(adaptivity_scores)) if adaptivity_scores else 0.0

    def calculate_emotional_stability(self, 
                                   emotional_history: List[Tuple[datetime, Dict[str, float]]]) -> float:
        """Calculate emotional stability over time."""
        if not emotional_history:
            return 0.0
            
        stability_scores = []
        for emotion in emotional_history[0][1].keys():
            values = [state[emotion] for _, state in emotional_history]
            stability_scores.append(1.0 - float(np.std(values)))
            
        return float(np.mean(stability_scores))

    def calculate_emotional_complexity(self, emotional_contexts: List[Dict[str, float]]) -> float:
        """Calculate the complexity of emotional responses."""
        if not emotional_contexts:
            return 0.0
            
        # Calculate average number of distinct emotions per memory
        distinct_emotions = [
            len([v for v in context.values() if v > 0.1])
            for context in emotional_contexts
        ]
        
        return float(np.mean(distinct_emotions))

    def record_decision(self, decision_type: str, context: Dict[str, Any], 
                       outcome: bool) -> None:
        """Record a decision and its outcome."""
        self.decision_outcomes[decision_type].append(outcome)
        self.decision_contexts[decision_type].append(context)
        
        # Keep only recent decisions
        max_history = 100
        if len(self.decision_outcomes[decision_type]) > max_history:
            self.decision_outcomes[decision_type] = self.decision_outcomes[decision_type][-max_history:]
            self.decision_contexts[decision_type] = self.decision_contexts[decision_type][-max_history:]

    def update_success_rate(self, event_type: str, success: bool) -> None:
        """Update success rates for learning analysis."""
        self.success_rates[event_type].append(1.0 if success else 0.0)

    def update_adaptation_score(self, event_type: str, score: float) -> None:
        """Update adaptation scores."""
        self.adaptation_scores[event_type] = score

    def update_engagement(self, level: float) -> None:
        """Update engagement level tracking."""
        self.engagement_levels.append((datetime.now(), level))

    def record_emotional_response(self, event_type: str, emotion: str, intensity: float) -> None:
        """Record an emotional response to an event type."""
        self.emotional_responses[event_type].append((emotion, intensity))
        if len(self.emotional_responses[event_type]) > 100:  # Keep last 100 responses
            self.emotional_responses[event_type].pop(0)
