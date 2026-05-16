# agenticLLM Hexagon

## Overview

The `agenticLLM` module provides an agentic AI assistant integrated into the EchoMaze workflow. It is designed following Clean Architecture principles, ensuring isolation from the rest of the system while being able to interact with it through well-defined ports.

## Architecture

- **Core**: Contains the `AgentUseCase`, which manages the agentic loop (Thought -> Action -> Observation).
- **Models**: Defines domain entities like `Message`, `Tool`, and `AgentState`.
- **Ports**:
    - **Drivers**: `ForAgentInteraction` (interface for the UI).
    - **Drivens**: `ForLLMProvider` (interface for LLM APIs) and `ForToolExecution` (interface for system actions).
- **Adapters**:
    - **MockLLMAdapter**: A simulated LLM provider for testing and development.
    - **LlamaCppAdapter**: Local provider using `llama-cpp-python`. Optimized for DeepSeek GGUF models.
    - **OllamaAdapter**: Local provider using the Ollama API. Supports models like llama3.1 and mistral.
    - **SystemToolExecutorAdapter**: The bridge linking the agent to EchoMaze tools.

## Integration

The agent is integrated into the EchoMaze UI and can be accessed from the main screen by pressing the **'L'** key. It is capable of answering questions and executing complex commands to manage the infrastructure.

## Configuration

### LlamaCpp Provider
1. Install the dependency: `pip install llama-cpp-python`
2. Download a DeepSeek Coder/Instruct model in GGUF format.
3. Set the environment variable `LLAMA_MODEL_PATH` to the `.gguf` file path.
4. Set `provider_type='llamacpp'` when calling `get_agent_api`.

### Ollama Provider
1. Install and run [Ollama](https://ollama.com/).
2. Pull a model (e.g., `ollama pull llama3.1`).
3. (Optional) Set `OLLAMA_MODEL` (default: `llama3.1`) and `OLLAMA_BASE_URL` (default: `http://localhost:11434`).
4. Set `provider_type='ollama'` when calling `get_agent_api`.

## Usage

```python
from agenticLLM import get_agent_api

# Initialize the agent with Ollama provider
agent = get_agent_api(provider_type='ollama')

# Ask a question
response = agent.ask("Analyze the current network topology for vulnerabilities.")
print(response)
```
