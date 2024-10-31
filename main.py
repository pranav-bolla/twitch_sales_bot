import os
from dotenv import load_dotenv
import twitchio
from twitchio.ext import commands, routines
import asyncio
import logging
import random
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Your Twitch credentials
CLIENT_ID = '1m7da2v2fpqz1wjlr97fqc8bcu0ofk'
CLIENT_SECRET = 'rk96cphwla8qgm0t10tldt93bjbkp2'
BOT_TOKEN = 'oauth:yunxg2byn125nc5e5pfvk0b3yccach'

# Constants
BATCH_SIZE = 20  # Number of channels to join at once
JOIN_DELAY = 2   # Seconds to wait between joining batches

# Channels to monitor
CHANNELS_TO_MONITOR = [
    'scarlettpls',
    'chaosrainlolpatchesandpiecesaeg',
    'horaderazor317',
    'shurjoka',
    'ygorr7fps',
    'caseoh_',
    'roy91c',
    'scump',
    'dooby3d',
    'xrockspvp',
    'ariplaytc',
    'benx',
    'stream20088',
    'tifaishottie',
    'bastighg',
    'pmoney4president',
    'ymdkria',
    'slvrlive',
    'gripey',
    'mervyntv',
    'rostislav_999',
    'loud_coringa',
    'aizenkyoga',
    'thezarox03_tv',
    'castcrafter',
    'superwill1972',
    'deepins02',
    'dbd_god1298',
    'rmcsport',
    'therealknossi',
    'mopaslots',
    'papaplatte',
    'pedlinhoz',
    'morphilina',
    'caedrel',
    'gentlerainfall',
    'diiamond7',
    't2x2',
    'kennyoffi',
    'hyperhelius',
    'viperstrike28',
    'jynxzi',
    'justriadhtv',
    'oozie',
    'kidgi0',
    'mich1',
    'boltz4x',
    'stegi',
    'la_toulousainetv',
    'xxbnice999',
    'derzko69',
    'gruendauer_spieleck',
    'deku_qck',
    'owlfn',
    'qassimiento',
    'giuliofracalvieri',
    'tenz',
    'rlkloirin',
    'shottamiki',
    'luc1dg',
    'brino',
    'mustibaz',
    'jumpar',
    '1trippi',
    'zesty27',
    'riotgames',
    'stintik',
    'aenot',
    'flapiix',
    'swagg',
    'egowydd',
    'hersocials',
    'saanti_slots',
    'cleohamburg',
    'bruno_mono',
    'jidionpremium',
    'nkbrothers',
    'drakeoffc',
    'vvcw',
    'xoxogledi',
    'punkill',
    'fadabalinha',
    'timthetatman',
    'elmariana',
    'fabo',
    'nicotine84',
    'mooda',
    'solarties',
    'chappycherri',
    'liamnouel33127',
    'wraxxyz',
    'sylveey',
    'prozexrlk',
    'bdj_insider',
    'meta_qq',
    'kucoofps',
    'mexsey',
    'wichtiger',
    'azhunky',
    'djmariio',
    'xboxgoat15',
    'adamdadams'
]

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=BOT_TOKEN,
            prefix='!',
            initial_channels=CHANNELS_TO_MONITOR[:1],
            nick='souppdog'
        )
        self.last_live_status = {}
        self.all_channels = CHANNELS_TO_MONITOR
        self.joined_channels = set()

    async def join_channels_in_batches(self):
        """Join channels in batches to avoid rate limits"""
        for i in range(0, len(self.all_channels), BATCH_SIZE):
            batch = self.all_channels[i:i + BATCH_SIZE]
            for channel in batch:
                if channel not in self.joined_channels:
                    try:
                        await self.join_channels([channel])
                        self.joined_channels.add(channel)
                        logging.info(f"Successfully joined channel: {channel}")
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logging.error(f"Error joining channel {channel}: {e}")
            
            if i + BATCH_SIZE < len(self.all_channels):
                logging.info(f"Waiting {JOIN_DELAY} seconds before next batch...")
                await asyncio.sleep(JOIN_DELAY)

    async def get_access_token(self):
        """Get OAuth access token using client credentials"""
        auth_url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        async with self._http.session.post(auth_url, params=params) as resp:
            data = await resp.json()
            return data.get('access_token')

    async def check_stream_status(self, channel):
        """Check if a channel is live using raw API call"""
        try:
            token = await self.get_access_token()
            headers = {
                'Client-ID': CLIENT_ID,
                'Authorization': f'Bearer {token}'
            }
            
            url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
            async with self._http.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    logging.error(f"API Error for {channel}: Status {resp.status}")
                    return False
                    
                data = await resp.json()
                streams = data.get('data', [])
                if streams:
                    stream_info = streams[0]
                    logging.info(f"Stream info for {channel}: Type={stream_info.get('type')}, Viewer Count={stream_info.get('viewer_count')}")
                return bool(streams)

        except Exception as e:
            logging.error(f"Error checking status for {channel}: {str(e)}")
            return False

    async def event_ready(self):
        """Called when bot is ready."""
        logging.info(f'Bot is ready! | {self.nick}')
        
        # Join remaining channels in batches
        await self.join_channels_in_batches()
        
        # Do initial check
        await self.check_streams()
        
        # Start checking routine
        self.check_streams_routine.start()

    async def check_streams(self):
        """Check if monitored channels are live."""
        try:
            for channel in self.joined_channels:
                try:
                    is_live = await self.check_stream_status(channel)
                    was_live = self.last_live_status.get(channel, False)

                    if is_live and not was_live:
                        # Double check to prevent false positives
                        await asyncio.sleep(5)  # Wait 5 seconds
                        is_still_live = await self.check_stream_status(channel)
                        if is_still_live:
                            await self.send_live_message(channel)
                            self.last_live_status[channel] = True
                            logging.info(f"{channel} went live!")
                    elif not is_live and was_live:
                        self.last_live_status[channel] = False
                        logging.info(f"{channel} went offline")

                except Exception as e:
                    logging.error(f'Error checking status for {channel}: {e}')

        except Exception as e:
            logging.error(f'Error in check_streams: {e}')
            logging.error(f'Error details:', exc_info=True)

    @routines.routine(seconds=60)
    async def check_streams_routine(self):
        await self.check_streams()

    async def event_message(self, message):
        """Runs every time a message is sent in chat."""
        # Ignore messages from the bot itself
        if message.echo:
            return

        # Only process messages that start with our prefix and are our commands
        if message.content.startswith('!'):
            if message.content.lower() == '!hello':
                await self.hello_command(message.channel, message)

    async def send_live_message(self, channel):
        """Send a message when a channel goes live."""
        messages = [
            "Good luck with the stream! 🎮 Your friends from savedgg",
            "Have an awesome stream! ✨ Your friends from savedgg",
            "Time to shine! Good luck with the stream! 🌟 Your friends from savedgg",
            "Wishing you a fantastic stream! 🎯 Your friends from savedgg",
            "Let's go! Have a great stream! 🚀 Your friends from savedgg",
            "Hope you have an amazing stream! ⭐ Your friends from savedgg"
        ]
        
        try:
            # Check if channel is in followers-only mode
            token = await self.get_access_token()
            headers = {
                'Client-ID': CLIENT_ID,
                'Authorization': f'Bearer {token}'
            }
            
            # Get channel ID first
            url = f'https://api.twitch.tv/helix/users?login={channel}'
            async with self._http.session.get(url, headers=headers) as resp:
                data = await resp.json()
                if not data.get('data'):
                    logging.error(f'Could not get channel ID for {channel}')
                    return
                channel_id = data['data'][0]['id']

            # Check chat settings
            url = f'https://api.twitch.tv/helix/chat/settings?broadcaster_id={channel_id}'
            async with self._http.session.get(url, headers=headers) as resp:
                data = await resp.json()
                if data.get('data'):
                    chat_settings = data['data'][0]
                    if chat_settings.get('follower_mode'):
                        logging.info(f"Skipping {channel} - followers-only mode enabled")
                        return
                    if chat_settings.get('subscriber_mode'):
                        logging.info(f"Skipping {channel} - subscribers-only mode enabled")
                        return
                    if chat_settings.get('emote_mode'):
                        logging.info(f"Skipping {channel} - emote-only mode enabled")
                        return
                    if chat_settings.get('slow_mode'):
                        logging.info(f"Channel {channel} has slow mode enabled - continuing anyway")

            # Get channel object and verify it's still live
            channel_obj = self.get_channel(channel)
            if channel_obj:
                is_still_live = await self.check_stream_status(channel)
                if not is_still_live:
                    logging.info(f"Channel {channel} went offline before sending message")
                    return

                message = random.choice(messages)
                await channel_obj.send(message)
                logging.info(f'Sent message to {channel}: {message}')
            else:
                logging.error(f'Could not get channel object for {channel}')
                
        except twitchio.errors.AuthenticationError:
            logging.error(f"Authentication error for {channel} - might be banned or chat restricted")
        except Exception as e:
            logging.error(f'Error sending message to {channel}: {e}')
            if 'followers-only' in str(e).lower():
                logging.info(f"Channel {channel} appears to be in followers-only mode")

    @commands.command(name='hello')
    async def hello_command(self, ctx):
        """Test command to check if bot is working."""
        await ctx.send(f'Hello {ctx.author.name}! 👋')

async def main():
    bot = Bot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
        logging.error(f'Error details:', exc_info=True)
    finally:
        logging.info("Bot shutdown complete")

if __name__ == "__main__":
    logging.info("Starting bot...")
    asyncio.run(main())