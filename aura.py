"""
A.U.R.A. v3.1
Advanced User Response Assistant

A Python-based personal AI assistant for Windows.

Features:
- Faster-Whisper speech recognition
- Ollama / Llama 3.2 local AI
- Edge TTS voice output
- Voice interruption
- Windows automation
- Brightness and volume control
- Screenshots
- Web and YouTube search
- Weather
- WhatsApp automation
- System diagnostics
"""

import asyncio
import datetime
import os
import random
import re
import subprocess
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import edge_tts
import ollama
import pygame
import pyautogui
import requests
import screen_brightness_control as sbc
import sounddevice as sd

from faster_whisper import WhisperModel


# ============================================================
# CONFIGURATION
# ============================================================

AURA_VERSION = "3.1"

OLLAMA_MODEL = "llama3.2"

WHISPER_MODEL = "small.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

VOICE = "en-GB-RyanNeural"

SAMPLE_RATE = 16000

# How long A.U.R.A. listens for a command.
LISTEN_SECONDS = 7

# Audio chunk used while A.U.R.A. is speaking.
INTERRUPT_SECONDS = 1.5

# Brightness adjustment amount when no percentage is specified.
DEFAULT_BRIGHTNESS_STEP = 10

# Volume key presses.
DEFAULT_VOLUME_PRESSES = 3

# Screenshot directory.
SCREENSHOT_DIR = Path.home() / "Pictures" / "AURA Screenshots"


# ============================================================
# HARDWARE PROFILE
# ============================================================

HARDWARE = {
    "Laptop": "HP Victus",
    "CPU": "AMD Ryzen 5 8645HS",
    "GPU": "NVIDIA GeForce RTX 3050 6GB",
    "RAM": "16GB DDR5-5600",
    "Storage": "512GB Gen 4 NVMe SSD",
    "Operating System": "Windows",
}


# ============================================================
# STATE
# ============================================================

speaking = False
stop_speaking_event = threading.Event()
shutdown_confirmation_pending = False
pending_power_action = None

conversation_history = []

pygame.mixer.init()


# ============================================================
# STARTUP INTRODUCTIONS
# ============================================================

INTRODUCTIONS = [
    "Good to see you, Mr. Abel. A.U.R.A. is online. What can I do for you?",
    "Welcome back, Mr. Abel. All core systems are operational. How may I assist?",
    "A.U.R.A. is online and ready, sir. What would you like me to do?",
    "Systems initialized successfully. Welcome back, Mr. Abel.",
    "Good evening, sir. A.U.R.A. is standing by.",
    "All systems are online, Mr. Abel. Give me a command.",
    "A.U.R.A. online. Voice interface active. How can I help?",
]


# ============================================================
# INTERRUPT PHRASES
# ============================================================

INTERRUPT_PHRASES = [
    "stop",
    "aura stop",
    "aura shut up",
    "shut up",
    "be quiet",
    "quiet",
    "enough",
    "silence",
    "cancel",
]


# ============================================================
# UTILITY
# ============================================================

def print_aura(message):
    print(f"A.U.R.A.: {message}")


def clean_text(text):
    return re.sub(r"\s+", " ", text.lower().strip())


def contains_phrase(text, phrases):
    text = clean_text(text)

    for phrase in phrases:
        if phrase in text:
            return True

    return False


# ============================================================
# TEXT TO SPEECH
# ============================================================

async def generate_tts(text, output_file):
    communicator = edge_tts.Communicate(text, VOICE)
    await communicator.save(output_file)


