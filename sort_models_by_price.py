import json

def sort_models_by_price(input_file):
    """
    Reads a JSON file containing a list of models, sorts them by the sum of
    'prompt' and 'completion' pricing, and prints the first 20 sorted models.
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_file}'.")
        return

    models = data.get("models", [])

    def get_total_price(model):
        pricing = model.get("pricing", {})
        try:
            prompt_price = float(pricing.get("prompt", "0"))
            completion_price = float(pricing.get("completion", "0"))
            return prompt_price + completion_price
        except ValueError:
            return float('inf') # Handle cases where pricing values are not valid numbers

    # Sort the models list
    models.sort(key=get_total_price)

    print("Top 20 models sorted by prompt + completion pricing:")
    for i, model in enumerate(models[:20]):
        model_id = model.get("id", "N/A")
        pricing = model.get("pricing", {})
        try:
            prompt_price = float(pricing.get("prompt", "0"))
            completion_price = float(pricing.get("completion", "0"))
            total_price = prompt_price + completion_price
        except ValueError:
            total_price = "N/A"
        print(f"model id = {model_id}, total price = {total_price}")

if __name__ == "__main__":
    input_json_file = "models.json" # Assuming models.json is in the root directory
    sort_models_by_price(input_json_file)