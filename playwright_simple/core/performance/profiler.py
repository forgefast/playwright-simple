#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance profiler for playwright-simple.

Provides profiling capabilities to identify performance bottlenecks.
"""

import time
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Performance profiler for measuring execution time and identifying bottlenecks."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.metrics: Dict[str, List[float]] = {}
        self.profiler: Optional[cProfile.Profile] = None
    
    @contextmanager
    def measure(self, operation_name: str):
        """
        Context manager to measure operation time.
        
        Args:
            operation_name: Name of the operation being measured
            
        Example:
            ```python
            with profiler.measure("yaml_parsing"):
                # Code to measure
                parse_yaml()
            ```
        """
        if not self.enabled:
            yield
            return
        
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(elapsed)
            logger.debug(f"⏱️  {operation_name}: {elapsed*1000:.2f}ms")
    
    def start_profiling(self):
        """Start CPU profiling."""
        if not self.enabled:
            return
        
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        logger.debug("🔍 CPU profiling started")
    
    def stop_profiling(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Stop CPU profiling and return statistics.
        
        Args:
            output_path: Optional path to save profile statistics
            
        Returns:
            Profile statistics as string, or None if profiling not enabled
        """
        if not self.enabled or not self.profiler:
            return None
        
        self.profiler.disable()
        
        # Generate statistics
        s = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        stats_str = s.getvalue()
        
        # Save to file if requested
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(stats_str)
            logger.info(f"📊 Profile saved to {output_path}")
        
        return stats_str
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get summary of all measured operations.
        
        Returns:
            Dictionary with operation names and statistics (min, max, avg, total)
        """
        summary = {}
        
        for operation_name, times in self.metrics.items():
            if not times:
                continue
            
            summary[operation_name] = {
                'count': len(times),
                'total': sum(times),
                'min': min(times),
                'max': max(times),
                'avg': sum(times) / len(times),
            }
        
        return summary
    
    def print_summary(self):
        """Print performance summary to console."""
        if not self.metrics:
            logger.info("📊 No performance metrics collected")
            return
        
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 Performance Summary")
        print("="*60)
        
        for operation_name, stats in sorted(summary.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"\n{operation_name}:")
            print(f"  Count:    {stats['count']}")
            print(f"  Total:    {stats['total']*1000:.2f}ms")
            print(f"  Average:  {stats['avg']*1000:.2f}ms")
            print(f"  Min:      {stats['min']*1000:.2f}ms")
            print(f"  Max:      {stats['max']*1000:.2f}ms")
        
        print("="*60 + "\n")
    
    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.profiler = None


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def set_profiler(profiler: PerformanceProfiler):
    """Set global profiler instance."""
    global _global_profiler
    _global_profiler = profiler

