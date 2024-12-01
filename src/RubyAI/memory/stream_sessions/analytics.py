import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from uuid import UUID

from ...integration.database.stream_queries import StreamQueries

class StreamAnalytics:
    """
    Analyzes stream data to provide insights about viewer engagement,
    interaction patterns, and stream performance.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = StreamQueries()
        
        # Real-time tracking
        self.engagement_levels: List[Tuple[datetime, float]] = []
        self.interaction_history: List[Dict[str, Any]] = []
        self.viewer_engagement: Dict[UUID, List[float]] = defaultdict(list)
        
        # Aggregated metrics
        self.peak_engagement = 0.0
        self.total_interactions = 0
        self.unique_viewers = set()
        self.interaction_types = defaultdict(int)
        
        # Time-based metrics
        self.hourly_stats = defaultdict(lambda: {
            'interactions': 0,
            'engagement': [],
            'unique_viewers': set()
        })

    def track_interaction(self, interaction: Dict[str, Any]) -> None:
        """Track a viewer interaction."""
        try:
            # Record interaction
            self.interaction_history.append(interaction)
            self.total_interactions += 1
            
            # Update metrics
            self.interaction_types[interaction['type']] += 1
            if 'viewer_id' in interaction:
                self.unique_viewers.add(interaction['viewer_id'])
            
            # Update hourly stats
            hour = datetime.now().hour
            self.hourly_stats[hour]['interactions'] += 1
            if 'viewer_id' in interaction:
                self.hourly_stats[hour]['unique_viewers'].add(interaction['viewer_id'])
            
            # Update viewer engagement
            if 'viewer_id' in interaction and 'engagement' in interaction:
                viewer_id = interaction['viewer_id']
                self.viewer_engagement[viewer_id].append(interaction['engagement'])
                
        except Exception as e:
            self.logger.error(f"Failed to track interaction: {e}")
            raise

    def track_engagement_level(self, level: float) -> None:
        """Track overall stream engagement level."""
        try:
            timestamp = datetime.now()
            self.engagement_levels.append((timestamp, level))
            
            # Update peak engagement
            self.peak_engagement = max(self.peak_engagement, level)
            
            # Update hourly stats
            hour = timestamp.hour
            self.hourly_stats[hour]['engagement'].append(level)
            
        except Exception as e:
            self.logger.error(f"Failed to track engagement level: {e}")
            raise

    def analyze_engagement_trends(self) -> Dict[str, Any]:
        """
        Analyze trends in engagement levels over time.
        
        Returns:
            Dictionary containing engagement trend analysis
        """
        if not self.engagement_levels:
            return {
                'average_engagement': 0.0,
                'peak_times': [],
                'trend': 0.0,
                'current_level': 0.0,
                'volatility': 0.0
            }
            
        # Calculate average engagement
        engagement_values = [level for _, level in self.engagement_levels]
        average_engagement = float(np.mean(engagement_values))
        
        # Find peak engagement times
        peak_times = []
        if len(self.engagement_levels) >= 2:
            # Group by hour
            hourly_engagement = defaultdict(list)
            for time, level in self.engagement_levels:
                hourly_engagement[time.hour].append(level)
                
            # Find top 3 hours by average engagement
            peak_times = sorted(
                [(hour, float(np.mean(levels))) for hour, levels in hourly_engagement.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
        
        # Calculate trend with numerical stability checks
        trend = 0.0
        if len(self.engagement_levels) >= 2:
            try:
                # Convert times to seconds from start
                start_time = self.engagement_levels[0][0]
                times = [(time - start_time).total_seconds() for time, _ in self.engagement_levels]
                levels = [level for _, level in self.engagement_levels]
                
                # Normalize times to prevent numerical issues
                max_time = max(times)
                if max_time > 0:
                    times = [t / max_time for t in times]
                
                # Add small noise to prevent exact duplicates
                times = np.array(times) + np.random.normal(0, 1e-10, len(times))
                levels = np.array(levels)
                
                # Calculate trend
                if len(set(times)) > 1:  # Ensure we have distinct x values
                    slope, _ = np.polyfit(times, levels, 1)
                    trend = float(slope)
            except Exception as e:
                self.logger.warning(f"Failed to calculate engagement trend: {e}")
                trend = 0.0
            
        return {
            'average_engagement': average_engagement,
            'peak_times': peak_times,
            'trend': trend,
            'current_level': engagement_values[-1] if engagement_values else 0.0,
            'volatility': float(np.std(engagement_values)) if len(engagement_values) > 1 else 0.0
        }

    def analyze_session(self, session_id: UUID) -> Dict[str, Any]:
        """Analyze current session data."""
        try:
            # Get session data from database
            session_data = self.db.get_session_analytics(session_id)
            if not session_data:
                raise ValueError(f"Session not found: {session_id}")
            
            # Combine with real-time data
            analysis = {
                'viewer_engagement': self._analyze_viewer_engagement(),
                'interaction_patterns': self._analyze_interaction_patterns(),
                'highlight_distribution': self._analyze_highlight_distribution(session_id),
                'performance_metrics': self._calculate_performance_metrics(),
                'historical_comparison': self._compare_to_historical(session_data)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze session: {e}")
            raise

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session metrics.
        
        Returns:
            Dictionary containing session summary
        """
        engagement_values = [level for _, level in self.engagement_levels]
        engagement_trends = self.analyze_engagement_trends()
        viewer_segments = self._analyze_viewer_engagement()
        
        return {
            'total_interactions': self.total_interactions,
            'unique_viewers': len(self.unique_viewers),
            'peak_engagement': self.peak_engagement,
            'average_engagement': float(np.mean(engagement_values)) if engagement_values else 0.0,
            'interaction_distribution': dict(self.interaction_types),
            'engagement_trend': engagement_trends['trend'],
            'viewer_segments': viewer_segments['segments']
        }

    def _analyze_viewer_engagement(self) -> Dict[str, Any]:
        """Analyze viewer engagement patterns."""
        segments = {
            'highly_engaged': 0,
            'moderately_engaged': 0,
            'low_engagement': 0
        }
        
        for viewer_levels in self.viewer_engagement.values():
            avg_engagement = float(np.mean(viewer_levels))
            if avg_engagement > 0.7:
                segments['highly_engaged'] += 1
            elif avg_engagement > 0.3:
                segments['moderately_engaged'] += 1
            else:
                segments['low_engagement'] += 1
                
        return {
            'segments': segments,
            'total_viewers': len(self.unique_viewers),
            'engagement_rate': len(self.viewer_engagement) / max(1, len(self.unique_viewers))
        }

    def _analyze_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in viewer interactions."""
        if not self.interaction_history:
            return {}
            
        patterns = {
            'type_distribution': dict(self.interaction_types),
            'hourly_activity': self._analyze_hourly_patterns(),
            'engagement_correlation': self._analyze_engagement_correlation()
        }
        
        return patterns

    def _analyze_highlight_distribution(self, session_id: UUID) -> Dict[str, Any]:
        """Analyze distribution of stream highlights."""
        try:
            highlights = self.db.get_session_highlights(session_id)
            
            if not highlights:
                return {}
                
            type_counts = defaultdict(int)
            significance_scores = defaultdict(list)
            
            for highlight in highlights:
                type_counts[highlight['highlight_type']] += 1
                significance_scores[highlight['highlight_type']].append(
                    highlight['significance_score']
                )
                
            return {
                'type_distribution': dict(type_counts),
                'average_significance': {
                    t: float(np.mean(scores))
                    for t, scores in significance_scores.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze highlights: {e}")
            return {}

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate various performance metrics."""
        return {
            'total_interactions': self.total_interactions,
            'unique_viewers': len(self.unique_viewers),
            'peak_engagement': self.peak_engagement,
            'interaction_rate': self.total_interactions / max(1, len(self.unique_viewers)),
            'engagement_stability': self._calculate_engagement_stability()
        }

    def _analyze_hourly_patterns(self) -> Dict[int, Dict[str, float]]:
        """Analyze patterns in hourly activity."""
        patterns = {}
        
        for hour, stats in self.hourly_stats.items():
            patterns[hour] = {
                'interaction_rate': stats['interactions'],
                'avg_engagement': float(np.mean(stats['engagement'])) if stats['engagement'] else 0.0,
                'unique_viewers': len(stats['unique_viewers'])
            }
            
        return patterns

    def _analyze_engagement_correlation(self) -> Dict[str, float]:
        """Analyze correlation between interaction types and engagement."""
        correlations = {}
        
        for interaction_type in self.interaction_types:
            type_engagements = [
                i.get('engagement', 0) for i in self.interaction_history
                if i['type'] == interaction_type
            ]
            if type_engagements:
                correlations[interaction_type] = float(np.mean(type_engagements))
                
        return correlations

    def _calculate_engagement_stability(self) -> float:
        """Calculate stability of engagement levels."""
        if len(self.engagement_levels) < 2:
            return 1.0
            
        engagement_values = [level for _, level in self.engagement_levels]
        return 1.0 - float(np.std(engagement_values))

    def _compare_to_historical(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current metrics to historical averages."""
        try:
            historical = self.db.get_session_analytics(current_data['session_id'])
            if not historical:
                return {}
                
            comparisons = {}
            metrics = ['unique_viewers', 'total_interactions', 'peak_engagement']
            
            for metric in metrics:
                if metric in historical and metric in current_data:
                    historical_val = historical[metric]
                    current_val = current_data[metric]
                    comparisons[metric] = {
                        'current': current_val,
                        'historical': historical_val,
                        'change': ((current_val - historical_val) / 
                                 historical_val * 100 if historical_val else 0)
                    }
                    
            return comparisons
            
        except Exception as e:
            self.logger.error(f"Failed to compare historical data: {e}")
            return {}
