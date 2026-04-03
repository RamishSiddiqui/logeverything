"""
Mock implementations of third-party libraries for testing purposes.

This module provides mock versions of popular libraries like langchain, fastapi, mlflow, etc.
that are sufficient for testing LogEverything's external logger integration capabilities
without requiring the actual libraries to be installed.

Usage:
    # Import the mock library functions
    from tests.mock_libraries import install_mocks, remove_mocks

    # Install mock libraries (only those not already available)
    installed_mocks = install_mocks()

    # Now you can import and use mock versions of these libraries
    import langchain
    import fastapi
    import mlflow

    # When done, you can remove the mocks if needed
    remove_mocks(installed_mocks)
"""

import logging
import sys
from unittest.mock import MagicMock


class MockModule:
    """Base class for mock modules."""

    def __init__(self, name):
        self.name = name
        # Create a logger with the library name
        self.logger = logging.getLogger(name)


class MockLangChain(MockModule):
    """Mock implementation of the LangChain library."""

    def __init__(self):
        super().__init__("langchain")

        # Create mock schema module
        self.schema = MagicMock()
        self.schema.Document = type(
            "Document",
            (),
            {"__init__": lambda self, **kwargs: None, "page_content": "", "metadata": {}},
        )

        # Create mock prompts module
        self.prompts = MagicMock()

        # Create a PromptTemplate class
        class PromptTemplate:
            def __init__(self, input_variables=None, template=None):
                self.input_variables = input_variables or []
                self.template = template or ""
                # Log something when created
                logging.getLogger("langchain").debug(
                    f"Created PromptTemplate with {len(input_variables)} variables"
                )

            def format(self, **kwargs):
                # Log when format is called
                logging.getLogger("langchain").info(
                    f"Formatting template with {len(kwargs)} variables"
                )
                # Simple template formatting
                result = self.template
                for key, value in kwargs.items():
                    if key in self.input_variables:
                        result = result.replace(f"{{{key}}}", str(value))
                return result

        self.prompts.PromptTemplate = PromptTemplate


class MockFastAPI(MockModule):
    """Mock implementation of the FastAPI library."""

    def __init__(self):
        super().__init__("fastapi")

        # Create basic FastAPI class
        class FastAPI:
            def __init__(self, **kwargs):
                # Log something when created
                logging.getLogger("fastapi").info("FastAPI app created")
                self.routes = []

            def get(self, path):
                # Log when a route is registered
                logging.getLogger("fastapi").debug(f"Route registered: GET {path}")

                def decorator(func):
                    self.routes.append((path, func))
                    return func

                return decorator

        self.FastAPI = FastAPI


class MockUvicorn(MockModule):
    """Mock implementation of the Uvicorn library."""

    def __init__(self):
        super().__init__("uvicorn")
        # Create access logger
        self.access_logger = logging.getLogger("uvicorn.access")

        def run(app, **kwargs):
            # Log something when run is called
            logging.getLogger("uvicorn").info(f"Starting server with {len(kwargs)} config options")
            logging.getLogger("uvicorn.access").info(
                f"Server listening on {kwargs.get('host', '127.0.0.1')}:{kwargs.get('port', 8000)}"
            )

        self.run = run


class MockMLflow(MockModule):
    """Mock implementation of the MLflow library."""

    def __init__(self):
        super().__init__("mlflow")

        def log_metric(key, value):
            # Log when a metric is logged
            logging.getLogger("mlflow").info(f"Logging metric {key}={value}")

        def log_param(key, value):
            # Log when a parameter is logged
            logging.getLogger("mlflow").debug(f"Logging parameter {key}={value}")

        def start_run(run_name=None):
            # Log when a run is started
            logging.getLogger("mlflow").info(f"Starting run: {run_name}")
            return MagicMock()

        def set_tracking_uri(uri):
            # Log when tracking URI is set
            logging.getLogger("mlflow").debug(f"Setting tracking URI: {uri}")

        self.log_metric = log_metric
        self.log_param = log_param
        self.start_run = start_run
        self.set_tracking_uri = set_tracking_uri

        # Mock sklearn integration
        sklearn_mock = MagicMock()
        sklearn_mock.log_model = MagicMock()
        self.sklearn = sklearn_mock


