"""
Example demonstrating LogEverything integration with a data science pipeline.

This example shows how to use LogEverything to track data processing steps,
model training, and evaluation metrics in a data science workflow.
"""

import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
import time
from typing import Any, Dict, List, Tuple

import logeverything as le


class DataLoader:
    """Example data loader class for loading and preprocessing data."""

    @le.log
    def __init__(self, data_path: str, validation_split: float = 0.2):
        self.data_path = data_path
        self.validation_split = validation_split
        self.logger = le.get_logger("pipeline.data")
        self.logger.info(f"Initialized DataLoader with path: {data_path}")

    @le.log
    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Load data from the specified path."""
        self.logger.info(f"Loading data from {self.data_path}")

        # Simulate loading data
        time.sleep(0.5)
        # In a real application, you would load actual data here
        data = [
            {
                "id": i,
                "features": [random.random() for _ in range(5)],
                "label": random.choice([0, 1]),
            }
            for i in range(100)
        ]

        self.logger.info(f"Loaded {len(data)} records")
        return data

    @le.log
    def preprocess(self, data: List[Dict]) -> Tuple[List[List[float]], List[int]]:
        """Preprocess the loaded data."""
        self.logger.info(f"Preprocessing {len(data)} records")

        # Extract features and labels
        features = [item["features"] for item in data]
        labels = [item["label"] for item in data]

        # Log data statistics
        self.logger.debug(f"Features shape: {len(features)}x{len(features[0])}")
        self.logger.debug(f"Class distribution: 0s={labels.count(0)}, 1s={labels.count(1)}")

        return features, labels

    @le.log
    def split_data(
        self, features: List[List[float]], labels: List[int]
    ) -> Tuple[List[List[float]], List[int], List[List[float]], List[int]]:
        """Split data into training and validation sets."""
        self.logger.info(f"Splitting data with validation ratio {self.validation_split}")

        # Calculate split index
        split_idx = int(len(features) * (1 - self.validation_split))

        # Split the data
        train_features = features[:split_idx]
        train_labels = labels[:split_idx]
        val_features = features[split_idx:]
        val_labels = labels[split_idx:]

        self.logger.info(f"Training set: {len(train_features)} samples")
        self.logger.info(f"Validation set: {len(val_features)} samples")

        return train_features, train_labels, val_features, val_labels


class Model:
    """Example model class for training and evaluation."""

    @le.log
    def __init__(self, name: str):
        self.name = name
        self.trained = False
        self.logger = le.get_logger("pipeline.model")
        self.logger.info(f"Initialized model: {name}")

    @le.log
    def train(
        self, features: List[List[float]], labels: List[int], epochs: int = 5
    ) -> Dict[str, List[float]]:
        """Train the model on the provided data."""
        self.logger.info(f"Training model {self.name} for {epochs} epochs")

        # Track metrics across epochs
        history = {"loss": [], "accuracy": []}

        # Simulate training loop
        for epoch in range(epochs):
            # Simulate epoch training
            time.sleep(0.2)

            # Generate fake metrics
            loss = 1.0 / (epoch + 1)
            accuracy = 0.5 + epoch * 0.1

            # Record metrics
            history["loss"].append(loss)
            history["accuracy"].append(accuracy)

            self.logger.info(
                f"Epoch {epoch + 1}/{epochs}: loss={loss:.4f}, accuracy={accuracy:.4f}"
            )

        self.trained = True
        self.logger.info(f"Model {self.name} training completed")
        return history

    @le.log
    def evaluate(self, features: List[List[float]], labels: List[int]) -> Dict[str, float]:
        """Evaluate the model on validation data."""
        if not self.trained:
            self.logger.warning("Attempting to evaluate untrained model")

        self.logger.info(f"Evaluating model {self.name} on {len(features)} samples")

        # Simulate evaluation
        time.sleep(0.3)

        # Generate fake metrics
        metrics = {
            "loss": random.uniform(0.1, 0.5),
            "accuracy": random.uniform(0.7, 0.95),
            "precision": random.uniform(0.7, 0.9),
            "recall": random.uniform(0.7, 0.9),
        }

        # Log metrics
        for name, value in metrics.items():
            self.logger.info(f"Evaluation {name}: {value:.4f}")

        return metrics

    @le.log
    def save(self, path: str) -> bool:
        """Save the trained model."""
        if not self.trained:
            self.logger.error("Cannot save untrained model")
            return False

        self.logger.info(f"Saving model {self.name} to {path}")

        # Simulate saving
        time.sleep(0.2)

        self.logger.info("Model saved successfully")
        return True


class Pipeline:
    """Main data science pipeline that coordinates the workflow."""

    @le.log
    def __init__(self, data_path: str, model_name: str, output_path: str):
        self.data_path = data_path
        self.model_name = model_name
        self.output_path = output_path
        self.logger = le.get_logger("pipeline")

        # Create component objects
        self.data_loader = DataLoader(data_path)
        self.model = Model(model_name)

        self.logger.info(f"Pipeline initialized with model {model_name}")

    @le.log
    def run(self, epochs: int = 5) -> Dict[str, Any]:
        """Execute the full pipeline."""
        self.logger.info("Starting pipeline execution")
        pipeline_start_time = time.time()

        # Load and preprocess data
        raw_data = self.data_loader.load_data()
        features, labels = self.data_loader.preprocess(raw_data)
        train_features, train_labels, val_features, val_labels = self.data_loader.split_data(
            features, labels
        )

        # Train model
        training_history = self.model.train(train_features, train_labels, epochs=epochs)

        # Evaluate model
        eval_metrics = self.model.evaluate(val_features, val_labels)

        # Save model
        save_success = self.model.save(self.output_path)

        # Log summary
        pipeline_time = time.time() - pipeline_start_time
        self.logger.info(f"Pipeline completed in {pipeline_time:.2f} seconds")
        self.logger.info(f"Final accuracy: {eval_metrics['accuracy']:.4f}")

        # Return results
        return {
            "metrics": eval_metrics,
            "history": training_history,
            "execution_time": pipeline_time,
            "success": save_success,
        }


def main():
    """Run the data science pipeline example."""
    # Set up logging with a profile suitable for data science
    logger = le.setup_logging(
        profile="development",  # Detailed logging with visual enhancements
        visual_mode=True,  # Enable visual enhancements
        use_symbols=True,  # Use symbols for log levels
        use_indent=True,  # Use indentation for hierarchical logs
        file_path="data_pipeline.log",  # Also save logs to a file
    )

    logger.info("Starting data science pipeline example")

    # Initialize and run the pipeline
    pipeline = Pipeline(
        data_path="./data/sample.csv",  # This is a mock path
        model_name="RandomForestModel",
        output_path="./models/rf_model.pkl",  # This is a mock path
    )

    # Execute the pipeline
    results = pipeline.run(epochs=3)

    # Log the results summary
    logger.info(f"Pipeline results: accuracy={results['metrics']['accuracy']:.4f}")
    logger.info("Data science pipeline example completed")


if __name__ == "__main__":
    main()
