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
    - **SystemToolExecutorAdapter**: The bridge linking the agent to EchoMaze tools.

## Integration

The agent is integrated into the EchoMaze UI and can be accessed from the main screen by pressing the **'L'** key. It is capable of answering questions and executing complex commands to manage the infrastructure.

## Configuration

To use the local LlamaCpp provider with DeepSeek:

1. Install the dependency: `pip install llama-cpp-python`
2. Download a DeepSeek Coder/Instruct model in GGUF format.
3. Set the environment variable `LLAMA_MODEL_PATH` to the `.gguf` file path.
4. (Optional) Set `AGENT_PROVIDER=llamacpp` in your environment.

## Usage

```python
from agenticLLM import get_agent_api

# Initialize the agent with LlamaCpp provider
agent = get_agent_api(provider_type='llamacpp')

# Ask a question
response = agent.ask("Analyze the current network topology for vulnerabilities.")
print(response)
```