class MockRequests(MockModule):
    """Mock implementation of the Requests library."""

    def __init__(self):
        super().__init__("requests")

        class Response:
            def __init__(self, status_code=200, content=b"", text=""):
                self.status_code = status_code
                self.content = content
                self.text = text
                self._json = {}

            def json(self):
                logging.getLogger("requests").debug("Parsing JSON response")
                return self._json

        def get(url, **kwargs):
            # Log when get is called
            logging.getLogger("requests").info(f"GET request to {url}")
            return Response()

        def post(url, **kwargs):
            # Log when post is called
            logging.getLogger("requests").info(f"POST request to {url}")
            if "json" in kwargs:
                logging.getLogger("requests").debug("With JSON payload")
            return Response()

        self.get = get
        self.post = post
        self.Response = Response


class MockTransformers(MockModule):
    """Mock implementation of the Transformers library."""

    def __init__(self):
        super().__init__("transformers")

        # Create logging module similar to the real one
        class TransformersLogging:
            def __init__(self):
                self.CRITICAL = 50
                self.ERROR = 40
                self.WARNING = 30
                self.INFO = 20
                self.DEBUG = 10
                self.NOTSET = 0

            def get_verbosity(self):
                return logging.getLogger("transformers").level

            def set_verbosity_info(self):
                logging.getLogger("transformers").setLevel(logging.INFO)

            def set_verbosity_warning(self):
                logging.getLogger("transformers").setLevel(logging.WARNING)

            def set_verbosity_debug(self):
                logging.getLogger("transformers").setLevel(logging.DEBUG)

            def set_verbosity_error(self):
                logging.getLogger("transformers").setLevel(logging.ERROR)

            def get_logger(self):
                return logging.getLogger("transformers")

        self.logging = TransformersLogging()

        # Create AutoTokenizer class
        class AutoTokenizer:
            @staticmethod
            def from_pretrained(pretrained_model_name_or_path, *args, **kwargs):
                # Log tokenizer loading
                logging.getLogger("transformers").info(
                    f"Loading tokenizer: {pretrained_model_name_or_path}"
                )

                # Create a simple tokenizer
                class MockTokenizer:
                    def __init__(self):
                        self.name = pretrained_model_name_or_path

                    def encode(self, text, *args, **kwargs):
                        logging.getLogger("transformers").debug(f"Encoding text: {text[:20]}...")
                        # Return a simple token list
                        return [101, 102, 103]

                    def decode(self, token_ids, *args, **kwargs):
                        logging.getLogger("transformers").debug(f"Decoding tokens: {token_ids}")
                        return "Decoded text"

                return MockTokenizer()

        self.AutoTokenizer = AutoTokenizer

        # Create AutoModel class
        class AutoModel:
            @staticmethod
            def from_pretrained(pretrained_model_name_or_path, *args, **kwargs):
                # Log model loading
                logging.getLogger("transformers").info(
                    f"Loading model: {pretrained_model_name_or_path}"
                )

                # Create a simple model
                class MockModel:
                    def __init__(self):
                        self.name = pretrained_model_name_or_path
                        self.config = type("MockConfig", (), {"hidden_size": 768})

                    def eval(self):
                        logging.getLogger("transformers").debug("Setting model to eval mode")
                        return self

                    def __call__(self, *args, **kwargs):
                        logging.getLogger("transformers").debug("Model forward pass")
                        # Return a simple output dict with expected structure
                        import torch

                        return {"last_hidden_state": torch.zeros(1, 1, 768)}

                return MockModel()

        self.AutoModel = AutoModel


