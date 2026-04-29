"""
Mock implementations for HuggingFace Hub components to avoid SSL certificate issues.
"""

import logging
import os

# Configure HuggingFace to bypass SSL verification
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"  # Force offline mode
os.environ["TRANSFORMERS_OFFLINE"] = "1"  # Force offline mode


def patch_huggingface_hub():
    """Patch the huggingface_hub modules to avoid SSL verification issues."""
    try:
        import sys

        import huggingface_hub
        import huggingface_hub.file_download
        import huggingface_hub.utils

        # Create mock for file_download.hf_hub_download

        def mock_hf_hub_download(repo_id, filename, **kwargs):
            """Mock version that logs but doesn't actually download."""
            logger = logging.getLogger("huggingface_hub")
            logger.info(f"Mock download from {repo_id}: {filename}")
            # Return a mock file path
            return os.path.join(os.path.dirname(__file__), "mock_tokenizer.json")

        # Replace the function
        huggingface_hub.file_download.hf_hub_download = mock_hf_hub_download

        # Create a mock file that can be used by tests
        with open(os.path.join(os.path.dirname(__file__), "mock_tokenizer.json"), "w") as f:
            f.write('{"model_max_length": 512, "do_lower_case": true}')

        print("Successfully patched huggingface_hub to avoid SSL verification issues")
        return True
    except (ImportError, Exception) as e:
        print(f"Failed to patch huggingface_hub: {e}")
        return False
