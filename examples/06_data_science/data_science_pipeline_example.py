#!/usr/bin/env python3
"""
Data Science Pipeline Logging Example

This example demonstrates how to use LogEverything in data science workflows,
including data loading, preprocessing, model training, evaluation, and
experiment tracking.
"""

import random
import sys
import time
from pathlib import Path

import numpy as np

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger, configure
from logeverything.contexts import log_context, performance_context
from logeverything.decorators import log


# Simulate data science libraries
class MockDataFrame:
    """Mock pandas DataFrame for demonstration."""

    def __init__(self, data, columns=None):
        self.data = data
        self.columns = columns or [f"feature_{i}" for i in range(len(data[0]))]
        self.shape = (len(data), len(data[0]) if data else 0)

    def head(self, n=5):
        return MockDataFrame(self.data[:n], self.columns)

    def describe(self):
        return {"count": len(self.data), "features": len(self.columns)}

    def dropna(self):
        # Simulate dropping NaN values
        return MockDataFrame([row for row in self.data if None not in row], self.columns)


class MockModel:
    """Mock machine learning model for demonstration."""

    def __init__(self, model_type="RandomForest"):
        self.model_type = model_type
        self.is_fitted = False
        self.feature_importance = None

    def fit(self, X, y):
        # Simulate model training
        time.sleep(0.2)
        self.is_fitted = True
        self.feature_importance = [random.random() for _ in range(len(X.columns))]
        return self

    def predict(self, X):
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        return [random.random() for _ in range(len(X.data))]

    def score(self, X, y):
        predictions = self.predict(X)
        return random.uniform(0.7, 0.95)


class DataProcessor:
    """Data processing pipeline with comprehensive logging."""

    def __init__(self):
        self.logger = Logger("data_processing")

    @log
    def load_data(self, source: str) -> MockDataFrame:
        """Load data from various sources."""
        with performance_context("Data loading", logger=self.logger):
            self.logger.info(f"Loading data from {source}")

            # Simulate different data sources
            if "csv" in source.lower():
                # Simulate CSV loading
                time.sleep(0.1)
                data = [[random.random() for _ in range(10)] for _ in range(1000)]
                df = MockDataFrame(data)

            elif "database" in source.lower():
                # Simulate database query
                time.sleep(0.3)
                data = [[random.random() for _ in range(15)] for _ in range(5000)]
                df = MockDataFrame(data)

            elif "api" in source.lower():
                # Simulate API call
                time.sleep(0.5)
                data = [[random.random() for _ in range(8)] for _ in range(2000)]
                df = MockDataFrame(data)

            else:
                raise ValueError(f"Unsupported data source: {source}")

            self.logger.info(
                f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns",
                extra={
                    "source": source,
                    "rows": df.shape[0],
                    "columns": df.shape[1],
                    "memory_usage_mb": df.shape[0] * df.shape[1] * 8 / 1024 / 1024,  # Approximate
                },
            )

            return df

    @log
    def clean_data(self, df: MockDataFrame) -> MockDataFrame:
        """Clean and preprocess data."""
        with log_context("Data cleaning", logger=self.logger):
            original_rows = df.shape[0]

            self.logger.info(f"Starting data cleaning for {original_rows} rows")

            # Simulate data cleaning steps
            with performance_context("Removing null values", logger=self.logger):
                df_clean = df.dropna()
                removed_rows = original_rows - df_clean.shape[0]
                if removed_rows > 0:
                    self.logger.warning(f"Removed {removed_rows} rows with null values")

            # Simulate outlier detection
            with performance_context("Outlier detection", logger=self.logger):
                time.sleep(0.05)
                outliers_detected = random.randint(5, 50)
                self.logger.info(f"Detected {outliers_detected} potential outliers")

            # Simulate feature engineering
            with performance_context("Feature engineering", logger=self.logger):
                time.sleep(0.1)
                new_features = 3
                df_clean.columns.extend([f"engineered_feature_{i}" for i in range(new_features)])
                self.logger.info(f"Created {new_features} engineered features")

            self.logger.info(
                f"Data cleaning completed: {df_clean.shape[0]} rows remaining",
                extra={
                    "original_rows": original_rows,
                    "final_rows": df_clean.shape[0],
                    "removed_rows": removed_rows,
                    "outliers_detected": outliers_detected,
                    "new_features": new_features,
                },
            )

            return df_clean

    @log
    def split_data(self, df: MockDataFrame, test_size: float = 0.2):
        """Split data into training and testing sets."""
        with log_context("Data splitting", logger=self.logger):
            total_rows = df.shape[0]
            test_rows = int(total_rows * test_size)
            train_rows = total_rows - test_rows

            # Simulate train/test split
            train_data = df.data[:train_rows]
            test_data = df.data[train_rows:]

            X_train = MockDataFrame(train_data, df.columns)
            X_test = MockDataFrame(test_data, df.columns)

            # Simulate target variable
            y_train = [random.randint(0, 1) for _ in range(train_rows)]
            y_test = [random.randint(0, 1) for _ in range(test_rows)]

            self.logger.info(
                f"Data split completed: {train_rows} training, {test_rows} testing samples",
                extra={
                    "total_samples": total_rows,
                    "train_samples": train_rows,
                    "test_samples": test_rows,
                    "test_ratio": test_size,
                },
            )

            return X_train, X_test, y_train, y_test


