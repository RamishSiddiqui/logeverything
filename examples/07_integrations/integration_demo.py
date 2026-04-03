"""
Integration Demo: Using LogEverything with multiple third-party libraries.

This example demonstrates how to configure and use LogEverything with various
third-party libraries like FastAPI, MLflow, Transformers, Pandas, and Requests
in a real-world machine learning application.

Example usage:
    python integration_demo.py

This will:
1. Set up LogEverything for all libraries
2. Create a FastAPI app with model serving endpoints
3. Load a Transformer model for inference
4. Track model metrics with MLflow
5. Process data with Pandas
6. Make HTTP requests to demonstrate logging

Requirements:
    - logeverything
    - fastapi
    - uvicorn
    - mlflow
    - transformers[torch]
    - pandas
    - numpy
    - requests
"""

import os
from typing import Optional

# Set up environment for cleaner demo output
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import LogEverything first to capture all logs
from logeverything import configure_external_logger, setup_logging

# Configure LogEverything's own logger
logger = setup_logging(level="INFO", use_color=True, align_values=True, show_timestamps=True)

# Configure external loggers
for logger_name in [
    "fastapi",
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "mlflow",
    "transformers",
    "pandas",
    "numpy",
    "requests",
    "urllib3",
]:
    # Configure each external logger
    configure_external_logger(
        logger_name,
        level="INFO",  # Set appropriate level for each library
        use_pretty_formatter=True,
        propagate=False,
    )

# Now import the libraries (ensures LogEverything captures everything)
import fastapi
import mlflow
import pandas as pd
import requests
import torch
import transformers
import uvicorn
from fastapi import BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Log that we've configured everything
logger.info(
    "LogEverything Integration Demo",
    libraries=["FastAPI", "MLflow", "Transformers", "Pandas", "NumPy", "Requests"],
)


# Create API input/output models
class TextInput(BaseModel):
    """Input model for text classification API."""

    text: str = Field(..., description="The text to classify")
    model_name: Optional[str] = Field(
        "distilbert-base-uncased", description="Model to use for classification"
    )


class PredictionOutput(BaseModel):
    """Output model for classification results."""

    text: str
    sentiment: str
    score: float
    processing_time_ms: float


# Create a FastAPI application
app = fastapi.FastAPI(
    title="LogEverything ML API Demo",
    description="API for text classification using HuggingFace Transformers with LogEverything logging",
    version="1.0.0",
)

# Global model and tokenizer cache
MODEL_CACHE = {}
TOKENIZER_CACHE = {}


# Load model function (would normally load a real model)
def load_model(model_name: str):
    """Load a model from HuggingFace or cache."""
    logger.info("Loading model", model=model_name)

    # Check cache first
    if model_name in MODEL_CACHE:
        logger.debug("Using cached model", model=model_name)
        return MODEL_CACHE[model_name], TOKENIZER_CACHE[model_name]

    try:
        # In a real app, this would load the actual model
        # For the demo, we'll simulate it
        logger.debug("Simulating model loading", model=model_name)

        # Mock tokenizer and model (in a real app, you'd use real models)
        tokenizer = transformers.AutoTokenizer.from_pretrained("distilbert-base-uncased")
        model = transformers.AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased"
        )

        # Cache for future use
        MODEL_CACHE[model_name] = model
        TOKENIZER_CACHE[model_name] = tokenizer

        # Log success with pretty formatting
        logger.success(
            "Model loaded successfully",
            model=model_name,
            parameters="10M+",
            device="CPU" if not torch.cuda.is_available() else "GPU",
        )

        return model, tokenizer
    except Exception as e:
        logger.error("Failed to load model", model=model_name, error=str(e))
        raise


# Background task to log metrics to MLflow
def log_prediction_to_mlflow(text: str, sentiment: str, score: float):
    """Log prediction metrics to MLflow in the background."""
    try:
        logger.debug("Logging prediction to MLflow", text_length=len(text), sentiment=sentiment)

        # Set up MLflow tracking
        mlflow.set_tracking_uri("file:./mlflow_tracking")

        with mlflow.start_run(run_name="sentiment_analysis"):
            # Log parameters and metrics
            mlflow.log_param("text_sample", text[:50] + "..." if len(text) > 50 else text)
            mlflow.log_param("model", "distilbert-base-uncased")
            mlflow.log_metric("confidence_score", score)

            # Create and log a pandas DataFrame with results
            results_df = pd.DataFrame({"text": [text], "sentiment": [sentiment], "score": [score]})

            # Log simple statistics
            summary = results_df.describe()
            mlflow.log_metrics(
                {
                    "avg_score": summary.loc["mean", "score"],
                    "min_score": summary.loc["min", "score"],
                    "max_score": summary.loc["max", "score"],
                }
            )

        logger.success("Successfully logged to MLflow")
    except Exception as e:
        logger.error("Failed to log to MLflow", error=str(e))


# FastAPI routes
@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    logger.info("API root endpoint accessed")
    return {
        "message": "LogEverything Integration Demo API",
        "docs_url": "/docs",
        "endpoints": ["/", "/health", "/predict"],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.debug("Health check performed")
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: TextInput, background_tasks: BackgroundTasks):
    """Predict sentiment from text."""
    import time

    start_time = time.time()

    logger.info("Processing prediction request", text_length=len(input_data.text))

    try:
        # Load model and tokenizer
        model, tokenizer = load_model(input_data.model_name)

        # In a real app, we'd actually use the model
        # For the demo, we'll simulate a sentiment prediction
        sentiment = "positive" if "good" in input_data.text.lower() else "negative"
        score = 0.95 if sentiment == "positive" else 0.85

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Schedule background task to log to MLflow
        background_tasks.add_task(log_prediction_to_mlflow, input_data.text, sentiment, score)

        # Return the result
        result = PredictionOutput(
            text=input_data.text,
            sentiment=sentiment,
            score=score,
            processing_time_ms=processing_time,
        )

        # Log success with hierarchical data
        logger.success(
            "Prediction successful",
            prediction={
                "sentiment": sentiment,
                "confidence": score,
                "time_ms": round(processing_time, 2),
            },
        )

        return result

    except Exception as e:
        logger.error("Prediction failed", error=str(e), text=input_data.text[:50])
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with enhanced logging."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        endpoint=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error. Check logs for details."}
    )


# Main entrypoint to run the app
def main():
    """Run the FastAPI application with Uvicorn."""
    logger.info("Starting server")

    # Make a test request using requests
    requests_logger = logging.getLogger("requests")
    requests_logger.info("Making test request to external API")

    try:
        response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
        if response.status_code == 200:
            requests_logger.info("External API request successful", status=response.status_code)

            # Process the data with pandas
            import pandas as pd

            df = pd.DataFrame([response.json()])
            logger.info("Data converted to DataFrame", shape=df.shape)
    except Exception as e:
        logger.error("Failed to make test request", error=str(e))

    # Start the server
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    # Add a banner to show it's working
    logger.info("=" * 60 + "\n" + "LogEverything Integration Demo".center(60) + "\n" + "=" * 60)

    # Start the main application
    main()
