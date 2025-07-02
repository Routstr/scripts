import os
import asyncio
import requests
import json
from pynostr.event import Event
from pynostr.relay_manager import RelayManager
from pynostr.filters import FiltersList, Filters
from pynostr.event import EventKind
from pynostr.key import PrivateKey
import time
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Placeholder: User should set this in their .env file
ROUTSTR_API_BASE_URL = os.getenv("ROUTSTR_API_URL", "https://api.example.com")
ROUTSTR_API_CHAT_URL = ROUTSTR_API_BASE_URL + "/v1/chat/completions"
NOSTR_BOT_NSEC = os.getenv("NOSTR_BOT_NSEC")
ROUTSTR_API_KEY = os.getenv("ROUTSTR_API_KEY")
MAIN_RELAYS = ["wss://relay.damus.io", "wss://nos.lol"]
BACKUP_RELAYS = ["wss://multiplexer.huszonegy.world"]
STATUS_FILE = "routstr_status.json" # File to store last status and event ID

# --- Helper Functions ---

def generate_comment(status: str) -> str:
    """Generates a quirky comment based on Routstr's status."""
    if status == "up":
        return "✅ Routstr is routing! Your Freedom AI Tech is routing requests as usual. \nProvider: `"+ROUTSTR_API_BASE_URL+"` \n"
    else:
        return "🔴 Routstr is NOT routing! Fear not, we have other providers. \nProvider: `"+ROUTSTR_API_BASE_URL+"` \n"

