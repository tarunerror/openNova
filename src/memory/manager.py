"""
Memory Manager - Long-term memory using ChromaDB.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("Memory")


class MemoryManager:
    """Manages long-term memory using ChromaDB."""
    
    def __init__(self, persist_dir: str = None):
        """
        Initialize memory manager.
        
        Args:
            persist_dir: Directory to persist ChromaDB data
        """
        if persist_dir is None:
            persist_dir = str(Path.home() / ".ai_agent" / "memory")
        
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
        
        self._init_db()
    
    def _init_db(self):
        """Initialize ChromaDB."""
        try:
            import chromadb
            
            # Create client
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="agent_memory",
                metadata={"description": "Long-term memory for AI agent"}
            )
            
            logger.info(f"Memory initialized at {self.persist_dir}")
            logger.info(f"Memory contains {self.collection.count()} entries")
            
        except ImportError:
            logger.error("chromadb not installed. Install with: pip install chromadb")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing memory: {e}")
            self.client = None
    
    def remember(self, content: str, metadata: Dict[str, Any] = None):
        """
        Store a memory.
        
        Args:
            content: The content to remember
            metadata: Additional metadata (type, timestamp, etc.)
        """
        if not self.collection:
            logger.warning("Memory not available")
            return
        
        try:
            # Add timestamp
            if metadata is None:
                metadata = {}
            
            metadata["timestamp"] = datetime.now().isoformat()
            
            # Generate ID
            memory_id = f"mem_{int(datetime.now().timestamp() * 1000)}"
            
            # Add to collection
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            logger.info(f"Stored memory: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
    
    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories similar to query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of memory dictionaries
        """
        if not self.collection:
            logger.warning("Memory not available")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            memories = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    memory = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    }
                    memories.append(memory)
            
            logger.info(f"Recalled {len(memories)} memories for: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            return []
    
    def remember_preference(self, key: str, value: str):
        """
        Remember a user preference.
        
        Args:
            key: Preference key (e.g., "signature", "theme")
            value: Preference value
        """
        self.remember(
            content=f"{key}: {value}",
            metadata={"type": "preference", "key": key}
        )
    
    def get_preference(self, key: str) -> str:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            
        Returns:
            Preference value or empty string
        """
        memories = self.recall(key, n_results=1)
        
        for memory in memories:
            if memory['metadata'].get('type') == 'preference':
                if memory['metadata'].get('key') == key:
                    # Extract value from "key: value" format
                    content = memory['content']
                    if ':' in content:
                        return content.split(':', 1)[1].strip()
        
        return ""
    
    def clear_all(self):
        """Clear all memories (use with caution)."""
        if self.collection:
            try:
                # Delete collection
                self.client.delete_collection("agent_memory")
                # Recreate
                self.collection = self.client.create_collection("agent_memory")
                logger.info("All memories cleared")
            except Exception as e:
                logger.error(f"Error clearing memories: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.collection:
            return {"available": False}
        
        return {
            "available": True,
            "total_memories": self.collection.count(),
            "persist_dir": self.persist_dir
        }


# Global memory manager instance
memory = MemoryManager()
