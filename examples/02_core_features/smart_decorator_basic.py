import sys
import time
from pathlib import Path

import requests

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import Logger
from logeverything.decorators import log

logger = Logger()


def main():
    """Demonstrate the smart decorator functionality."""

    print("LogEverything Smart Decorator Example")
    print("=====================================")
    print("The @log decorator automatically detects what it's decorating:")

    # Example 1: Regular function
    @log
    def calculate_sum(a, b, c=0):
        """Calculate the sum of numbers."""
        time.sleep(0.1)  # Small delay to simulate work
        return a + b + c

    print("\n1. Using @log on a regular function:")
    result = calculate_sum(5, 7, 3)
    print(f"Result: {result}")

    # Example 2: I/O function (detected by name and operations)
    @log
    def read_file_content(filename):
        """Read content from a file."""
        time.sleep(0.1)  # Small delay to simulate work
        try:
            with open(filename, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error: {str(e)}"

    print("\n2. Using @log on an I/O function:")
    # Attempt to read a file (will likely fail, but that's ok for demonstration)
    content = read_file_content("example_file.txt")
    print(f"File content length: {len(content) if not content.startswith('Error') else 'N/A'}")

    # Example 3: Class with methods
    @log
    class DataProcessor:
        """A class for processing data."""

        def __init__(self, multiplier=2):
            """Initialize with a multiplier."""
            self.multiplier = multiplier
            self.processed_count = 0

        def process(self, items):
            """Process a list of items by multiplying them."""
            time.sleep(0.1)  # Small delay to simulate work
            result = [item * self.multiplier for item in items]
            self.processed_count += len(items)
            return result

        def fetch_remote_data(self, url):
            """Fetch data from a remote URL."""
            try:
                # This method will be detected as I/O
                # Note: We don't actually make the request to avoid external dependencies
                print(f"Would fetch data from: {url}")
                return {"status": "success", "items": [1, 2, 3]}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    print("\n3. Using @log on a class:")
    processor = DataProcessor(multiplier=3)
    processed_data = processor.process([1, 2, 3, 4, 5])
    print(f"Processed data: {processed_data}")

    # The fetch_remote_data method will be detected as I/O
    remote_data = processor.fetch_remote_data("https://example.com/api/data")
    print(f"Remote data status: {remote_data['status']}")


if __name__ == "__main__":
    main()