def interrupt_listener():
    """
    Listens for interruption commands while A.U.R.A. is speaking.

    NOTE:
    Using speakers can cause the microphone to hear A.U.R.A.'s own
    voice. Headphones provide the best interruption experience.
    """

    while speaking and not stop_speaking_event.is_set():

        try:
            audio = sd.rec(
                int(INTERRUPT_SECONDS * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32"
            )

            sd.wait()

            if not speaking:
                break

            # Ignore extremely quiet audio.
            volume = float(abs(audio).mean())

            if volume < 0.008:
                continue

            segments, _ = whisper_model.transcribe(
                audio.flatten(),
                beam_size=3,
                language="en",
                vad_filter=True,
                condition_on_previous_text=False,
            )

            heard = " ".join(segment.text for segment in segments).strip()

            if heard:
                print(f"[INTERRUPT LISTENER]: {heard}")

            if contains_phrase(heard, INTERRUPT_PHRASES):
                stop_speaking_event.set()

                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

                break

        except Exception:
            # Do not crash A.U.R.A. because of interruption listening.
            time.sleep(0.1)


def speak(text):
    """
    Speak text using Edge TTS.

    Uses a unique temporary file every time to prevent the
    Windows permission/file-lock problem caused by reusing
    aura_tts.mp3.
    """

    global speaking

    if not text:
        return

    print_aura(text)

    stop_speaking_event.clear()
    speaking = True

    temp_file = None
    listener_thread = None

    try:
        with tempfile.NamedTemporaryFile(
            prefix="aura_tts_",
            suffix=".mp3",
            delete=False
        ) as f:
            temp_file = f.name

        asyncio.run(generate_tts(text, temp_file))

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        listener_thread = threading.Thread(
            target=interrupt_listener,
            daemon=True
        )

        listener_thread.start()

        while pygame.mixer.music.get_busy():

            if stop_speaking_event.is_set():
                pygame.mixer.music.stop()
                break

            time.sleep(0.05)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass

    except Exception as e:
        print(f"[TTS ERROR] {e}")

    finally:
        speaking = False
        stop_speaking_event.clear()

        if temp_file:
            try:
                os.remove(temp_file)
            except Exception:
                pass


# ============================================================
# WHISPER
# ============================================================

print("\n============================================================")
print("                 A.U.R.A. INITIALIZATION")
print("============================================================")
print(f"Version        : {AURA_VERSION}")
print(f"Model          : {OLLAMA_MODEL}")
print(f"Whisper        : {WHISPER_MODEL}")
print(f"Device         : {WHISPER_DEVICE}")
print(f"Compute        : {WHISPER_COMPUTE}")
print(f"CPU            : {HARDWARE['CPU']}")
print(f"GPU            : {HARDWARE['GPU']}")
print(f"RAM            : {HARDWARE['RAM']}")
print("============================================================\n")

print("[A.U.R.A.] Loading Whisper...")

try:
    whisper_model = WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE
    )

    print("[A.U.R.A.] Whisper loaded.")

except Exception as e:
    print(f"[FATAL] Whisper failed to load: {e}")
    raise


# ============================================================
# SPEECH RECOGNITION
# ============================================================

