import os

TOKEN = os.environ.get("TOKEN")  # Bot token
POSTGRES = os.environ.get("DB_URI")  # PostgreSQL connection URI

YOUTUBE_API_KEY = os.environ.get(
    "YOUTUBE_API_KEY"
)  # Youtube Data API v3 - API Key: https://developers.google.com/youtube/v3/docs

# NOTIFICATION_WEBHOOK = ""  # Webhook for notifications to tims youtube channel

NOTIFICATION_ROLE_ID: int = int(
    os.environ.get("NOTIFICATION_ROLE_ID")
)  # Role to be mentioned in announcements
NOTIFICATION_CHANNEL_ID: int = int(
    os.environ.get("NOTIFICATION_CHANNEL_ID")
)  # Channel to post notifications in

AOC_SESSION_COOKIE = os.environ.get("AOC_SESSION_COOKIE")

STAFF_ROLE_ID = int(os.environ.get("STAFF_ROLE_ID"))
CHALLENGE_HOST_ROLE_ID = int(os.environ.get("CHALLENGE_HOST_ROLE_ID"))
CHALLENGE_HOST_HELPER_ROLE_ID = int(os.environ.get("CHALLENGE_HOST_HELPER_ROLE_ID"))
CHALLENGE_WINNER_ROLE_ID = int(os.environ.get("CHALLENGE_WINNER_ROLE_ID"))
SUBMITTED_ROLE_ID = int(os.environ.get("SUBMITTED_ROLE_ID"))

INFO_CHANNEL_ID = int(os.environ.get("INFO_CHANNEL_ID"))
BOT_GAMES_CHANNEL_ID = int(os.environ.get("BOT_GAMES_CHANNEL_ID"))