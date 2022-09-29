import json
import os

from dotenv import load_dotenv

load_dotenv()

# -------- Secrets
TOKEN: str  # Bot token
DB_URI: str  # PostgreSQL connection URI

# --- Webhooks
NOTIFICATION_WEBHOOK: str = ""  # Webhook for notifications to tim's youtube channel
TAGS_REQUESTS_WEBHOOK: str

# --- Others
AOC_SESSION_COOKIE: str
YOUTUBE_API_KEY: str = ""  # Youtube Data AP - API Key: https://developers.google.com/youtub/docs

# -------- Config
# --- Guild
GUILD_ID: int
WELCOMES_CHANNEL_ID: int
NOTIFICATION_CHANNEL_ID: int
NOTIFICATION_ROLE_ID: int

# --- AOC
AOC_CHANNEL_ID: int
AOC_ROLE_ID: int

# --- COC
COC_CHANNEL_ID: int
COC_MESSAGE_ID: int
COC_ROLE_ID: int

# --- CHALLENGES
CHALLENGE_HOST_HELPER_ROLE_ID: int
CHALLENGE_HOST_ROLE_ID: int
CHALLENGE_PARTICIPANT_ROLE_ID: int
CHALLENGE_SUBMITTED_ROLE_ID: int
CHALLENGE_WINNER_ROLE_ID: int
CHALLENGE_INFO_CHANNEL_ID: int
CHALLENGE_HIDDEN_CHANNEL_ID: int
CHALLENGE_POST_CHANNEL_ID: int
CHALLENGE_SUBMIT_CHANNEL_ID: int

# --- Staff
ADMIN_ROLES_ID: json.loads  # List[int]  # [@Tim, @Admin]
STAFF_ROLE_ID: int
TAGS_LOG_CHANNEL_ID: int

# --- Timathon
TIMATHON_PARTICIPANT_ROLE_ID: int
TIMATHON_CHANNEL_ID: int

# --- Level roles
ENGINEER_ROLE_ID: int
DEVELOPER_ROLE_ID: int
REACTION_ROLES: json.loads  # Dict[emoji_id: str, role_id: int] (json doesn't accept integer keys)
REACTION_ROLES_MESSAGE_ID: int

# --- Bots
BOT_COMMANDS_CHANNELS_ID: json.loads  # List[int]  # [#bot-commands, #commands] (main text-channel at index 0)
BOT_GAMES_CHANNEL_ID: int


# The real part, note that the env var will override.
for k, v in __annotations__.items():
    gotten = os.environ.get(k)
    if gotten is None:
        try:
            gotten = globals()[k]
        except KeyError as e:
            raise KeyError(f"env variable {e.args} is missing.")
    globals()[k] = v(gotten)

del os, json, load_dotenv, gotten, k, v
