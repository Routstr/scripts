# Routstr Scripts

This repository contains various Python scripts used by Routstr for different functionalities. Each script has specific setup and usage instructions detailed below.

## Available Scripts

### `fetch_and_filter_models.py`

This script is responsible for fetching AI models from the OpenRouter API. It then filters these models based on their pricing, ensuring that only models with valid prompt and completion costs are included. This helps users to get a curated list of usable models, which is then saved to a JSON file.

#### Setup

1.  **Install dependencies:**
    ```bash
    pip install requests
    ```

#### Usage

To run the script and fetch/filter models, simply execute:

```bash
python fetch_and_filter_models.py
```

The script will create a `models.json` file in the same directory containing the filtered model data. By default, it uses `https://openrouter.ai/api/v1/models` as the source.

### `routstr_bot.py`

This script powers the Routstr Nostr bot. It interacts with the Nostr network to fetch the latest events and provides witty comments related to Bitcoin. It also checks the status of the Routstr API and includes this status in its Nostr posts, keeping users informed about the service's availability.

#### Setup

1.  **Install dependencies:**
    ```bash
    pip install pynostr python-dotenv requests
    ```

2.  **Create a `.env` file:**
    This script requires sensitive information to be stored as environment variables. Create a file named `.env` in the same directory as `routstr_bot.py` with the following content:

    ```
    ROUTSTR_API_URL="YOUR_ROUTSTR_API_BASE_URL" # e.g., https://api.routstr.io
    NOSTR_BOT_NSEC="YOUR_NOSTR_BOT_NSEC_PRIVATE_KEY" # Your bot's Nostr private key (nsec format)
    ROUTSTR_API_KEY="YOUR_ROUTSTR_API_KEY" # Your API key for Routstr
    ```

    **Important:** Keep your `NOSTR_BOT_NSEC` and `ROUTSTR_API_KEY` secure and do not share them publicly.

#### Usage

To start the Routstr Nostr bot, run the script:

```bash
python routstr_bot.py
```

The bot will connect to the configured Nostr relays and begin its operations.