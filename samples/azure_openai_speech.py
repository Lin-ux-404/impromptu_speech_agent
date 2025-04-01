import asyncio
import websockets
import json
import os
from dotenv import load_dotenv
import pyaudio
import numpy as np
import base64
import time

"""
References:
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-quickstart?pivots=programming-language-python&tabs=keyless%2Cwindows
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/realtime-audio
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-reference#realtimeservereventsessionupdated
"""

class AzureOpenAISpeechClient:
    def __init__(self):
        load_dotenv()
        self.key = os.getenv('AZURE_OPENAI_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini-realtime-preview')
        self.endpoint = self.endpoint.replace("https://", "")
        self.url = f"wss://{self.endpoint}/openai/realtime?deployment={self.deployment}&api-version=2024-10-01-preview"
        
        # Audio settings
        self.sample_rate = 24000
        self.chunk_size = 2400
        self.channels = 1
        self.format = pyaudio.paInt16
        self.record_seconds = 500

    async def connect(self):
        async with websockets.connect(self.url, additional_headers={"api-key": self.key}) as websocket:
            print("Connected to server.")
            receive_task = asyncio.create_task(self.receive_messages(websocket))
            send_task = asyncio.create_task(self.send_messages(websocket))
            record_task = await asyncio.to_thread(self.record_audio, websocket)
            await asyncio.gather(receive_task, send_task, record_task)

    async def receive_messages(self, websocket):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format, channels=self.channels, 
                       rate=self.sample_rate, output=True)

        while True:
            message = await websocket.recv()
            message_data = json.loads(message)
            if message_data.get("type") == "response.done":
                print(message_data)
            elif message_data.get("type") == "response.audio.delta":
                delta = message_data.get("delta")
                delta = base64.b64decode(delta)
                stream.write(delta)
            else:
                print(f"Received message type: {message_data.get('type')}")

    async def record_audio(self, websocket):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                       channels=self.channels,
                       rate=self.sample_rate,
                       input=True,
                       frames_per_buffer=self.chunk_size)

        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "max_response_output_tokens": 150,
                "voice": "shimmer",
                "input_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "input_audio_transcription": {
                    "model": "whisper-1",
                    "language": "en"
                }
            }
        }))

        start_time = time.time()
        while time.time() - start_time < self.record_seconds:
            data = stream.read(self.chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            base64_audio = base64.b64encode(audio_data.tobytes()).decode('utf-8')
            
            await websocket.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64_audio
            }))
            await asyncio.sleep(0.1)

        stream.stop_stream()
        stream.close()
        p.terminate()

    async def send_messages(self, websocket):
        await websocket.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["text"],
                "instructions": "You are an AI assistant who helps users come up with simple and open-ended topics for an impromptu speech. Do not give suggestions on how they can talk about the porposed topic. Please keep you answers short and simple.",
            }
        }))

if __name__ == "__main__":
    client = AzureOpenAISpeechClient()
    asyncio.run(client.connect())