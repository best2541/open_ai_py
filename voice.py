from openai import OpenAI
client = OpenAI(api_key='')

audio_file= open("./assets/audio/wokeup.mp3", "rb")
translation = client.audio.translations.create(
  model="whisper-1", 
  file=audio_file
)
print(translation.text)