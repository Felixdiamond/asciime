# core/cache_manager.py
import os
import json
import sqlite3
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import time

class CacheManager:
    def __init__(self, cache_dir: str = "~/.cache/asciime"):
        self.cache_dir = os.path.expanduser(cache_dir)
        self.db_path = os.path.join(self.cache_dir, "meta.db")
        self._init_storage()

    def _init_storage(self):
        """Initialize cache storage with improved schema"""
        try:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

            for attempt in range(3):
                try:
                    conn = sqlite3.connect(
                        self.db_path,
                        timeout=20,
                        isolation_level=None
                    )
                    c = conn.cursor()
                    
                    c.execute("""
                        CREATE TABLE IF NOT EXISTS gifs (
                            id TEXT PRIMARY KEY,
                            path TEXT NOT NULL,
                            category TEXT,
                            source TEXT,
                            width INTEGER,
                            height INTEGER,
                            size INTEGER,
                            last_used TEXT,
                            created TEXT,
                            play_count INTEGER DEFAULT 0
                        )
                    """)
                    
                    c.execute("""
                        CREATE INDEX IF NOT EXISTS idx_category 
                        ON gifs(category)
                    """)
                    
                    conn.close()
                    break
                except sqlite3.OperationalError as e:
                    if attempt == 2:
                        raise
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Failed to initialize cache: {e}")
            raise

    async def cleanup_old(
        self,
        max_age_days: int = 30,
        max_size_mb: int = 100
    ):
        """Asynchronous cache cleanup"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            cutoff_date = (
                datetime.now() - timedelta(days=max_age_days)
            ).isoformat()
            
            c.execute(
                "SELECT path FROM gifs WHERE last_used < ?",
                (cutoff_date,)
            )
            old_files = c.fetchall()

            for (file_path,) in old_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError as e:
                    print(
                        f"Warning: Could not remove {file_path}: "
                        f"{e}"
                    )

            c.execute("DELETE FROM gifs WHERE last_used < ?", (cutoff_date,))

            total_size = 0
            for path in Path(self.cache_dir).rglob("*.gif"):
                try:
                    total_size += path.stat().st_size
                except OSError:
                    continue

            while total_size > max_size_mb * 1024 * 1024:
                c.execute("""
                    SELECT id, path, COALESCE(size, 0) as size
                    FROM gifs 
                    ORDER BY play_count ASC, last_used ASC 
                    LIMIT 1
                """)
                
                result = c.fetchone()

                if not result:
                    break

                file_id, file_path, file_size = result
                
                if file_size == 0:
                    try:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                    except OSError:
                        file_size = 0

                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        if file_size > 0:
                            total_size -= file_size
                except OSError as e:
                    print(
                        f"Warning: Could not remove {file_path}: "
                        f"{e}"
                    )

                c.execute("DELETE FROM gifs WHERE id = ?", (file_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Cache cleanup error: {e}")
            print("(From cache manager)")
            try:
                conn.rollback()
                conn.close()
            except:
                pass

    def get_cache_path(self, gif_id: str, category: str) -> str:
        """Generate cache path for GIF"""
        category_dir = os.path.join(
            self.cache_dir,
            category.lower().replace(" ", "_")
        )
        return os.path.join(category_dir, f"{gif_id}.gif")

    async def get_random_cached(
        self,
        category: Optional[str] = None
    ) -> Optional[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            query = "SELECT path FROM gifs"
            params = []

            if category:
                query += " WHERE category = ?"
                params.append(category)

            # print(f"Executing query {query} with params {params}")
            query += " ORDER BY RANDOM() LIMIT 1"
            
            c.execute(query, params)
            result = c.fetchone()
            
            if result and os.path.exists(result[0]):
                c.execute(
                    """
                    UPDATE gifs 
                    SET last_used = ?, play_count = play_count + 1 
                    WHERE path = ?
                    """,
                    (datetime.now().isoformat(), result[0])
                )
                conn.commit()
                print(f"Returning cached GIF: {result[0]}")
                return result[0]

            conn.close()
            print("No cached GIF found")
            return None

        except Exception as e:
            print(
                f"Error getting random cached GIF: {e}"
            )
            return None

    async def update_metadata(
        self,
        gif_id: str,
        path: str,
        metadata: Optional[Dict] = None
    ):
        """Update GIF metadata in database with safe fallbacks"""
        try:
            metadata = metadata or {}
            
            dims = metadata.get('dims', [0, 0])
            if not isinstance(dims, (list, tuple)) or len(dims) < 2:
                dims = [0, 0]
                
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("""
                INSERT OR REPLACE INTO gifs (
                    id, path, category, source, width, height,
                    size, last_used, created, play_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gif_id,
                path,
                metadata.get('category'),
                metadata.get('source'),
                dims[0],
                dims[1],
                metadata.get('size', 0),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error updating metadata: {e}")
            try:
                conn.rollback()
                conn.close()
            except:
                pass