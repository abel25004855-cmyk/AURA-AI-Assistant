A.U.R.A. - Personal AI Assistant

A.U.R.A. (Advanced User Response Assistant) is a Python-based personal AI assistant designed to bring natural voice interaction and desktop automation together in one system.

It uses Ollama and Llama 3.2 for local AI conversations, Faster-Whisper for speech recognition, and Edge TTS for natural voice responses.

✨ Features
🎙️ Voice-controlled interaction
🧠 Local AI powered by Llama 3.2
🎧 Faster-Whisper speech recognition
🔊 Neural text-to-speech using Edge TTS
🛑 Interrupt A.U.R.A. while she is speaking
💡 Control screen brightness
🔊 Control system volume
📸 Take screenshots
🔒 Lock the computer
😴 Put the computer to sleep
🔄 Restart the computer
⏻ Shut down the computer
🌐 Open websites
🔎 Google search
▶️ YouTube search
🌦️ Weather information
💻 System and hardware information
📱 WhatsApp message automation
🚀 Launch Windows applications
🎭 Randomized startup introductions
🧠 AI Architecture

A.U.R.A. combines several technologies:

Technology	Purpose
Python	Core application
Ollama	Local AI runtime
Llama 3.2	AI language model
Faster-Whisper	Speech recognition
Edge TTS	Voice synthesis
PyAutoGUI	Desktop automation
Pygame	Audio playback
SoundDevice	Microphone input
Screen Brightness Control	Brightness control
Requests	Web requests
🖥️ Hardware

The project was developed and tested on an HP Victus laptop with:

CPU: AMD Ryzen 5 8645HS
GPU: NVIDIA GeForce RTX 3050 6GB
RAM: 16GB DDR5-5600
Storage: 512GB Gen 4 NVMe SSD
OS: Windows

The hardware information can be modified in the Python configuration.

🚀 Installation
Requirements
Windows
Python 3.12
Ollama
Microphone
Internet connection for initial model downloads and online features
1. Clone the repository
git clone https://github.com/YOUR-USERNAME/AURA-AI-Assistant.git
cd AURA-AI-Assistant
2. Install Python dependencies
pip install -r requirements.txt
3. Install the AI model

Install Ollama, then download Llama 3.2:

ollama pull llama3.2

You can test it with:

ollama run llama3.2
4. Run A.U.R.A.
python aura.py

A.U.R.A. will initialize the speech recognition model and then begin listening for commands.

🎙️ Voice Commands
General
"Who are you?"
"Introduce yourself"
"Goodbye"
"Exit"
Brightness
"Increase brightness"
"Decrease brightness"
"Brightness up"
"Brightness down"
"Set brightness to 70"
Volume
"Volume up"
"Volume down"
"Increase volume"
"Decrease volume"
"Mute"
Screenshots
"Take a screenshot"
"Screenshot"
"Capture screen"
Computer controls
"Lock my computer"
"Put computer to sleep"
"Restart my PC"
"Shut down my computer"
"Cancel shutdown"
Web
"Open Google"
"Open YouTube"
"Open GitHub"
"Open Gmail"
"Open WhatsApp"
Search
"Search Google for Python tutorials"
"Search YouTube for Messi highlights"
Weather
"What's the weather?"
"What's the weather in Bangalore?"
"Weather in Bahrain"
System
"What are my laptop specs?"
"Tell me about my computer"
"Run diagnostics"
"System check"
📱 WhatsApp Automation

A.U.R.A. can prepare WhatsApp messages using voice commands.

Example:

"Send WhatsApp to Rahul saying I'll be there in ten minutes."

A.U.R.A. asks for confirmation before sending.

"Send it"

or:

"Cancel"

This confirmation helps prevent accidental messages caused by speech-recognition errors.

Note: WhatsApp automation relies on the current WhatsApp Web/Desktop interface and may require updates if WhatsApp changes its interface or keyboard shortcuts.

🛑 Interrupt A.U.R.A.

A.U.R.A. can be interrupted while speaking.

Simply say:

"Stop"

Other supported phrases include:

"AURA stop"
"Shut up"
"Be quiet"
"Cancel"
"Enough"
"Silence"

This allows conversations to feel more natural instead of forcing the user to wait for a complete response.

🔐 Privacy

A.U.R.A. is designed around local AI processing.

The main language model runs locally through Ollama, while speech recognition is performed locally using Faster-Whisper after the model has been downloaded.

Internet access is still required for features such as:

Google Search
YouTube Search
Weather
WhatsApp Web
Edge TTS
⚙️ Configuration

The main settings can be changed at the top of aura.py.

VOICE = "en-GB-RyanNeural"

WHISPER_MODEL = "small.en"

DEVICE = "cpu"

COMPUTE_TYPE = "int8"

OLLAMA_MODEL = "llama3.2"
Whisper models

Available models include:

tiny.en
base.en
small.en
medium.en

Larger models generally provide better speech recognition accuracy but require more processing power and memory.

📁 Project Structure
AURA-AI-Assistant/
│
├── aura.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
└── screenshots/
    └── aura-demo.png
🔮 Future Development

A.U.R.A. is an ongoing project.

Planned improvements include:

 Wake-word detection
 "Hey A.U.R.A." activation
 Continuous listening
 Improved voice activity detection
 GPU-accelerated Whisper
 CPU/GPU temperature monitoring
 RAM and resource monitoring
 Battery monitoring
 Music and media controls
 Custom graphical interface
 Animated A.U.R.A. interface
 Plugin system
 Custom user commands
 Multi-language support
 More advanced Windows automation
👨‍💻 Author

Abel

A.U.R.A. was created as a personal AI and desktop automation project, combining local artificial intelligence, voice interaction, and Windows automation.

⭐ Contributing

Ideas, improvements, and contributions are welcome.

If you find a bug or have an idea for a new A.U.R.A. capability, open an issue or submit a pull request.

📜 License

This project is licensed under the MIT License.