class MockPandas(MockModule):
    """Mock implementation of the Pandas library."""

    def __init__(self):
        super().__init__("pandas")

        # Create a minimal DataFrame class
        class DataFrame:
            def __init__(self, data=None, index=None, columns=None, **kwargs):
                # Log DataFrame creation
                logging.getLogger("pandas").debug(
                    f"Creating DataFrame with {len(data) if data else 0} rows"
                )
                self.data = data or {}
                self.index = index or []
                self.columns = columns or list(self.data.keys())
                self._shape = (len(self.index) if self.index else 0, len(self.columns))

            @property
            def shape(self):
                return self._shape

            def head(self, n=5):
                logging.getLogger("pandas").debug(f"Getting first {n} rows of DataFrame")
                # Return a new DataFrame with first n rows
                return self

            def describe(self):
                logging.getLogger("pandas").info("Generating DataFrame statistics")
                # Return a new DataFrame with statistics
                return DataFrame()

            def to_csv(self, path_or_buf=None, **kwargs):
                logging.getLogger("pandas").info(f"Saving DataFrame to CSV: {path_or_buf}")
                return None

            def to_dict(self, **kwargs):
                logging.getLogger("pandas").debug("Converting DataFrame to dictionary")
                return self.data

        self.DataFrame = DataFrame

        # Mock read functions
        def read_csv(filepath_or_buffer, **kwargs):
            logging.getLogger("pandas").info(f"Reading CSV file: {filepath_or_buffer}")
            return DataFrame()

        def read_json(path_or_buf, **kwargs):
            logging.getLogger("pandas").info(f"Reading JSON file: {path_or_buf}")
            return DataFrame()

        self.read_csv = read_csv
        self.read_json = read_json


class MockNumpy(MockModule):
    """Mock implementation of the NumPy library."""

    def __init__(self):
        super().__init__("numpy")

        # Mock array creation functions
        def array(object, dtype=None, *args, **kwargs):
            # Log array creation
            logging.getLogger("numpy").debug("Creating numpy array")
            return object

        def zeros(shape, dtype=None, *args, **kwargs):
            # Log zeros creation
            logging.getLogger("numpy").debug(f"Creating zeros array with shape {shape}")
            return [0] * (shape if isinstance(shape, int) else shape[0])

        def ones(shape, dtype=None, *args, **kwargs):
            # Log ones creation
            logging.getLogger("numpy").debug(f"Creating ones array with shape {shape}")
            return [1] * (shape if isinstance(shape, int) else shape[0])

        # Basic operations
        def mean(a, *args, **kwargs):
            logging.getLogger("numpy").debug("Calculating mean")
            return 0.0

        def sum(a, *args, **kwargs):
            logging.getLogger("numpy").debug("Calculating sum")
            return 0.0

        self.array = array
        self.zeros = zeros
        self.ones = ones
        self.mean = mean
        self.sum = sum

        # Constants
        self.pi = 3.141592653589793

        # Mock ndarray class for PyTorch compatibility
        class ndarray:
            """Mock ndarray class."""

            def __init__(self, data=None):
                self.data = data or []

            def __len__(self):
                return len(self.data) if hasattr(self.data, "__len__") else 0

            def __getitem__(self, key):
                return self.data[key] if hasattr(self.data, "__getitem__") else None

            def shape(self):
                return (len(self.data),) if hasattr(self.data, "__len__") else ()

            def dtype(self):
                return "float64"

        self.ndarray = ndarray

        # Mock numpy scalar types that PyTorch expects
        self.bool_ = bool
        self.number = (int, float, complex)
        self.object_ = object

        # Mock dtype for ndarray compatibility
        class dtype:
            def __init__(self, type_str="float64"):
                self.str = type_str

        self.dtype = dtype


def install_mocks():
    """Install mock libraries in sys.modules."""
    # Check if requested libraries are already imported
    mocks = {
        "langchain": MockLangChain(),
        "fastapi": MockFastAPI(),
        "uvicorn": MockUvicorn(),
        "mlflow": MockMLflow(),
        "requests": MockRequests(),
        "transformers": MockTransformers(),
        "pandas": MockPandas(),
        "numpy": MockNumpy(),
    }

    # Install mocks for missing libraries
    installed_mocks = []

    for name, mock in mocks.items():
        if name not in sys.modules:
            sys.modules[name] = mock
            installed_mocks.append(name)
            # Also create schema module for langchain
            if name == "langchain":
                sys.modules["langchain.schema"] = mock.schema
                sys.modules["langchain.prompts"] = mock.prompts

    return installed_mocks


def remove_mocks(mock_names=None):
    """Remove mock libraries from sys.modules."""
    if mock_names is None:
        mock_names = [
            "langchain",
            "fastapi",
            "uvicorn",
            "mlflow",
            "requests",
            "transformers",
            "pandas",
            "numpy",
        ]

    for name in mock_names:
        if name in sys.modules:
            del sys.modules[name]

        # Also remove submodules
        if name == "langchain":
            for submodule in list(sys.modules.keys()):
                if submodule.startswith("langchain."):
                    del sys.modules[submodule]