def listen():
    print("\n[A.U.R.A.] Listening...")

    try:
        audio = sd.rec(
            int(LISTEN_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        volume = float(abs(audio).mean())

        if volume < 0.005:
            return ""

        segments, _ = whisper_model.transcribe(
            audio.flatten(),
            beam_size=5,
            language="en",
            vad_filter=True,
            condition_on_previous_text=False,
        )

        text = " ".join(
            segment.text for segment in segments
        ).strip()

        if text:
            print(f"You: {text}")

        return text

    except Exception as e:
        print(f"[MIC ERROR] {e}")
        return ""


# ============================================================
# BRIGHTNESS
# ============================================================

def get_brightness():
    try:
        values = sbc.get_brightness()

        if isinstance(values, list):
            return int(values[0])

        return int(values)

    except Exception:
        return None


def set_brightness(level):
    level = max(0, min(100, int(level)))

    try:
        sbc.set_brightness(level)
        return f"Brightness has been set to {level}%."

    except Exception as e:
        return f"I couldn't change the brightness. {e}"


def change_brightness(amount):
    current = get_brightness()

    if current is None:
        return "I couldn't read the current display brightness."

    new_level = max(0, min(100, current + amount))

    try:
        sbc.set_brightness(new_level)

        if amount > 0:
            return (
                f"Brightness increased by {abs(amount)}%. "
                f"It is now at {new_level}%."
            )

        return (
            f"Brightness decreased by {abs(amount)}%. "
            f"It is now at {new_level}%."
        )

    except Exception as e:
        return f"I couldn't change the brightness. {e}"


def extract_percentage(text):
    match = re.search(
        r"(?:by|to|at|level)\s*(\d{1,3})\s*(?:percent|%)?",
        text
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# VOLUME
# ============================================================

def volume_up():
    pyautogui.press("volumeup", presses=DEFAULT_VOLUME_PRESSES)
    return "Volume increased."


def volume_down():
    pyautogui.press("volumedown", presses=DEFAULT_VOLUME_PRESSES)
    return "Volume decreased."


def mute_volume():
    pyautogui.press("volumemute")
    return "Volume muted."


# ============================================================
# SCREENSHOT
# ============================================================

def take_screenshot():
    try:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        path = SCREENSHOT_DIR / f"AURA_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        return f"Screenshot saved successfully."

    except Exception as e:
        return f"I couldn't take the screenshot. {e}"


# ============================================================
# WINDOWS POWER CONTROLS
# ============================================================

def lock_pc():
    try:
        subprocess.Popen(
            ["rundll32.exe", "user32.dll,LockWorkStation"]
        )

        return "Locking the computer."

    except Exception as e:
        return f"I couldn't lock the computer. {e}"


def sleep_pc():
    try:
        subprocess.Popen(
            [
                "rundll32.exe",
                "powrprof.dll,SetSuspendState",
                "0",
                "1",
                "0"
            ]
        )

        return "Putting the computer to sleep."

    except Exception as e:
        return f"I couldn't put the computer to sleep. {e}"


def restart_pc():
    try:
        subprocess.Popen(
            ["shutdown", "/r", "/t", "5"]
        )

        return "Restart scheduled in five seconds."

    except Exception as e:
        return f"I couldn't restart the computer. {e}"


def shutdown_pc():
    try:
        subprocess.Popen(
            ["shutdown", "/s", "/t", "5"]
        )

        return "Shutdown scheduled in five seconds."

    except Exception as e:
        return f"I couldn't shut down the computer. {e}"


def cancel_shutdown():
    try:
        subprocess.Popen(
            ["shutdown", "/a"]
        )

        return "The scheduled shutdown has been cancelled."

    except Exception as e:
        return f"I couldn't cancel the shutdown. {e}"


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def system_specs():
    return (
        f"You're running A.U.R.A. on an {HARDWARE['Laptop']} with "
        f"{HARDWARE['CPU']}, {HARDWARE['GPU']}, "
        f"{HARDWARE['RAM']} of RAM, and "
        f"{HARDWARE['Storage']}."
    )


def diagnostics():
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()

        result = (
            f"Diagnostic complete. CPU usage is {cpu} percent. "
            f"Memory usage is {ram} percent."
        )

        if battery:
            result += (
                f" Battery is at {battery.percent} percent."
            )

        return result

    except Exception as e:
        return f"Diagnostics completed with limited information. {e}"


# ============================================================
# WEB FUNCTIONS
# ============================================================

def open_google():
    webbrowser.open("https://www.google.com")
    return "Opening Google."


def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."


def open_github():
    webbrowser.open("https://github.com")
    return "Opening GitHub."


def open_gmail():
    webbrowser.open("https://mail.google.com")
    return "Opening Gmail."


def open_chatgpt():
    webbrowser.open("https://chatgpt.com")
    return "Opening ChatGPT."


def open_instagram():
    webbrowser.open("https://www.instagram.com")
    return "Opening Instagram."


def open_reddit():
    webbrowser.open("https://www.reddit.com")
    return "Opening Reddit."


def open_whatsapp():
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "whatsapp:"],
            shell=False
        )

        time.sleep(2)

        return "Opening WhatsApp."

    except Exception:
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web."


def google_search(query):
    query = query.strip()

    if not query:
        return "What would you like me to search for?"

    url = "https://www.google.com/search?q=" + quote_plus(query)

    webbrowser.open(url)

    return f"Searching Google for {query}."


def youtube_search(query):
    query = query.strip()

    if not query:
        return "What would you like me to search for on YouTube?"

    url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    webbrowser.open(url)

    return f"Searching YouTube for {query}."


# ============================================================
# WEATHER
# ============================================================

def weather(city="Bangalore"):
    try:
        url = (
            "https://wttr.in/"
            + quote_plus(city)
            + "?format=j1"
        )

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "AURA-AI-Assistant"}
        )

        data = response.json()

        current = data["current_condition"][0]

        temperature = current["temp_C"]
        feels = current["FeelsLikeC"]
        description = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]

        return (
            f"The current weather in {city} is {description}. "
            f"It's {temperature} degrees Celsius, "
            f"feels like {feels}, with {humidity} percent humidity."
        )

    except Exception:
        return "I couldn't retrieve the weather right now."


