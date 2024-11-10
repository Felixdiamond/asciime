# # First GifPlayer Implementation

# import os
# import sys
# import asyncio
# from typing import Optional, Tuple
# from gif_for_cli.execute import execute
# import signal

# class GIFPlayer:
#     def __init__(
#         self,
#         display_mode: str = "256",
#         terminal_title: Optional[str] = None,
#         width_percentage: float = 0.5,
#         max_height_percentage: float = 0.7,
#         loop_count: int = 0
#     ):
#         """Initialize GIF player
        
#         Args:
#             display_mode (str): Display mode ('nocolor', '256', '256fgbg', or 'truecolor')
#             terminal_title (str, optional): Custom terminal title during playback
#             width_percentage (float): Percentage of terminal width to use (0.1 to 1.0)
#             max_height_percentage (float): Maximum percentage of terminal height to use (0.1 to 1.0)
#             loop_count (int): Number of times to loop (0 for infinite)
#         """
#         self.display_mode = display_mode
#         self.terminal_title = terminal_title
#         self.width_percentage = max(0.1, min(1.0, width_percentage))
#         self.max_height_percentage = max(0.1, min(1.0, max_height_percentage))
#         self.loop_count = loop_count
#         self._original_title = None
#         self._running = False

#     def _calculate_dimensions(self) -> Tuple[int, int]:
#         """Calculate optimal terminal dimensions based on percentage of terminal width and max height"""
#         try:
#             terminal_rows = int(os.popen("tput lines").read().strip())
#             terminal_cols = int(os.popen("tput cols").read().strip())
            
#             target_cols = int(terminal_cols * self.width_percentage)
#             target_cols = max(20, min(terminal_cols, target_cols))
#             target_rows = int(target_cols * 0.5)
            
#             max_rows = int(terminal_rows * self.max_height_percentage)
#             if target_rows > max_rows:
#                 target_rows = max_rows
#                 target_cols = target_rows * 2
            
#             target_rows = max(10, target_rows)
#             target_cols = max(20, target_cols)
            
#             return (target_rows, target_cols)
#         except:
#             return (24, 80)

#     def _setup_terminal(self):
#         """Setup terminal for GIF playback"""
#         if self.terminal_title:
#             self._original_title = os.popen('echo $TERM').read().strip()
#             os.system(f'echo -ne "\033]0;{self.terminal_title}\007"')
        
#         print("\033[?25l", end='')
#         print("\033[2J\033[H", end='')

#     def _cleanup_terminal(self):
#         """Restore terminal to original state"""
#         print("\033[?25h", end='')
#         if self._original_title:
#             os.system(f'echo -ne "\033]0;{self._original_title}\007"')

#     def _handle_signal(self, signum, frame):
#         """Handle interrupt signals"""
#         self._running = False
#         self._cleanup_terminal()

#     async def play_animation(self, gif_path: str):
#         """Play GIF animation in terminal
        
#         Args:
#             gif_path (str): Path to the GIF file or URL
#         """
#         if not (os.path.exists(gif_path) or gif_path.startswith(('http://', 'https://'))):
#             print(f"Error: Invalid GIF source: {gif_path}")
#             return

#         signal.signal(signal.SIGINT, self._handle_signal)
#         signal.signal(signal.SIGTERM, self._handle_signal)

#         self._running = True
#         rows, cols = self._calculate_dimensions()

#         try:
#             self._setup_terminal()
            
#             env = os.environ.copy()
#             env['GIF_FOR_CLI_DISPLAY_MODE'] = self.display_mode

#             args = [
#                 gif_path,
#                 '--rows', str(rows),
#                 '--cols', str(cols),
#                 '--display-mode', self.display_mode,
#                 '-l', str(self.loop_count),
#                 '--pool-size', '8'
#             ]

#             while self._running:
#                 await asyncio.get_event_loop().run_in_executor(
#                     None,
#                     execute,
#                     env,
#                     args,
#                     sys.stdout
#                 )
                
#                 if self.loop_count > 0:
#                     break

#         except KeyboardInterrupt:
#             print("\nPlayback interrupted by user")
#         except Exception as e:
#             print(f"\nPlayback error: {e}")
#         finally:
#             self._running = False
#             self._cleanup_terminal()

#     def play(self, gif_path: str):
#         """Synchronous wrapper for playing GIF animations
        
#         Args:
#             gif_path (str): Path to the GIF file or URL
#         """
#         try:
#             asyncio.run(self.play_animation(gif_path))
#         except Exception as e:
#             print(f"Error: {e}")