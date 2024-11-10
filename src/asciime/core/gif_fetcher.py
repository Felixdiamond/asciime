import aiohttp
import asyncio
import os
from typing import Optional, List, Dict
from pathlib import Path
import logging


logger = logging.getLogger(__name__)

class GIFFetcher:
    def __init__(self, api_url: str, cache_manager: 'CacheManager'):
        self.api_url = api_url
        self.cache_manager = cache_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=10)
        self._categories: Optional[List[Dict]] = None

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _init_session(self):
        """Initialize aiohttp session with retry logic"""
        if not self.session:
            retry_options = aiohttp.ClientTimeout(
                total=30,
                connect=10
            )
            self.session = aiohttp.ClientSession(
                timeout=retry_options,
                headers={'User-Agent': 'ASCIIme/1.0'}
            )

    async def fetch_random(self, category: Optional[str] = None) -> Optional[str]:
        try:
            params = {'category': category} if category else {}
            async with self.session.get(
                f"{self.api_url}/random",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('success') and data.get('data'):
                        return await self._download_gif(data['data'])
                else:
                    logger.debug(f"Failed to fetch random GIF: {resp.status}")

        except Exception as e:
            logger.debug(f"Error fetching random GIF: {e}")

        return None

    async def _download_gif(self, gif_data: Dict) -> Optional[str]:
        try:
            gif_url = gif_data.get('url')
            if not gif_url:
                return None

            gif_id = gif_data.get('id')
            category = gif_data.get('category', 'unknown')
            cache_path = self.cache_manager.get_cache_path(gif_id, category)

            if os.path.exists(cache_path):
                logger.debug(f"Skipping download for {gif_id}")
                await self.cache_manager.update_metadata(
                    gif_id,
                    cache_path,
                    gif_data
                )
                return cache_path

            async with self.session.get(gif_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, 'wb') as f:
                        f.write(content)
                    
                    await self.cache_manager.update_metadata(
                        gif_id,
                        cache_path,
                        gif_data
                    )
                    return cache_path

        except Exception as e:
            logger.debug(f"Error downloading GIF: {e}")

        return None

    async def prefetch_batch(
        self,
        count: int = 3,
        category: Optional[str] = None
    ):
        try:
            params = {
                'count': min(count, 3)
            }
            if category:
                params['category'] = category

            async with self.session.get(
                f"{self.api_url}/batch",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('success') and isinstance(
                        data.get('data'), list
                    ):
                        # Download in parallel
                        tasks = [
                            self._download_gif(gif)
                            for gif in data['data']
                        ]
                        await asyncio.gather(*tasks, return_exceptions=True)
                        logger.debug(f"Prefetched {len(tasks)} GIFs")

        except Exception as e:
            logger.debug(f"Prefetch error: {e}")

    async def get_categories(self) -> List[Dict]:
        if self._categories is None:
            try:
                async with self.session.get(
                    f"{self.api_url}/categories"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('success'):
                            self._categories = data.get('data', [])
            except Exception as e:
                logger.debug(f"Error fetching categories: {e}")
                self._categories = []
        
        return self._categories

    async def close(self):
        if self.session:
            try:
                await asyncio.wait_for(
                    self.session.close(),
                    timeout=5.0
                )
            except:
                pass
            self.session = None
