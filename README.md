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
pip install websockets python-dotenv pyaudio numpy
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
python azure-openai-speech.py
```

Once started, you can:
- Begin speaking naturally - the agent will detect your voice automatically
- Wait for the agent's response
- Interrupt or continue the conversation as needed
- Press Ctrl+C to end the session

## Configuration

The agent can be configured by modifying the following parameters in `azure-openai-speech.py`:

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