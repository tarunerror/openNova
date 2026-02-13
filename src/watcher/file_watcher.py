"""
File system watcher for monitoring file changes.
Uses watchdog to detect file system events.
"""
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from typing import Callable, Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileSystemWatcher:
    """
    Monitors file system changes and triggers callbacks.
    """
    
    def __init__(self):
        """Initialize the file system watcher."""
        self.observer = Observer()
        self.handlers: Dict[str, FileSystemEventHandler] = {}
        self.running = False
        logger.info("File system watcher initialized")
    
    def watch_directory(self, 
                        path: str, 
                        on_created: Optional[Callable[[str], None]] = None,
                        on_modified: Optional[Callable[[str], None]] = None,
                        on_deleted: Optional[Callable[[str], None]] = None,
                        on_moved: Optional[Callable[[str, str], None]] = None,
                        recursive: bool = False,
                        patterns: Optional[List[str]] = None) -> bool:
        """
        Start watching a directory for changes.
        
        Args:
            path: Directory path to watch
            on_created: Callback when a file is created
            on_modified: Callback when a file is modified
            on_deleted: Callback when a file is deleted
            on_moved: Callback when a file is moved (src_path, dest_path)
            recursive: Whether to watch subdirectories
            patterns: File patterns to match (e.g., ["*.txt", "*.py"])
            
        Returns:
            True if watching started successfully, False otherwise
        """
        try:
            watch_path = Path(path)
            if not watch_path.exists():
                logger.error(f"Watch path does not exist: {path}")
                return False
            
            # Create custom event handler
            handler = CustomFileHandler(
                on_created=on_created,
                on_modified=on_modified,
                on_deleted=on_deleted,
                on_moved=on_moved,
                patterns=patterns
            )
            
            # Schedule the observer
            self.observer.schedule(handler, str(watch_path), recursive=recursive)
            self.handlers[path] = handler
            
            # Start observer if not already running
            if not self.running:
                self.observer.start()
                self.running = True
            
            logger.info(f"Started watching directory: {path} (recursive={recursive})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch directory '{path}': {e}")
            return False
    
    def stop_watching(self, path: str) -> bool:
        """
        Stop watching a specific directory.
        
        Args:
            path: Directory path to stop watching
            
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if path in self.handlers:
                # Remove the handler
                del self.handlers[path]
                logger.info(f"Stopped watching directory: {path}")
                return True
            else:
                logger.warning(f"No active watch found for: {path}")
                return False
        except Exception as e:
            logger.error(f"Failed to stop watching '{path}': {e}")
            return False
    
    def stop_all(self):
        """Stop watching all directories."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            self.handlers.clear()
            logger.info("Stopped all file system watchers")
    
    def get_watched_paths(self) -> List[str]:
        """
        Get list of currently watched paths.
        
        Returns:
            List of directory paths being watched
        """
        return list(self.handlers.keys())


class CustomFileHandler(FileSystemEventHandler):
    """
    Custom event handler for file system events.
    """
    
    def __init__(self,
                 on_created: Optional[Callable[[str], None]] = None,
                 on_modified: Optional[Callable[[str], None]] = None,
                 on_deleted: Optional[Callable[[str], None]] = None,
                 on_moved: Optional[Callable[[str, str], None]] = None,
                 patterns: Optional[List[str]] = None):
        """
        Initialize the event handler.
        
        Args:
            on_created: Callback for file creation
            on_modified: Callback for file modification
            on_deleted: Callback for file deletion
            on_moved: Callback for file move
            patterns: File patterns to match
        """
        super().__init__()
        self.on_created_callback = on_created
        self.on_modified_callback = on_modified
        self.on_deleted_callback = on_deleted
        self.on_moved_callback = on_moved
        self.patterns = patterns or []
    
    def _matches_pattern(self, path: str) -> bool:
        """
        Check if the file path matches any of the patterns.
        
        Args:
            path: File path to check
            
        Returns:
            True if matches, False otherwise
        """
        if not self.patterns:
            return True  # No patterns means match all
        
        file_path = Path(path)
        for pattern in self.patterns:
            if file_path.match(pattern):
                return True
        return False
    
    def on_created(self, event: FileSystemEvent):
        """Called when a file or directory is created."""
        if not event.is_directory and self._matches_pattern(event.src_path):
            logger.info(f"File created: {event.src_path}")
            if self.on_created_callback:
                try:
                    self.on_created_callback(event.src_path)
                except Exception as e:
                    logger.error(f"Error in on_created callback: {e}")
    
    def on_modified(self, event: FileSystemEvent):
        """Called when a file or directory is modified."""
        if not event.is_directory and self._matches_pattern(event.src_path):
            logger.debug(f"File modified: {event.src_path}")
            if self.on_modified_callback:
                try:
                    self.on_modified_callback(event.src_path)
                except Exception as e:
                    logger.error(f"Error in on_modified callback: {e}")
    
    def on_deleted(self, event: FileSystemEvent):
        """Called when a file or directory is deleted."""
        if not event.is_directory and self._matches_pattern(event.src_path):
            logger.info(f"File deleted: {event.src_path}")
            if self.on_deleted_callback:
                try:
                    self.on_deleted_callback(event.src_path)
                except Exception as e:
                    logger.error(f"Error in on_deleted callback: {e}")
    
    def on_moved(self, event: FileSystemEvent):
        """Called when a file or directory is moved."""
        if not event.is_directory:
            src_matches = self._matches_pattern(event.src_path)
            dest_matches = self._matches_pattern(event.dest_path) if hasattr(event, 'dest_path') else False
            
            if src_matches or dest_matches:
                logger.info(f"File moved: {event.src_path} -> {event.dest_path}")
                if self.on_moved_callback and hasattr(event, 'dest_path'):
                    try:
                        self.on_moved_callback(event.src_path, event.dest_path)
                    except Exception as e:
                        logger.error(f"Error in on_moved callback: {e}")


# Global file system watcher instance
file_watcher = FileSystemWatcher()
