# Workflow Builder

An AI-powered workflow automation tool inspired by N8N, built with Streamlit, LangGraph, and Groq.

## Features

- 🎨 **Visual Workflow Builder**: Create workflows using an intuitive node-based interface
- 🤖 **AI-Powered Nodes**: Leverage Groq LLMs for intelligent task processing
- 🔀 **Conditional Routing**: Dynamic workflow routing based on AI decisions
- 📊 **Visual Graph**: Interactive workflow visualization
- 💾 **Workflow Persistence**: Save and load your workflows
- 📝 **Templates**: Pre-built workflow templates for common use cases
- 💾 **Persistence**: Save and load workflows with file-based storage

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

## Usage

1. **Start the application**:
   ```bash
   # From the project root directory
   streamlit run src/main.py
   
   # Or using Python module syntax
   python -m streamlit run src/main.py
   ```

2. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8501`)

3. **Create your first workflow**:
   - Click "New Workflow" to start
   - Add nodes by clicking "Add Node"
   - Configure each node with a name and prompt
   - Set up routing rules to connect nodes
   - Click "Compile Workflow" to validate
   - Click "Run Workflow" to execute

## Project Structure

```
workflow-builder/
├── config/           # Configuration management
├── src/              # Source code
│   ├── models/       # Data models
│   ├── core/         # Core engine
│   ├── nodes/        # Node implementations
│   ├── ui/           # Streamlit UI
│   ├── storage/      # Persistence layer
│   └── utils/        # Utilities
├── tests/            # Test suite
├── templates/        # Workflow templates
└── docs/             # Documentation
```

## Configuration

Configuration is managed through environment variables (see `.env.example`) and `config/settings.py`.

### Required Environment Variables

- `GROQ_API_KEY`: Your Groq API key (required)

### Optional Environment Variables

- `LLM_MODEL_NAME`: Model to use (default: `llama-3.3-70b-versatile`)
- `LLM_TEMPERATURE`: Temperature for LLM (default: `0.2`)
- `WORKFLOW_STORAGE_PATH`: Where to store workflows (default: `./workflows`)
- `LOG_LEVEL`: Logging level (default: `INFO`)





## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

