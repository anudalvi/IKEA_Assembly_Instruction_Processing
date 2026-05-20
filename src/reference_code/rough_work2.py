
"""
Dynamic Config-Based Dictionary Value Resolver

Config file format:
    source_dict:<dict_name>, key_value:<key_name>

This reads the config and dynamically fetches dict_name[key_name] at runtime.
"""
'''
import json


# ── Sample config file (config.txt) ─────────────────────────────────────────
CONFIG_CONTENT = """\
source_dict:pdf_file_detail, key_value:pdf_type
source_dict:pdf_file_detail, key_value:pdf_version
source_dict:user_info,       key_value:username
source_dict:user_info,       key_value:email
"""

# ── Sample data sources (the actual dicts your config points to) ─────────────
pdf_file_detail = {
    "pdf_type": "invoice",
    "pdf_version": "1.7",
    "page_count": 5,
}

user_info = {
    "username": "john_doe",
    "email": "john@example.com",
    "role": "admin",
}


# ── Parser ───────────────────────────────────────────────────────────────────
def parse_config(config_text: str) -> list[dict]:
    """
    Parses each config line into structured entries.

    Input line:  "source_dict:pdf_file_detail, key_value:pdf_type"
    Output:      {"source_dict": "pdf_file_detail", "key_value": "pdf_type"}
    """
    entries = []
    for line in config_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        entry = {}
        for part in line.split(","):
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                entry[k.strip()] = v.strip()

        if "source_dict" in entry and "key_value" in entry:
            entries.append(entry)

    return entries


# ── Resolver ─────────────────────────────────────────────────────────────────
def resolve_value(entry: dict, context: dict) -> tuple:
    """
    Dynamically resolves dict_name[key] using the provided context namespace.

    Args:
        entry:   Parsed config entry {"source_dict": "...", "key_value": "..."}
        context: A dict mapping dict names → actual dict objects

    Returns:
        (dict_name, key, resolved_value)  — or raises KeyError if not found
    """
    dict_name = entry["source_dict"]
    key       = entry["key_value"]

    if dict_name not in context:
        raise KeyError(f"Source dict '{dict_name}' not found in context.")
    if key not in context[dict_name]:
        raise KeyError(f"Key '{key}' not found in '{dict_name}'.")

    return dict_name, key, context[dict_name][key]


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # 1. All available data sources — add new dicts here as needed
    context = {
        "pdf_file_detail": pdf_file_detail,
        "user_info":       user_info,
    }

    # 2. Parse config (swap CONFIG_CONTENT with open("config.txt").read() for real files)
    entries = parse_config(CONFIG_CONTENT)

    # 3. Resolve each entry dynamically
    print(f"{'SOURCE DICT':<20} {'KEY':<15} {'VALUE'}")
    print("-" * 50)
    for entry in entries:
        try:
            dict_name, key, value = resolve_value(entry, context)
            print(f"{dict_name:<20} {key:<15} {value}")
        except KeyError as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    main()'''

import json

# --- The Strategy Layer ---
# This class acts as a container for all available transformation 'strategies'
class TransformationLibrary:
    @staticmethod
    def split_by_comma(value, args, kwargs):
        """Splits a string and returns a specific index."""
        # args[0] is the separator, kwargs['index'] is the part to return
        return value.split(args[0])[kwargs.get("index", 0)]

    @staticmethod
    def to_uppercase(value, args, kwargs):
        """Simple strategy to demonstrate interchangeability."""
        return value.upper()

# --- The Command / Processor Layer ---
class DataTransformer:
    def __init__(self, context):
        # The context holds our raw data (the 'Receiver' in Command Pattern)
        self.context = context
        # Dispatch Table: Maps string names to actual function references
        self._registry = {
            "split_by_comma": TransformationLibrary.split_by_comma,
            "to_uppercase": TransformationLibrary.to_uppercase
        }

    def execute_config(self, config):
        """
        The 'Invoker' logic: Parses the config command and executes it.
        """
        # 1. Extract source data using the keys provided in the config
        source_name = config["source_dict"]
        source_key = config["key_value"]
        
        # Retrieve the actual value from the context
        # e.g., context['pdf_file_detail']['product_name']
        raw_value = self.context[source_name][source_key]

        # 2. Identify the transformation 'Strategy'
        func_name = config["transform_function"]
        transform_func = self._registry.get(func_name)

        if not transform_func:
            raise ValueError(f"Transformation '{func_name}' not found in registry.")

        # 3. Execute the transformation (Dynamic Dispatch)
        transformed_value = transform_func(
            raw_value, 
            config.get("transform_function_args", []), 
            config.get("transform_function_kwargs", {})
        )

        return transformed_value

# --- Main Execution ---
def main():
    # Configuration defined as data (Command Pattern)
    config_string = {
        "source_dict": "pdf_file_detail",
        "key_value": "product_name",
        "destination_key": "product_name",
        "destination_dict": "product_details_node",
        "transform_function": "split_by_comma",
        "transform_function_args": [","],
        "transform_function_kwargs": {"index": 0}
    }

    # The data environment (The Receiver)
    context = {
        "pdf_file_detail": {
            "product_name": "IKEA, Billy, Bookcase"
        }
    }

    # Initialize the Processor
    transformer = DataTransformer(context)

    # Run the dynamic command
    try:
        result = transformer.execute_config(config_string)
        print(f"Final Result: {result}") 
    except Exception as e:
        print(f"Error processing command: {e}")

if __name__ == "__main__":
    main()
