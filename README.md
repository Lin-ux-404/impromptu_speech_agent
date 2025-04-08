# Impromptu Speech Agent


## Features

- Real-time speech-to-text transcription using Whisper
- Natural voice responses using Azure OpenAI's voice synthesis
- Continuous conversation capability with voice activity detection
- Low-latency audio processing for smooth interaction
- Support for interruptions and mid-conversation responses

## Prerequisites

- Python 3.8 or higher
- Azure OpenAI API access
- A microphone for audio input
- Speakers or headphones for audio output

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd impromptu_speech_agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your Azure OpenAI credentials:
```env
AZURE_OPENAI_ENDPOINT="your-endpoint"
AZURE_OPENAI_KEY="your-key"
AZURE_OPENAI_CHAT_DEPLOYMENT="your-deployment"
```

## Usage

Run the speech agent:
```bash
python azure_openai_speech.py
```

run the sk agent sample with:
```bash
streamlit run sk_agent_sample.py
```

Once started, you can:
- Begin speaking naturally - the agent will detect your voice automatically
- Wait for the agent's response
- Interrupt or continue the conversation as needed
- Press Ctrl+C to end the session

## Configuration

The agent can be configured by modifying the following parameters in `azure_openai_speech.py`:

- `sample_rate`: Audio sampling rate (default: 24000)
- `chunk_size`: Audio processing chunk size (default: 2400)
- Voice activity detection settings in the `session.update` configuration

## Troubleshooting

Common issues:
1. **Audio device not found**: Ensure your microphone is properly connected and selected as the default input device
2. **Connection errors**: Verify your Azure OpenAI credentials and internet connection
3. **High latency**: Adjust the chunk_size and sample_rate parameters for your system's capabilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Azure OpenAI for providing the real-time audio API
- OpenAI's Whisper model for speech recognition
- The Python WebSockets community

## Resources and References

### Azure AI Agents
- [Exploring the Semantic Kernel ChatCompletionAgent](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/chat-completion-agent?pivots=programming-language-python)
- [Exploring the Semantic Kernel OpenAIAssistantAgent](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/assistant-agent?pivots=programming-language-python)
- [Exploring the Semantic Kernel AzureAIAgent](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/azure-ai-agent?pivots=programming-language-python)
- [Exploring Agent Collaboration in AgentChat](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-chat?pivots=programming-language-python)

### Semantic Kernel
- [Understanding the kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/kernel?pivots=programming-language-python)
- [An Overview of the Agent Architecture](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-architecture?pivots=programming-language-python)
- [Semantic Kernel Components](https://learn.microsoft.com/en-us/semantic-kernel/concepts/semantic-kernel-components?pivots=programming-language-python)
- [Function calling with chat completion](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/function-calling/?pivots=programming-language-python)

### Additional Resources
- [Develop an Azure AI agent with the Semantic Kernel SDK](https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/04-semantic-kernel.html#create-an-azure-ai-foundry-project)
