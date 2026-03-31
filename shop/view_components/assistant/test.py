from google import genai


GEMINI_KEY="AIzaSyBWXGjUtCiQ1G7qO-iClvCOiTpQiSha_fI"
# genai.configure(api_key=GEMINI_KEY)


# Remplace par ta clé API
client = genai.Client(api_key=GEMINI_KEY)

# Lister les modèles
print("--- Modèles disponibles pour ta clé ---")
for model in client.models.list():
    print(f"ID: {model.name} | Display: {model.display_name}")