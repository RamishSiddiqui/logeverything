"""
Run integration tests for the LogEverything library.

This script runs the integration tests for the LogEverything library, testing
the integration with popular third-party libraries like langchain, fastapi, mlflow,
transformers, pandas, numpy, and requests.
"""

import os
import sys
import unittest

# Add the parent directory to the path to make imports work when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    # Display test banner
    print("\n" + "=" * 80)
    print("LogEverything Integration Tests".center(80))
    print("Testing integration with third-party libraries".center(80))
    print("=" * 80)

    # Import mock libraries module
    from tests.mock_libraries import install_mocks, remove_mocks

    # Install mock libraries if the real ones aren't available
    installed_mocks = install_mocks()

    if installed_mocks:
        print(f"\nInstalled mock libraries for: {', '.join(installed_mocks)}")

    try:
        # Run all integration test modules
        loader = unittest.TestLoader()
        start_dir = os.path.join(os.path.dirname(__file__), "tests")

        # Run specific integration test files
        integration_tests = [
            "test_library_integrations.py",
            "test_additional_integrations.py",
            "test_fastapi_integration.py",
            "test_mlflow_integration.py",
        ]

        suite = unittest.TestSuite()

        # Add each test module to the suite
        for test_file in integration_tests:
            test_path = os.path.join(os.path.dirname(__file__), test_file)
            if os.path.exists(test_path):
                file_suite = unittest.defaultTestLoader.discover(
                    os.path.dirname(__file__), pattern=os.path.basename(test_path)
                )
                suite.addTest(file_suite)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print test summary
        print("\n" + "=" * 80)
        print(f"Tests Run: {result.testsRun}")
        print(f"Errors: {len(result.errors)}")
        print(f"Failures: {len(result.failures)}")
        print(f"Skipped: {len(result.skipped)}")
        print("=" * 80)

        # Exit with appropriate code
        if result.wasSuccessful():
            print("\nAll integration tests passed successfully!")
            sys.exit(0)
        else:
            print("\nSome integration tests failed. See details above.")
            sys.exit(1)

    finally:
        # Remove mock libraries
        if installed_mocks:
            remove_mocks(installed_mocks)
            print(f"\nRemoved mock libraries: {', '.join(installed_mocks)}")