# ============================================================
# WINDOWS APPLICATIONS
# ============================================================

APP_COMMANDS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
}


def launch_app(app):
    app = app.lower().strip()

    if app in APP_COMMANDS:

        try:
            subprocess.Popen(APP_COMMANDS[app])
            return f"Launching {app}."

        except Exception as e:
            return f"I couldn't launch {app}. {e}"

    return f"I don't have a configured launcher for {app}."


# ============================================================
# WHATSAPP
# ============================================================

pending_whatsapp = None


def prepare_whatsapp(contact, message):
    global pending_whatsapp

    pending_whatsapp = {
        "contact": contact.strip(),
        "message": message.strip()
    }

    return (
        f"I've prepared a WhatsApp message for "
        f"{contact}. The message says: "
        f"{message}. Say 'send it' to send it, "
        f"or 'cancel' to cancel."
    )


def send_whatsapp():
    global pending_whatsapp

    if not pending_whatsapp:
        return "There is no WhatsApp message waiting to be sent."

    contact = pending_whatsapp["contact"]
    message = pending_whatsapp["message"]

    try:
        # Open WhatsApp Web.
        webbrowser.open("https://web.whatsapp.com")

        # Give the browser time to load.
        time.sleep(7)

        # Try WhatsApp Web's search shortcut.
        pyautogui.hotkey("ctrl", "alt", "/")
        time.sleep(1)

        pyautogui.write(
            contact,
            interval=0.03
        )

        pyautogui.press("enter")

        time.sleep(2)

        pyautogui.write(
            message,
            interval=0.01
        )

        pyautogui.press("enter")

        pending_whatsapp = None

        return f"Message sent to {contact}."

    except Exception as e:
        return (
            "I couldn't complete the WhatsApp automation. "
            "Please check that WhatsApp Web is open and logged in."
        )


# ============================================================
# POWER CONFIRMATION
# ============================================================

def request_power_confirmation(action):
    global pending_power_action

    pending_power_action = action

    return (
        f"Confirm that you want me to {action} the computer. "
        f"Say 'confirm' to proceed or 'cancel' to abort."
    )


def execute_pending_power_action():
    global pending_power_action

    action = pending_power_action
    pending_power_action = None

    if action == "restart":
        return restart_pc()

    if action == "shut down":
        return shutdown_pc()

    if action == "sleep":
        return sleep_pc()

    return "No power action is pending."


# ============================================================
# AI CHAT
# ============================================================

SYSTEM_PROMPT = """
You are A.U.R.A., Advanced User Response Assistant.

You are a personal desktop AI assistant created by Abel.

Address the user as "sir" or "Mr. Abel" occasionally.
Do not constantly repeat the user's name.

Your personality is intelligent, calm, concise, confident and helpful.

You are running on a Windows HP Victus computer.

Hardware:
- AMD Ryzen 5 8645HS
- NVIDIA GeForce RTX 3050 6GB
- 16GB DDR5-5600 RAM
- 512GB Gen 4 NVMe SSD

You are a local AI assistant powered by Ollama and Llama 3.2.

Do not claim that you performed a computer action unless the
Python application actually performed that action.

If asked about your capabilities, explain that you can control
brightness, volume, screenshots, Windows power functions,
web searches, weather, applications and WhatsApp automation.
"""


def ask_ai(user_text):
    global conversation_history

    try:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages.extend(conversation_history[-8:])

        messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )

        answer = response["message"]["content"].strip()

        conversation_history.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        conversation_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer

    except Exception as e:
        print(f"[OLLAMA ERROR] {e}")

        return (
            "I'm unable to reach my local AI model right now. "
            "Please make sure Ollama is running and Llama 3.2 is installed."
        )


