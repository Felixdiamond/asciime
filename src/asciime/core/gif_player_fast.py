# Current GifPlayer Implementation

import os
import sys
import asyncio
import signal
from typing import Optional, Tuple
import subprocess

class GIFPlayerError(Exception):
    """Base exception for GIF player errors"""
    pass

class GIFPlayer:
    def __init__(
        self,
        display_mode: str = "truecolor",
        terminal_title: Optional[str] = None,
        width_percentage: float = 0.8,
        max_height_percentage: float = 0.8,
        loop_count: int = 3
    ):
        """Initialize GIF player
        
        Args:
            display_mode (str): Display mode ('ascii', '256color', or 'truecolor')
            terminal_title (str, optional): Custom terminal title during playback
            width_percentage (float): Percentage of terminal width to use (0.1 to 1.0)
            max_height_percentage (float): Maximum percentage of terminal height to use (0.1 to 1.0)
            loop_count (int): Number of times to loop (0 for infinite)
        """
        mode_mapping = {
            'nocolor': 'ascii',
            '256': '256color',
            '256fgbg': '256color',
            'truecolor': 'truecolor'
        }
        self.display_mode = mode_mapping.get(display_mode, 'truecolor')
        self.terminal_title = terminal_title
        self.width_percentage = max(0.1, min(1.0, width_percentage))
        self.max_height_percentage = max(0.1, min(1.0, max_height_percentage))
        self.loop_count = loop_count
        self._original_title = None
        self._running = False
        self._process = None

    def _calculate_dimensions(self) -> Tuple[int, int]:
        """Calculate optimal terminal dimensions based on percentage of terminal width and max height"""
        try:
            terminal_rows = int(os.popen("tput lines").read().strip())
            terminal_cols = int(os.popen("tput cols").read().strip())
            
            # Calculate target width based on terminal size
            target_cols = int(terminal_cols * self.width_percentage)
            target_cols = max(40, min(terminal_cols, target_cols)) 
            
            char_aspect_ratio = 0.5
            
            raw_target_rows = int(target_cols * char_aspect_ratio * 0.5)
            max_rows = int(terminal_rows * self.max_height_percentage)
            target_rows = min(raw_target_rows, max_rows)
            
            target_rows = max(20, target_rows)
            

            if target_rows != raw_target_rows:
                target_cols = int(target_rows / (char_aspect_ratio * 0.5))
                target_cols = min(target_cols, terminal_cols)
            
            return (target_rows, target_cols)
        except:
            return (40, 80)

    def _setup_terminal(self):
        """Setup terminal for GIF playback"""
        if self.terminal_title:
            self._original_title = os.popen('echo $TERM').read().strip()
            os.system(f'echo -ne "\033]0;{self.terminal_title}\007"')
        
        print("\033[?25l", end='')
        print("\033[2J\033[H", end='')

    def _cleanup_terminal(self):
        """Restore terminal to original state"""
        print("\033[?25h", end='')
        if self._original_title:
            os.system(f'echo -ne "\033]0;{self._original_title}\007"')
        print("\033[2J\033[H", end='')

    def _handle_signal(self, signum, frame):
        """Handle interrupt signals"""
        self._running = False
        if self._process:
            try:
                self._process.terminate()
            except:
                pass
        self._cleanup_terminal()

    async def _run_gif(self, gif_path: str, rows: int, cols: int):
        """Run the GIF with specified loop count"""
        try:
            env = os.environ.copy()
            env["LINES"] = str(rows)
            env["COLUMNS"] = str(cols)
            env["PYTHONUNBUFFERED"] = "1"
            
            cmd = [
                sys.executable, "-m", "gif_cli_fast",
                "--provider", "local",
                "--mode", self.display_mode,
                "--rows", str(rows),
                "--cols", str(cols),
                "--loops", str(self.loop_count),
                str(gif_path)
            ]

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=sys.stdout,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await self._process.communicate()
            
            if self._process.returncode != 0 and stderr:
                raise GIFPlayerError(f"gif-cli-fast error: {stderr.decode()}")

        except Exception as e:
            raise GIFPlayerError(f"Failed to play GIF: {str(e)}")
        finally:
            if self._process:
                try:
                    self._process.terminate()
                except:
                    pass
            self._process = None

    async def play_animation(self, gif_path: str):
        """Play GIF animation in terminal
        
        Args:
            gif_path (str): Path to the GIF file or URL
        """
        if not (os.path.exists(gif_path) or gif_path.startswith(('http://', 'https://'))):
            raise GIFPlayerError(f"Invalid GIF source: {gif_path}")

        
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._running = True
        rows, cols = self._calculate_dimensions()

        try:
            self._setup_terminal()
            await self._run_gif(gif_path, rows, cols)
        except KeyboardInterrupt:
            print("\nPlayback interrupted by user")
        except Exception as e:
            print(f"\nPlayback error: {e}")
        finally:
            self._running = False
            self._cleanup_terminal()