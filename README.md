# LlamaChat

A native macOS chat application powered by Ollama, built with Python and PyQt6.

## Features

- Native macOS application
- Ollama model integration
- Persistent chat history
- Dark mode support
- Configurable model parameters

## Prerequisites

- macOS 10.12 or later
- Python 3.13+
- [Ollama](https://ollama.ai) installed and running

## Installation

### Using DMG (Recommended)

1. Download the latest `LlamaChat.dmg` from the releases page
2. Mount the DMG and drag LlamaChat to your Applications folder
3. Launch LlamaChat from Applications

### Building from Source

See [BUILD.md](BUILD.md) for detailed build instructions.

## Configuration

LlamaChat can be configured using environment variables or through the application settings:

```
LLAMA_MODEL=llama3.2
LLAMA_TEMPERATURE=0.7
LLAMA_MAX_RETRIES=3
LOG_LEVEL=INFO
```

## Project Structure

```
llamachat/
├── database/       # Database models and initialization
├── ui/            # PyQt6 user interface components
├── utils/         # Utility functions
└── main.py        # Application entry point
```

## Data Storage

- Chat history: `~/Library/Application Support/LlamaChat/llamachat.db`
- Logs: `~/Library/Logs/LlamaChat/llamachat.log`

## Dependencies

- backoff: Retry mechanism for API calls
- markdown: Markdown rendering support
- ollama: Ollama API client
- PyQt6: GUI framework
- python-dotenv: Environment variable management
- qasync: Async support for PyQt
- sqlmodel: SQLite database ORM

## Development

1. Clone the repository
2. Create and activate virtual environment:

```
python3.13 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```
pip install -e .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see below or the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.ai) for the LLM backend
- [PyQt](https://riverbankcomputing.com/software/pyqt/) for the GUI framework
