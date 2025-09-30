import os
import json
import io
from google.cloud import texttospeech
from pydub import AudioSegment

def create_podcast_from_text(text_content: str, output_filename: str) -> str | None:
    gcp_credentials = os.getenv('GCP_CREDENTIALS')
    if not gcp_credentials:
        print("Critical error: GCP_CREDENTIALS environment variable not found.")
        return None

    try:
        credentials = json.loads(gcp_credentials)
        client = texttospeech.TextToSpeechClient.from_service_account_info(credentials)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in GCP_CREDENTIALS environment variable.")
        return None
    except Exception as e:
        print(f"Error initializing TextToSpeech client: {e}")
        return None

    # Split text into chunks
    chunks = [chunk.strip() for chunk in text_content.split("\n---\n") if chunk.strip()]
    total_chunks = len(chunks)

    if total_chunks == 0:
        print("No valid text chunks to process.")
        return None

    audio_segments = []

    for i, chunk in enumerate(chunks):
        print(f"Synthesizing audio for chunk {i+1}/{total_chunks}...")

        synthesis_input = texttospeech.SynthesisInput(text=chunk)

        voice = texttospeech.VoiceSelectionParams(
            language_code="fa-IR",
            name="fa-IR-Wavenet-A",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
        except Exception as e:
            print(f"Error during synthesize_speech API call for chunk {i+1}: {e}")
            continue  # Skip this chunk and try the next one

        if response.audio_content:
            segment = AudioSegment.from_mp3(io.BytesIO(response.audio_content))
            audio_segments.append(segment)
        else:
            print(f"No audio content returned for chunk {i+1}")

    if not audio_segments:
        print("No audio segments were generated.")
        return None

    # Combine audio segments
    full_podcast = audio_segments[0]
    for segment in audio_segments[1:]:
        full_podcast += segment

    # Export combined audio
    full_podcast.export(output_filename, format="mp3")

    print(f"Podcast created successfully: {output_filename}")
    return output_filename