# ============================================================
# COMMAND PROCESSOR
# ============================================================

def process_command(command):
    global pending_power_action
    global pending_whatsapp

    text = clean_text(command)

    if not text:
        return None

    # --------------------------------------------------------
    # POWER CONFIRMATIONS
    # --------------------------------------------------------

    if pending_power_action:

        if text in [
            "confirm",
            "confirmed",
            "yes",
            "yes do it",
            "proceed",
            "go ahead"
        ]:

            return execute_pending_power_action()

        if text in [
            "cancel",
            "no",
            "abort",
            "don't",
            "do not"
        ]:

            pending_power_action = None
            return "Power operation cancelled."

        return (
            "I need confirmation. Say confirm to proceed "
            "or cancel to abort."
        )

    # --------------------------------------------------------
    # WHATSAPP CONFIRMATION
    # --------------------------------------------------------

    if pending_whatsapp:

        if text in [
            "send it",
            "send",
            "yes",
            "confirm",
            "go ahead"
        ]:
            return send_whatsapp()

        if text in [
            "cancel",
            "cancel it",
            "no",
            "abort"
        ]:
            pending_whatsapp = None
            return "WhatsApp message cancelled."

        return (
            "The WhatsApp message is ready. "
            "Say send it to send it, or cancel."
        )

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if text in [
        "exit",
        "quit",
        "goodbye",
        "good bye",
        "power down aura",
        "shutdown aura"
    ]:
        speak("Understood, Mr. Abel. A.U.R.A. shutting down.")
        raise SystemExit

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if contains_phrase(text, INTERRUPT_PHRASES):
        stop_speaking_event.set()

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        return None

    # --------------------------------------------------------
    # INTRODUCTION
    # --------------------------------------------------------

    if (
        "who are you" in text
        or "introduce yourself" in text
        or "what are you" in text
    ):
        return random.choice(INTRODUCTIONS)

    # --------------------------------------------------------
    # BRIGHTNESS
    # --------------------------------------------------------

    if "brightness" in text:

        # "set brightness to 60"
        if any(word in text for word in [
            "set",
            "make",
            "change"
        ]):

            percentage = extract_percentage(text)

            if percentage is not None:

                # If the phrase says "decrease by X",
                # it should remain a relative adjustment.
                if "decrease" in text or "lower" in text:
                    return change_brightness(-percentage)

                if "increase" in text or "raise" in text:
                    return change_brightness(percentage)

                return set_brightness(percentage)

        percentage = extract_percentage(text)

        if percentage is not None:

            if any(word in text for word in [
                "decrease",
                "lower",
                "dimmer",
                "down"
            ]):
                return change_brightness(-percentage)

            if any(word in text for word in [
                "increase",
                "raise",
                "brighter",
                "up"
            ]):
                return change_brightness(percentage)

        if any(word in text for word in [
            "decrease",
            "lower",
            "down",
            "dimmer"
        ]):
            return change_brightness(
                -DEFAULT_BRIGHTNESS_STEP
            )

        if any(word in text for word in [
            "increase",
            "raise",
            "up",
            "brighter"
        ]):
            return change_brightness(
                DEFAULT_BRIGHTNESS_STEP
            )

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if any(word in text for word in [
        "volume",
        "sound"
    ]):

        if "mute" in text:
            return mute_volume()

        if any(word in text for word in [
            "increase",
            "up",
            "louder",
            "raise"
        ]):
            return volume_up()

        if any(word in text for word in [
            "decrease",
            "down",
            "quieter",
            "lower"
        ]):
            return volume_down()

    if text in [
        "mute",
        "mute volume",
        "mute the computer"
    ]:
        return mute_volume()

    # --------------------------------------------------------
    # SCREENSHOT
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "take a screenshot",
        "take screenshot",
        "screenshot",
        "capture screen",
        "capture the screen"
    ]):
        return take_screenshot()

    # --------------------------------------------------------
    # LOCK
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "lock my computer",
        "lock the computer",
        "lock pc",
        "lock my pc"
    ]):
        return lock_pc()

    # --------------------------------------------------------
    # SLEEP
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "put computer to sleep",
        "put the computer to sleep",
        "sleep computer",
        "sleep pc"
    ]):
        return request_power_confirmation("put to sleep")

    # --------------------------------------------------------
    # RESTART
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "restart my pc",
        "restart the pc",
        "restart my computer",
        "restart the computer",
        "reboot my pc",
        "reboot my computer"
    ]):
        pending_power_action = "restart"

        return (
            "Confirm that you want me to restart the computer. "
            "Say confirm to proceed or cancel to abort."
        )

    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "shut down my pc",
        "shut down the pc",
        "shut down my computer",
        "shut down the computer",
        "shutdown my pc",
        "shutdown my computer",
        "turn off my computer",
        "turn off the computer"
    ]):
        pending_power_action = "shut down"

        return (
            "Confirm that you want me to shut down the computer. "
            "Say confirm to proceed or cancel to abort."
        )

    # --------------------------------------------------------
    # CANCEL SHUTDOWN
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "cancel shutdown",
        "abort shutdown",
        "cancel restart"
    ]):
        return cancel_shutdown()

    # --------------------------------------------------------
    # LAPTOP SPECS
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "laptop specs",
        "computer specs",
        "pc specs",
        "my specs",
        "my laptop",
        "tell me about my computer"
    ]):
        return system_specs()

    # --------------------------------------------------------
    # DIAGNOSTICS
    # --------------------------------------------------------

    if any(phrase in text for phrase in [
        "run diagnostics",
        "run diagnostic",
        "system check",
        "check my computer",
        "check the computer"
    ]):
        return diagnostics()

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    if "weather" in text:

        match = re.search(
            r"weather\s+(?:in|at|for)\s+(.+)",
            text
        )

        if match:
            city = match.group(1).strip()
            return weather(city)

        return weather()

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    google_match = re.search(
        r"(?:search google for|google search for|google)\s+(.+)",
        text
    )

    if google_match:
        return google_search(
            google_match.group(1)
        )

    # --------------------------------------------------------
    # YOUTUBE SEARCH
    # --------------------------------------------------------

    youtube_match = re.search(
        r"(?:search youtube for|youtube search for|youtube)\s+(.+)",
        text
    )

    if youtube_match:
        return youtube_search(
            youtube_match.group(1)
        )

    # --------------------------------------------------------
    # OPEN WEBSITES
    # --------------------------------------------------------

    if "open google" in text:
        return open_google()

    if "open youtube" in text:
        return open_youtube()

    if "open github" in text:
        return open_github()

    if "open gmail" in text:
        return open_gmail()

    if "open chatgpt" in text:
        return open_chatgpt()

    if "open instagram" in text:
        return open_instagram()

    if "open reddit" in text:
        return open_reddit()

    if "open whatsapp" in text:
        return open_whatsapp()

    # --------------------------------------------------------
    # WHATSAPP MESSAGE
    # --------------------------------------------------------

    whatsapp_match = re.search(
        r"(?:send whatsapp to|message|whatsapp)\s+(.+?)"
        r"\s+(?:saying|that says|with the message)\s+(.+)",
        text
    )

    if whatsapp_match:

        contact = whatsapp_match.group(1).strip()
        message = whatsapp_match.group(2).strip()

        return prepare_whatsapp(
            contact,
            message
        )

    # --------------------------------------------------------
    # WINDOWS APPS
    # --------------------------------------------------------

    for app in APP_COMMANDS:

        if (
            text == f"open {app}"
            or text == f"launch {app}"
            or text == f"start {app}"
        ):
            return launch_app(app)

    # --------------------------------------------------------
    # AI FALLBACK
    # --------------------------------------------------------

    return ask_ai(command)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n[A.U.R.A.] System initialization complete.\n")

    intro = random.choice(INTRODUCTIONS)

    speak(intro)

    while True:

        try:

            command = listen()

            if not command:
                continue

            result = process_command(command)

            if result:
                speak(result)

        except KeyboardInterrupt:
            print("\n[A.U.R.A.] Manual shutdown.")
            break

        except SystemExit:
            break

        except Exception as e:
            print(f"[MAIN ERROR] {e}")
            speak(
                "I encountered an unexpected error, sir."
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
