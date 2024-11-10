# ASCIIme

[![PyPI version](https://badge.fury.io/py/asciime.svg)](https://badge.fury.io/py/asciime)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Turn your terminal into a kawaii anime experience! ASCIIme is a command-line tool that displays animated ASCII art GIFs in your terminal, with a focus on anime and kawaii content.


## Features

- Display animated GIFs as ASCII art in your terminal
- Support for true color and 256-color terminals
- Automatic caching system for faster loading
- Configurable display settings
- Category-based GIF selection
- Background prefetching for smooth playback

## Installation

First install my fork of the [gif-cli-fast](https://github.com/telnet23/gif-cli-fast) project using:
```bash
python -m pip install git+https://github.com/Felixdiamond/gif-cli-fast
```

Then set up asciime:

```bash
# Install from PyPI
pip install asciime

# Or install from source
git clone https://github.com/Felixdiamond/asciime.git
cd asciime
pip install -e .
```

## Usage

Basic usage:

```bash
# Display a random GIF
asciime --random

# Normal mode with prefetching and caching
asciime
```

**Note**: I'm using the Free Plan on render so my API usually sleeps in 5 mins or so. If you want 100% uptime, you can set up your own server by cloning the repo [asciime-api](https://github.com/Felixdiamond/asciime-api)

If you want to see a random anime gif whenever you open your terminal:

### For Bash users
Add this to your `~/.bashrc`:
```bash
# Display random ASCII anime GIF on terminal start
asciime
```

### For Zsh users
Add this to your `~/.zshrc`:
```bash
# Display random ASCII anime GIF on terminal start
asciime
```

### For Fish users
Add this to your `~/.config/fish/config.fish`:
```bash
# Display random ASCII anime GIF on terminal start
asciime
```

Not sure if this works for windows yet..

## Configuration

ASCIIme can be configured by editing `~/.config/asciime/config.json`. Available options:

```json
{
    "display_mode": "truecolor",     // Display mode: "truecolor", "256", "256fgbg", or "nocolor"
    "max_cache_size_mb": 100,        // Maximum cache size in megabytes
    "max_cache_age_days": 30,        // Maximum age of cached files in days
    "prefetch_count": 3,             // Number of GIFs to prefetch
    "api_url": "https://asciime-api.onrender.com/api",  // API endpoint
    "preferred_category": null,       // Preferred GIF category (null for random)
    "loop_count": 3,                 // Number of times to loop animation (0 for infinite)
    "debug": false                   // Enable debug logging
}
```

## Requirements

- Python 3.8 or higher
- Internet connection for fetching GIFs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Uses [gif-cli-fast](https://github.com/telnet23/gif-cli-fast) for GIF to ASCII conversion