def load_last_status() -> tuple[str | None, str | None]:
    """Loads the last recorded status and event ID from a file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                return data.get("last_status"), data.get("last_event_id")
        except json.JSONDecodeError:
            print(f"Error decoding {STATUS_FILE}. Starting fresh.")
    return None, None

def save_current_status(status: str, event_id: str | None):
    """Saves the current status and event ID to a file."""
    with open(STATUS_FILE, 'w') as f:
        json.dump({"last_status": status, "last_event_id": event_id}, f)

async def get_latest_nostr_event(public_key: str) -> Event | None:
    """Queries Nostr relays for the latest event from a specific public key with 'routstr-status' tag."""
    def _fetch_events_sync():
        try:
            # Create a new relay manager for fetching events
            relay_manager = RelayManager(timeout=2)
            for relay_url in MAIN_RELAYS + BACKUP_RELAYS:
                relay_manager.add_relay(relay_url)
            
            # Create filters to get events from the specific public key with routstr-status tag
            filters = FiltersList([Filters(
                kinds=[EventKind.TEXT_NOTE],
                limit=10
            )])
            
            subscription_id = uuid.uuid1().hex
            relay_manager.add_subscription_on_all_relays(subscription_id, filters)
            relay_manager.run_sync()
            
            # Check for notices
            while relay_manager.message_pool.has_notices():
                notice_msg = relay_manager.message_pool.get_notice()
                print(f"Notice: {notice_msg.content}")
            
            # Get the latest event
            latest_event = None
            while relay_manager.message_pool.has_events():
                event_msg = relay_manager.message_pool.get_event()
                if not latest_event or event_msg.event.created_at > latest_event.created_at:
                    latest_event = event_msg.event
            
            relay_manager.close_all_relay_connections()
            
            return latest_event
            
        except Exception as e:
            print(f"Error querying latest Nostr event: {e}")
            return None

    # Run the synchronous function in a thread to avoid blocking the event loop
    return await asyncio.to_thread(_fetch_events_sync)

async def publish_nostr_event(event_content: str, tags: list[list[str]] = None, relay_manager: RelayManager = None) -> str | None:
    """Publishes a Nostr event to configured relays."""
    if not NOSTR_BOT_NSEC:
        print("Error: NOSTR_BOT_NSEC environment variable not set.")
        return None

    def _publish_sync():
        try:
            private_key = PrivateKey.from_nsec(NOSTR_BOT_NSEC)
        except ValueError as e:
            print(f"Error: Invalid NOSTR_BOT_NSEC. Ensure it's a valid hex string or bech32 nsec. Details: {e}")
            return None

        # Create a fresh RelayManager like in tes.py
        relay_manager = RelayManager(timeout=6)
        for relay_url in MAIN_RELAYS + BACKUP_RELAYS:
            relay_manager.add_relay(relay_url)

        event = Event(
            content=event_content,
            tags=tags if tags else [],
            kind=1 # Default to Note event
        )
        event.sign(private_key.hex())

        try:
            relay_manager.publish_event(event)
            relay_manager.run_sync()
            import time
            time.sleep(5) # allow the messages to send
            
            while relay_manager.message_pool.has_ok_notices():
                ok_msg = relay_manager.message_pool.get_ok_notice()
                if("True" not in str(ok_msg)):
                    print(f"Relay not OK: {ok_msg}")
            
            return event.id
        except Exception as e:
            print(f"Error publishing event: {e}")
            return None

    # Run the synchronous function in a thread to avoid blocking the event loop
    return await asyncio.to_thread(_publish_sync)

# --- Main Logic ---

async def main():
    if not NOSTR_BOT_NSEC:
        print("NOSTR_BOT_NSEC not set, cannot query latest relay event.")
        return

    try:
        private_key = PrivateKey.from_nsec(NOSTR_BOT_NSEC)
        public_key = private_key.public_key.hex()
    except ValueError as e:
        print(f"Error: Invalid NOSTR_BOT_NSEC for deriving public key. Details: {e}")
        return

    # Fetch the latest event from relays instead of local file
    latest_event = await get_latest_nostr_event(public_key)
    
    current_status = "down" # Assume down by default
    ai_response_content = ""

    try:
        # Create AI prompt including the latest event content if available
        note_content = 'Error fetching event'
        if latest_event:
            note_content = latest_event.content
        base_prompt = f"Here's a nostr note someone made: '{note_content}'. Add a witty comment about how Bitcoin relates to it. Keep it short and concise, within 2 sentences. No hashtags. "

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ROUTSTR_API_KEY}",
            "Accept-Encoding": "identity"
        }
        response = requests.post(
            ROUTSTR_API_CHAT_URL,
            headers=headers,
            json={
                "model": "nousresearch/hermes-2-pro-llama-3-8b",
                # "model": "x-ai/grok-3-mini-beta",
                "messages": [{"role": "user", "content": base_prompt}]
            },
            timeout=10
        )
        
        if response.ok and response.status_code == 200:
            # API is working, extract AI response content
            current_status = "up"
            try:
                ai_data = response.json()
                if 'choices' in ai_data and ai_data['choices']:
                    ai_response_content = ai_data['choices'][0]['message']['content']
            except json.JSONDecodeError:
                ai_response_content = "AI response received but couldn't parse content."
        else:
            print(f"API returned non-OK status: {response.status_code}. Response text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Routstr API unreachable: {e}")
        current_status = "down"

    print(f"Routstr current status: {current_status}")

    # Generate event content (use AI response if available, otherwise fallback to generated comment)
    if ai_response_content:
        event_content = ai_response_content+"\n\n"+generate_comment(current_status)
    else:
        event_content = generate_comment(current_status)

    # Set up tags
    tags = []
    
    # If we have a previous event, quote it instead of replying to it
    if latest_event:
        tags.extend([
            ["q", latest_event.id, "wss://relay.damus.io", latest_event.pubkey],  # Quote tag with proper format
            # ["p", '4ad6fa2d16e2a9b576c863b4cf7404a70d4dc320c0c447d10ad6ff58993eacc8']  # Tag the original author
        ])

    new_event_id = await publish_nostr_event(event_content+"nostr:"+latest_event.bech32(), tags)

    if new_event_id:
        print(f"Published new status event: {new_event_id}")
        # Save status for reference (keeping this for backward compatibility)
        save_current_status(current_status, new_event_id)
    else:
        print("Failed to publish Nostr event.")

if __name__ == "__main__":
    asyncio.run(main())
