# Routstr Scripts

This repository contains various Python scripts used by Routstr for different functionalities.

## Available Scripts

### `fetch_and_filter_models.py`
This script is responsible for fetching AI models from the OpenRouter API. It then filters these models based on their pricing, ensuring that only models with valid prompt and completion costs are included. This helps users to get a curated list of usable models.

### `routstr_bot.py`
This script powers the Routstr Nostr bot. It interacts with the Nostr network to fetch the latest events and provide witty comments related to Bitcoin. It also checks the status of the Routstr API and includes this status in its Nostr posts, keeping users informed about the service's availability.