class ModelTrainer:
    """Model training and evaluation with detailed logging."""

    def __init__(self):
        self.logger = Logger("model_training")
        self.experiment_id = None

    def start_experiment(self, experiment_name: str):
        """Start a new experiment with logging."""
        self.experiment_id = f"exp_{int(time.time())}"
        self.logger.info(
            f"Starting experiment: {experiment_name} (ID: {self.experiment_id})",
            extra={"experiment_id": self.experiment_id, "experiment_name": experiment_name},
        )

    @log
    def train_model(
        self, X_train: MockDataFrame, y_train: list, model_type: str = "RandomForest"
    ) -> MockModel:
        """Train machine learning model with logging."""
        if not self.experiment_id:
            raise ValueError("No active experiment. Call start_experiment() first.")

        with log_context(f"Training {model_type} model", logger=self.logger):
            self.logger.info(f"Initializing {model_type} model")
            model = MockModel(model_type)

            # Log training data info
            self.logger.info(
                f"Training data: {X_train.shape[0]} samples, {X_train.shape[1]} features",
                extra={
                    "experiment_id": self.experiment_id,
                    "model_type": model_type,
                    "train_samples": X_train.shape[0],
                    "features": X_train.shape[1],
                },
            )

            # Train model with performance monitoring
            with performance_context("Model fitting", logger=self.logger) as perf_ctx:
                model.fit(X_train, y_train)

            self.logger.info(
                f"{model_type} model training completed",
                extra={
                    "experiment_id": self.experiment_id,
                    "model_type": model_type,
                    "training_duration": (
                        perf_ctx.duration if hasattr(perf_ctx, "duration") else "unknown"
                    ),
                },
            )

            return model

    @log
    def evaluate_model(self, model: MockModel, X_test: MockDataFrame, y_test: list) -> dict:
        """Evaluate model performance with comprehensive logging."""
        with log_context("Model evaluation", logger=self.logger):
            # Generate predictions
            with performance_context("Generating predictions", logger=self.logger):
                predictions = model.predict(X_test)

            # Calculate metrics
            accuracy = model.score(X_test, y_test)
            precision = random.uniform(0.6, 0.9)
            recall = random.uniform(0.6, 0.9)
            f1_score = 2 * (precision * recall) / (precision + recall)

            metrics = {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "test_samples": len(y_test),
            }

            self.logger.info(
                f"Model evaluation completed - Accuracy: {accuracy:.4f}, "
                f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1_score:.4f}",
                extra={
                    "experiment_id": self.experiment_id,
                    "model_type": model.model_type,
                    **metrics,
                },
            )

            # Log feature importance if available
            if model.feature_importance:
                top_features = sorted(
                    enumerate(model.feature_importance), key=lambda x: x[1], reverse=True
                )[:5]

                self.logger.info(
                    f"Top 5 important features: {[(f'feature_{i}', round(importance, 4)) for i, importance in top_features]}",
                    extra={"experiment_id": self.experiment_id},
                )

            return metrics

    @log
    def hyperparameter_tuning(self, X_train: MockDataFrame, y_train: list, param_grid: dict):
        """Perform hyperparameter tuning with logging."""
        with log_context("Hyperparameter tuning", logger=self.logger):
            best_score = 0
            best_params = None

            # Simulate grid search
            total_combinations = len(param_grid.get("n_estimators", [100])) * len(
                param_grid.get("max_depth", [10])
            )

            self.logger.info(
                f"Starting hyperparameter tuning with {total_combinations} combinations",
                extra={
                    "experiment_id": self.experiment_id,
                    "total_combinations": total_combinations,
                },
            )

            for i, n_est in enumerate(param_grid.get("n_estimators", [100])):
                for j, max_depth in enumerate(param_grid.get("max_depth", [10])):
                    params = {"n_estimators": n_est, "max_depth": max_depth}

                    # Simulate training with these parameters
                    model = MockModel("RandomForest")
                    model.fit(X_train, y_train)
                    score = model.score(X_train, y_train)

                    self.logger.debug(
                        f"Params {params} -> Score: {score:.4f}",
                        extra={
                            "experiment_id": self.experiment_id,
                            "params": params,
                            "score": score,
                        },
                    )

                    if score > best_score:
                        best_score = score
                        best_params = params
                        self.logger.info(
                            f"New best score: {best_score:.4f} with params {best_params}"
                        )

            self.logger.info(
                f"Hyperparameter tuning completed - Best score: {best_score:.4f}, Best params: {best_params}",
                extra={
                    "experiment_id": self.experiment_id,
                    "best_score": best_score,
                    "best_params": best_params,
                },
            )

            return best_params, best_score


