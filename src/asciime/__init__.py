"""
ASCIIme - Turn your terminal into a kawaii anime experience!
"""

__version__ = "0.1.0"
__author__ = "Ayane"
__license__ = "MIT"

from asciime.core.cache_manager import CacheManager
from asciime.core.config_manager import ConfigManager
from asciime.core.gif_fetcher import GIFFetcher
from asciime.core.gif_player import GIFPlayer

__all__ = [
    "CacheManager",
    "ConfigManager", 
    "GIFFetcher",
    "GIFPlayer",
]
