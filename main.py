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

# Get credentials from environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
BOT_TOKEN = os.getenv('BOT_TOKEN')

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
        # Start with just first channel to initialize
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
        token = await self.get_access_token()
        headers = {
            'Client-ID': CLIENT_ID,
            'Authorization': f'Bearer {token}'
        }
        
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        async with self._http.session.get(url, headers=headers) as resp:
            data = await resp.json()
            return len(data.get('data', [])) > 0

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
            channel_obj = self.get_channel(channel)
            if channel_obj:
                message = random.choice(messages)
                await channel_obj.send(message)
                logging.info(f'Sent message to {channel}: {message}')
            else:
                logging.error(f'Could not get channel object for {channel}')
        except Exception as e:
            logging.error(f'Error sending message to {channel}: {e}')

    @commands.command(name='hello')
    async def hello_command(self, ctx):
        """Test command to check if bot is working."""
        await ctx.send(f'Hello {ctx.author.name}! 👋')

async def main():
    # Verify environment variables
    if not all([CLIENT_ID, CLIENT_SECRET, BOT_TOKEN]):
        logging.error("Missing required environment variables. Check your .env file!")
        return
        
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