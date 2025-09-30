import os
import json
from dotenv import load_dotenv
from google.cloud import texttospeech

# Load environment variables from .env file
load_dotenv()

print("--- Starting Google TTS API Diagnostic Test ---")

# 1. Check for credentials
gcp_credentials_str = os.getenv('GCP_CREDENTIALS')
if not gcp_credentials_str:
    print("🔴 CRITICAL FAILURE: GCP_CREDENTIALS environment variable not found.")
    exit()
print("✅ Step 1/4: GCP_CREDENTIALS found.")

# 2. Initialize Client
try:
    credentials = json.loads(gcp_credentials_str)
    client = texttospeech.TextToSpeechClient.from_service_account_info(credentials)
    print("✅ Step 2/4: Google TTS client initialized successfully.")
except Exception as e:
    print(f"🔴 CRITICAL FAILURE: Could not initialize client. Error: {e}")
    exit()

# 3. Prepare simple, clean data
synthesis_input = texttospeech.SynthesisInput(text="این یک پیام آزمایشی است.")
voice = texttospeech.VoiceSelectionParams(
    language_code="fa-IR", name="fa-IR-Wavenet-A"
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)
print("✅ Step 3/4: API request data prepared.")

# 4. Make the API Call
print("... Step 4/4: Sending request to Google Cloud API. Please wait...")
try:
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open("test_output.mp3", "wb") as out:
        out.write(response.audio_content)
    print("🟢 SUCCESS! API call was successful. 'test_output.mp3' has been created.")

except Exception as e:
    print(f"🔴 FAILURE: The API call failed.")
    print(f"   Error Type: {type(e).__name__}")
    print(f"   Error Details: {e}")

print("--- Test Concluded ---")