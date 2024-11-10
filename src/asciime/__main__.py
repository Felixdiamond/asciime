"""
ASCIIme main module - Handles program initialization and main execution flow.
"""
import asyncio
import os
import sys
from typing import Dict, Optional
import signal
import argparse
import logging
from pathlib import Path

from asciime.core.cache_manager import CacheManager
from asciime.core.gif_fetcher import GIFFetcher
from asciime.core.gif_player_fast import GIFPlayer
from asciime.core.config_manager import ConfigManager

def setup_logging(debug: bool = False) -> None:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                Path.home() / ".cache" / "asciime" / "asciime.log",
                encoding="utf-8"
            )
        ]
    )

logger = logging.getLogger(__name__)

class ASCIImeError(Exception):
    """Base exception class for ASCIIme-specific errors."""
    pass

class GIFPlaybackError(ASCIImeError):
    """Raised when there's an error playing a GIF."""
    pass

class FetchError(ASCIImeError):
    """Raised when there's an error fetching a GIF."""
    pass

async def play_random_gif(config: Dict) -> None:
    """Play a single random GIF without caching or prefetching.
    
    Args:
        config: Configuration dictionary containing display settings
        
    Raises:
        GIFPlaybackError: If there's an error during playback
        FetchError: If there's an error fetching the GIF
    """
    gif_fetcher = None
    try:
        cache_manager = CacheManager()
        gif_fetcher = GIFFetcher(config["api_url"], cache_manager)
        logger.debug("Initializing GIF fetcher session")
        await gif_fetcher._init_session()
        
        gif_player = GIFPlayer(
            config["display_mode"],
            terminal_title="ASCIIme",
            loop_count=config.get("loop_count", 3),
        )
        logger.debug("GIF player initialized")
        
        category = config.get("preferred_category")
        gif = await gif_fetcher.fetch_random(category)
        if not gif:
            raise FetchError("Failed to fetch random GIF")
            
        logger.debug(f"Playing GIF from {gif}")
        await gif_player.play_animation(gif)

    except Exception as e:
        logger.error(f"Error playing random GIF: {e}", exc_info=True)
        raise GIFPlaybackError(f"Failed to play GIF: {str(e)}")

    finally:
        if gif_fetcher:
            await gif_fetcher.close()

async def async_cleanup_cache(
    cache_manager: CacheManager,
    config: Dict
) -> None:
    """Clean up old cached files.
    
    Args:
        cache_manager: Instance of CacheManager
        config: Configuration dictionary containing cache settings
    """
    try:
        await cache_manager.cleanup_old(
            max_age_days=config["max_cache_age_days"],
            max_size_mb=config["max_cache_size_mb"],
        )
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}", exc_info=True)

async def async_main(args: argparse.Namespace) -> None:
    """Main async execution flow.
    
    Args:
        args: Parsed command line arguments
    """
    gif_fetcher = None
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up logging based on config
        setup_logging(config.get("debug", False))

        if args.random:
            await play_random_gif(config)
            return

        cache_manager = CacheManager()
        cleanup_task = asyncio.create_task(
            async_cleanup_cache(cache_manager, config)
        )

        gif_player = GIFPlayer(
            config["display_mode"],
            terminal_title="ASCIIme",
            loop_count=config.get("loop_count", 3),
        )

        gif_fetcher = GIFFetcher(config["api_url"], cache_manager)
        await gif_fetcher._init_session()

        # Try to get a cached GIF first
        gif: Optional[str] = None
        try:
            category = config.get("preferred_category")
            gif = await cache_manager.get_random_cached(category)
        except Exception as e:
            logger.warning(f"Error fetching cached GIF: {e}")

        # Fetch new GIF if no cached one available
        if not gif:
            try:
                category = config.get("preferred_category")
                gif = await gif_fetcher.fetch_random(category)
                if not gif:
                    raise FetchError("Failed to fetch random GIF")
            except Exception as e:
                logger.error(f"Error fetching GIF: {e}", exc_info=True)
                raise FetchError(f"Failed to fetch GIF: {str(e)}")

        # Start prefetching in background
        prefetch_task = asyncio.create_task(
            gif_fetcher.prefetch_batch(
                config["prefetch_count"],
                config.get("preferred_category")
            )
        )

        await gif_player.play_animation(gif)

        try:
            await asyncio.gather(cleanup_task, prefetch_task)
        except Exception as e:
            logger.warning(f"Background task error: {e}")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

    finally:
        if gif_fetcher:
            await gif_fetcher.close()

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed argument namespace
    """
    parser = argparse.ArgumentParser(
        description="ASCIIme - Turn your terminal into a kawaii anime experience!"
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Fetch and play a random GIF without prefetching or cleanup",
    )
    return parser.parse_args()

async def shutdown(loop: asyncio.AbstractEventLoop, signal: signal.Signals) -> None:
    """Clean shutdown of the event loop.
    
    Args:
        loop: Event loop to shut down
        signal: Signal that triggered the shutdown
    """
    logger.info(f"Received exit signal {signal.name}")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def main() -> None:
    """Entry point for the ASCIIme application."""
    try:
        args = parse_arguments()

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.get_event_loop()
        
        signals = (signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(loop, s))
            )


        loop.run_until_complete(async_main(args))

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        loop.close()

if __name__ == "__main__":
    main()
