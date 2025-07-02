import requests
import json
from datetime import datetime

def fetch_and_filter_models(output_file="models.json", example_output_path="/home/user42/projects/routstr_main/proxy/models.example.json"):
    """
    Fetches models from OpenRouter API, filters them based on pricing, and writes
    the output to a JSON file.
    """
    url = "https://openrouter.ai/api/v1/models"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        models_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        # Fallback to example output if API call fails
        try:
            with open(example_output_path, 'r') as f:
                models_data = json.load(f)
            print(f"Using example output from {example_output_path} due to API error.")
        except FileNotFoundError:
            print(f"Error: Example output file not found at {example_output_path}")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from example output file at {example_output_path}")
            return

    filtered_models = []
    for model in models_data.get("data", []):
        prompt_cost = float(model.get("pricing", {}).get("prompt", 0))
        completion_cost = float(model.get("pricing", {}).get("completion", 0))

        # Filter out models where prompt or completion pricing is 0 or -1
        if prompt_cost > 0 and completion_cost > 0:
            filtered_models.append(model)
        else:
            print(f"Filtering out model '{model.get('id', 'N/A')}' due to pricing: prompt={prompt_cost}, completion={completion_cost}")


    # Reconstruct the output with filtered models under the "data" key
    output_data = {"models": filtered_models}

    # Update metadata with timestamp
    try:
        with open("script_metadata.json", 'r+') as f:
            metadata = json.load(f)
            metadata["last_run_timestamp"] = datetime.now().isoformat()
            f.seek(0)
            json.dump(metadata, f, indent=4)
            f.truncate()
        print(f"Updated script metadata with timestamp.")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"script_metadata.json not found or invalid, creating/overwriting it.")
        with open("script_metadata.json", 'w') as f:
            json.dump({"last_run_timestamp": datetime.now().isoformat()}, f, indent=4)


    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"Filtered models successfully written to {output_file}")
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")

if __name__ == "__main__":
    fetch_and_filter_models()