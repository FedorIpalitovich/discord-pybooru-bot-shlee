from typing import Final
from random import randint
import urllib.parse
import requests
import json
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message

# load from dotenv
load_dotenv()
help_instructions: Final[str] = os.getenv('HELP_INSTRUCTIONS')
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
api_key: Final[str] = os.getenv('API_KEY')
user_id: Final[str] = os.getenv('USER_ID')

# bot setup
intents: Intents = Intents.default()
intents.message_content = True 
client: Client = Client(intents=intents)

# log func
async def log_messages(message:Message) -> None:
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')

# user request handling
async def user_request_handling(message: Message, user_message: str) -> dict:
    user_request: dict = {
        'random': False,
        'id': None,
        'pid': '1',
        'count': '1',
        'tags': []
        } 
    content_tags: list = user_message.split()

    if content_tags[0] == '!random':
        user_request['random'] = True
        await message.channel.send('питон для пидорасов')
    elif content_tags[0] != '!search':
        await message.channel.send('питон для пидорасов')
        return None
    del content_tags[0]

    for tags in content_tags:
        if ':' in tags:
            if 'pid:' in tags:
                user_request['pid'] = tags[4:]
            elif 'id:' in tags:
                user_request['id'] = tags[3:]
            elif 'count:' in tags:
                user_request['count'] = tags[6:]
            else: user_request['tags'].append(tags)
            continue
        user_request['tags'].append(tags)
        
        for value in user_request:
            if not value.isdigit:
                await message.channel.send('ошибка значений параметров')
                return None
    return user_request

# message func
async def send_message(message: Message, user_request: dict, api_key: str, user_id: str) -> None:
    if int(user_request['count']) > 100:
        user_request['count'] = '100'
    tags = 'tags='
    if user_request['id']:
        tags = f'id={user_request['id']}'
    else:
        for a in user_request['tags']:
            tags += urllib.parse.quote(a) + '+'
    request_url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={user_request['count']}&pid={user_request['pid']}&{tags}'
    print(request_url)
    if api_key and user_id:
        request_url += f'&api_key={api_key}&user_id={user_id}'
    
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f'Non-200 response from Gelbooru, got {response.status_code} instead')

    try:
        json_response = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        return
    
    if 'post' not in json_response:
        return
    elif isinstance(json_response['post'], dict):
        json_response_images_data = [json_response['post']]
    else:
        json_response_images_data = json_response['post']

    for json_item in json_response_images_data:
        full_url = json_item['file_url']
        await message.channel.send(f'{full_url}')

# bot startup terminal output
@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')


# handling incoming messages
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    await log_messages(message)

    user_message = message.content

    if not user_message.startswith('!'):
        return
    
    if message.channel.nsfw == False:
        await message.reply('nsfw channels only')
        return
    
    if user_message.startswith('!help'):
        await message.channel.send(f'{help_instructions}')
        return
    

    user_request = await user_request_handling(message, user_message.lower())
    if user_request:
        await send_message(message, user_request, api_key, user_id)


# main entry point
def main() -> None:
    client.run(token=TOKEN)


if __name__ == '__main__':
    main()