class ExperimentTracker:
    """Track and compare multiple experiments."""

    def __init__(self):
        self.logger = Logger("experiment_tracking")
        self.experiments = {}

    @log
    def log_experiment(
        self, experiment_id: str, model_type: str, metrics: dict, params: dict = None
    ):
        """Log experiment results."""
        experiment_data = {
            "experiment_id": experiment_id,
            "model_type": model_type,
            "metrics": metrics,
            "params": params or {},
            "timestamp": time.time(),
        }

        self.experiments[experiment_id] = experiment_data

        self.logger.info(
            f"Experiment logged: {experiment_id} ({model_type}) - Accuracy: {metrics.get('accuracy', 'N/A'):.4f}",
            extra=experiment_data,
        )

    @log
    def compare_experiments(self, metric: str = "accuracy"):
        """Compare experiments by a specific metric."""
        if not self.experiments:
            self.logger.warning("No experiments to compare")
            return

        sorted_experiments = sorted(
            self.experiments.items(), key=lambda x: x[1]["metrics"].get(metric, 0), reverse=True
        )

        self.logger.info(f"Experiment comparison by {metric}:")

        for i, (exp_id, exp_data) in enumerate(sorted_experiments[:5]):  # Top 5
            score = exp_data["metrics"].get(metric, 0)
            model_type = exp_data["model_type"]

            self.logger.info(
                f"  {i+1}. {exp_id} ({model_type}): {score:.4f}",
                extra={
                    "rank": i + 1,
                    "experiment_id": exp_id,
                    "model_type": model_type,
                    "score": score,
                    "metric": metric,
                },
            )


async def run_data_science_pipeline():
    """Run a complete data science pipeline with logging."""
    print("=== Data Science Pipeline Demo ===\n")

    # Initialize components
    processor = DataProcessor()
    trainer = ModelTrainer()
    tracker = ExperimentTracker()

    print("1. Data Loading and Preprocessing")
    print("-" * 40)

    # Load data from different sources
    datasets = ["data/training.csv", "database://prod/users", "api://external/features"]

    for source in datasets:
        try:
            # Load and process data
            df = processor.load_data(source)
            df_clean = processor.clean_data(df)
            X_train, X_test, y_train, y_test = processor.split_data(df_clean)

            print("\n2. Model Training and Evaluation")
            print("-" * 40)

            # Train different models
            models_to_try = ["RandomForest", "GradientBoosting", "NeuralNetwork"]

            for model_type in models_to_try:
                # Start experiment
                experiment_name = f"{model_type}_on_{source.split('/')[-1]}"
                trainer.start_experiment(experiment_name)

                # Train model
                model = trainer.train_model(X_train, y_train, model_type)

                # Evaluate model
                metrics = trainer.evaluate_model(model, X_test, y_test)

                # Log experiment
                tracker.log_experiment(trainer.experiment_id, model_type, metrics)

            # Only run hyperparameter tuning for first dataset to save time
            if source == datasets[0]:
                print("\n3. Hyperparameter Tuning")
                print("-" * 35)

                param_grid = {"n_estimators": [50, 100, 200], "max_depth": [5, 10, 15]}

                trainer.start_experiment("RandomForest_Tuned")
                best_params, best_score = trainer.hyperparameter_tuning(
                    X_train, y_train, param_grid
                )

                # Train final model with best parameters
                final_model = trainer.train_model(X_train, y_train, "RandomForest")
                final_metrics = trainer.evaluate_model(final_model, X_test, y_test)

                tracker.log_experiment(
                    trainer.experiment_id, "RandomForest_Tuned", final_metrics, best_params
                )

        except Exception as e:
            processor.logger.error(f"Pipeline failed for {source}: {e}")
            continue

    print("\n4. Experiment Comparison")
    print("-" * 30)

    # Compare all experiments
    tracker.compare_experiments("accuracy")
    tracker.compare_experiments("f1_score")

    print("\n✓ Data science pipeline completed!")


def main():
    """Main function."""
    print("=== Data Science Pipeline Logging Demo ===\n")

    # Configure logging for data science workflows
    configure(level="INFO", visual_mode=True, use_symbols=True, format_type="detailed")

    # Run the pipeline
    import asyncio

    asyncio.run(run_data_science_pipeline())

    print("\nData Science Features Demonstrated:")
    print("- Data loading from multiple sources")
    print("- Data preprocessing and cleaning logging")
    print("- Performance monitoring for each step")
    print("- Model training with detailed metrics")
    print("- Model evaluation and comparison")
    print("- Hyperparameter tuning logging")
    print("- Experiment tracking and comparison")
    print("- Error handling in data pipelines")
    print("- Feature importance logging")
    print("- Structured logging with metrics")


if __name__ == "__main__":
    main()
