"""
UI Component pooling system for ConsultEase.
Provides efficient widget reuse to improve performance on Raspberry Pi.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ComponentPool(QObject):
    """
    Component pool for efficient widget reuse.
    Reduces memory allocation and improves performance.
    """
    
    # Signal emitted when pool statistics change
    stats_changed = pyqtSignal(dict)
    
    def __init__(self, max_pool_size: int = 50):
        """
        Initialize the component pool.
        
        Args:
            max_pool_size: Maximum number of components to keep in pool
        """
        super().__init__()
        self.max_pool_size = max_pool_size
        
        # Pool storage: component_type -> list of available components
        self.pools: Dict[str, List[QWidget]] = {}
        
        # Active components: component_id -> component
        self.active_components: Dict[str, QWidget] = {}
        
        # Component creation counters
        self.creation_stats = {
            'total_created': 0,
            'total_reused': 0,
            'total_returned': 0,
            'active_count': 0
        }
        
        logger.info(f"Component pool initialized with max size: {max_pool_size}")
    
    def get_component(self, component_type: str, component_class: Type[QWidget], 
                     component_id: str = None, **kwargs) -> QWidget:
        """
        Get a component from the pool or create a new one.
        
        Args:
            component_type: Type identifier for the component
            component_class: Class to instantiate if no pooled component available
            component_id: Unique identifier for this component instance
            **kwargs: Arguments to pass to component constructor
            
        Returns:
            QWidget: Component instance
        """
        # Generate component ID if not provided
        if component_id is None:
            component_id = f"{component_type}_{len(self.active_components)}"
        
        # Check if we have a pooled component available
        if component_type in self.pools and self.pools[component_type]:
            component = self.pools[component_type].pop()
            self.creation_stats['total_reused'] += 1
            logger.debug(f"Reused pooled component: {component_type}")
        else:
            # Create new component
            try:
                component = component_class(**kwargs)
                self.creation_stats['total_created'] += 1
                logger.debug(f"Created new component: {component_type}")
            except Exception as e:
                logger.error(f"Failed to create component {component_type}: {e}")
                raise
        
        # Track active component
        self.active_components[component_id] = component
        self.creation_stats['active_count'] = len(self.active_components)
        
        # Reset component state
        self._reset_component(component)
        
        # Emit stats update
        self.stats_changed.emit(self.get_stats())
        
        return component
    
    def return_component(self, component_id: str, component_type: str) -> bool:
        """
        Return a component to the pool for reuse.
        
        Args:
            component_id: Unique identifier of the component
            component_type: Type identifier for the component
            
        Returns:
            bool: True if component was returned to pool, False otherwise
        """
        if component_id not in self.active_components:
            logger.warning(f"Attempted to return unknown component: {component_id}")
            return False
        
        component = self.active_components.pop(component_id)
        self.creation_stats['active_count'] = len(self.active_components)
        
        # Check if pool has space
        if component_type not in self.pools:
            self.pools[component_type] = []
        
        if len(self.pools[component_type]) < self.max_pool_size:
            # Clean up component before pooling
            self._cleanup_component(component)
            
            # Add to pool
            self.pools[component_type].append(component)
            self.creation_stats['total_returned'] += 1
            
            logger.debug(f"Returned component to pool: {component_type}")
            
            # Emit stats update
            self.stats_changed.emit(self.get_stats())
            return True
        else:
            # Pool is full, destroy component
            self._destroy_component(component)
            logger.debug(f"Pool full, destroyed component: {component_type}")
            return False
    
    def _reset_component(self, component: QWidget):
        """
        Reset component to default state for reuse.
        
        Args:
            component: Component to reset
        """
        try:
            # Hide component
            component.hide()
            
            # Clear any text content if applicable
            if hasattr(component, 'setText'):
                component.setText('')
            if hasattr(component, 'clear'):
                component.clear()
            
            # Reset enabled state
            component.setEnabled(True)
            
            # Reset visibility
            component.setVisible(False)
            
            # Reset stylesheet to default
            component.setStyleSheet('')
            
            # Reset size policy if needed
            if hasattr(component, 'setSizePolicy'):
                from PyQt5.QtWidgets import QSizePolicy
                component.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            
        except Exception as e:
            logger.warning(f"Error resetting component: {e}")
    
    def _cleanup_component(self, component: QWidget):
        """
        Clean up component before returning to pool.
        
        Args:
            component: Component to clean up
        """
        try:
            # Disconnect all signals
            if hasattr(component, 'disconnect'):
                component.disconnect()
            
            # Remove from parent
            if component.parent():
                component.setParent(None)
            
            # Hide component
            component.hide()
            
            # Reset component state
            self._reset_component(component)
            
        except Exception as e:
            logger.warning(f"Error cleaning up component: {e}")
    
    def _destroy_component(self, component: QWidget):
        """
        Properly destroy a component.
        
        Args:
            component: Component to destroy
        """
        try:
            # Clean up first
            self._cleanup_component(component)
            
            # Schedule for deletion
            component.deleteLater()
            
        except Exception as e:
            logger.warning(f"Error destroying component: {e}")
    
    def clear_pool(self, component_type: str = None):
        """
        Clear components from pool.
        
        Args:
            component_type: Specific component type to clear, or None for all
        """
        if component_type:
            if component_type in self.pools:
                for component in self.pools[component_type]:
                    self._destroy_component(component)
                self.pools[component_type].clear()
                logger.info(f"Cleared pool for component type: {component_type}")
        else:
            # Clear all pools
            for comp_type, components in self.pools.items():
                for component in components:
                    self._destroy_component(component)
                components.clear()
            self.pools.clear()
            logger.info("Cleared all component pools")
        
        # Emit stats update
        self.stats_changed.emit(self.get_stats())
    
    def cleanup_active_components(self):
        """
        Clean up all active components (call on shutdown).
        """
        for component_id, component in list(self.active_components.items()):
            self._destroy_component(component)
        
        self.active_components.clear()
        self.creation_stats['active_count'] = 0
        
        logger.info("Cleaned up all active components")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.
        
        Returns:
            dict: Pool statistics
        """
        pool_sizes = {comp_type: len(components) for comp_type, components in self.pools.items()}
        
        stats = {
            'pool_sizes': pool_sizes,
            'total_pooled': sum(pool_sizes.values()),
            'max_pool_size': self.max_pool_size,
            **self.creation_stats
        }
        
        # Calculate efficiency metrics
        total_requests = stats['total_created'] + stats['total_reused']
        if total_requests > 0:
            stats['reuse_rate'] = stats['total_reused'] / total_requests
            stats['efficiency'] = (stats['total_reused'] / total_requests) * 100
        else:
            stats['reuse_rate'] = 0.0
            stats['efficiency'] = 0.0
        
        return stats
    
    def optimize_pools(self):
        """
        Optimize pools by removing excess components.
        """
        optimized_count = 0
        
        for component_type, components in self.pools.items():
            if len(components) > self.max_pool_size // 2:
                # Keep only half the max pool size for each type
                target_size = self.max_pool_size // 4
                excess_components = components[target_size:]
                
                for component in excess_components:
                    self._destroy_component(component)
                
                self.pools[component_type] = components[:target_size]
                optimized_count += len(excess_components)
        
        if optimized_count > 0:
            logger.info(f"Optimized pools, removed {optimized_count} excess components")
            self.stats_changed.emit(self.get_stats())


# Global component pool instance
_component_pool = None


def get_component_pool() -> ComponentPool:
    """
    Get the global component pool instance.
    
    Returns:
        ComponentPool: Global component pool
    """
    global _component_pool
    if _component_pool is None:
        _component_pool = ComponentPool()
    return _component_pool


def cleanup_component_pool():
    """
    Clean up the global component pool.
    """
    global _component_pool
    if _component_pool:
        _component_pool.cleanup_active_components()
        _component_pool.clear_pool()
        _component_pool = None
        logger.info("Global component pool cleaned up")
