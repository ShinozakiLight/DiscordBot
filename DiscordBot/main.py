import discord
import requests
from langdetect import detect
from flask import Flask
import asyncio
import mysql.connector
from threading import Thread
from config import TOKEN


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

chatgpt_api_url = "https://api.openai.com/v1/chat/completions"

app = Flask(__name__)

# Database connection
try:
  db_config = {
    'host': 'sql12.freesqldatabase.com',
    'user': 'sql12675656',
    'password': 'yqdqbasvwV',
    'database': 'sql12675656',
  }
  db_conn = mysql.connector.connect(**db_config)
  cursor = db_conn.cursor(dictionary=True)
except mysql.connector.Error as err:
  print(f"Error connecting to the database: {err}")
  exit()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.guild:  # Check if the message is sent in a server (guild)
        server_id = message.guild.id
    else:
        print("Message not sent in a server.")
        return

    # Load the API key from the database for each server
    try:
        select_query = f"SELECT openai_key FROM users WHERE server_id = {server_id}"
        cursor.execute(select_query)
        row = cursor.fetchone()

        if row:
            OPENAI_API_KEY = row['openai_key']
        else:
            print(f"OpenAI key not found for server {server_id}.")
            return
    except Exception as e:
        print(f"Error loading OpenAI key: {e}")
        return

    # Rest of your existing code
    message_language = detect(message.content)
    gpt_language = "th"

    if message_language != gpt_language:
        translated_message = translate_function(message.content, message_language, gpt_language)
    else:
        translated_message = message.content

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'model': 'gpt-3.5-turbo-1106',
        'messages': [
            {'role': 'assistant', 'content': 'Your additional context message here'},
            {'role': 'system', 'content': 'You are a helpful assistant with a female persona.'},
            {'role': 'user', 'content': translated_message},
    ],
    'max_tokens': 1000
    }

    response = requests.post(chatgpt_api_url, headers=headers, json=payload)
    response_data = response.json()

    if 'choices' in response_data:
        gpt_response = response_data['choices'][0]['message']['content']
    else:
        print("Unexpected response format:", response_data)
        gpt_response = "Sorry, I couldn't understand your question."

    await message.channel.send(gpt_response)

def translate_function(text, source_language, target_language):
    # Implement your translation logic here
    # You may use a translation API or a library like 'googletrans' for translation
    return text

def run_flask_app():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    # Run the Flask app in a separate thread
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()

    # Run the Discord bot in the background
    client.run(TOKEN)
