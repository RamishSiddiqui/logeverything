"""
Example demonstrating LogEverything integration with data science workflows using context managers.

This example shows how to use LogEverything's context managers with pandas, numpy
and machine learning libraries to provide enhanced logging during different phases
of a data science pipeline.
"""

import logging
import os
import sys
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logeverything as le
from logeverything import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryFileHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
)

# Initialize logging with basic settings
logger = le.setup_logging(
    level=logging.INFO, handlers=["console"], log_entry_exit=True, beautify=True
)
ds_logger = le.get_logger("datascience")


class DataSciencePipeline:
    """Example data science pipeline utilizing context managers for different processing phases."""

    @le.log
    def __init__(self, data_path: str = None):
        """Initialize the pipeline with configuration settings."""
        self.data_path = data_path
        self.logger = ds_logger
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.model = None

        # Generate synthetic data if no path provided
        if not data_path:
            self.logger.info("No data path provided. Using synthetic data.")
            self._generate_sample_data()

    @le.log
    def _generate_sample_data(self, n_samples: int = 1000):
        """Generate synthetic data for demonstration."""
        np.random.seed(42)
        # Create a synthetic dataset
        self.data = pd.DataFrame(
            {
                "feature_1": np.random.normal(0, 1, n_samples),
                "feature_2": np.random.normal(0, 1, n_samples),
                "feature_3": np.random.normal(0, 1, n_samples),
                "feature_4": np.random.normal(0, 1, n_samples),
                "target": np.random.choice([0, 1], size=n_samples),
            }
        )
        self.logger.info(
            f"Generated synthetic dataset with {n_samples} samples and {self.data.shape[1]} columns"
        )

    @le.log
    def load_data(self):
        """Load data from file or use generated data."""
        if self.data_path:
            # Use VerboseLoggingContext to capture detailed information during data loading
            with VerboseLoggingContext(level=logging.DEBUG):
                self.logger.info(f"Loading data from {self.data_path}")
                try:
                    # Different file types may need different loading methods
                    if self.data_path.endswith(".csv"):
                        self.data = pd.read_csv(self.data_path)
                    elif self.data_path.endswith(".parquet"):
                        self.data = pd.read_parquet(self.data_path)
                    elif self.data_path.endswith(".xlsx"):
                        self.data = pd.read_excel(self.data_path)
                    else:
                        self.logger.error(f"Unsupported file format: {self.data_path}")
                        raise ValueError(f"Unsupported file format: {self.data_path}")

                    self.logger.debug(f"Data shape: {self.data.shape}")
                    self.logger.debug(f"Data columns: {list(self.data.columns)}")
                    self.logger.debug(f"Data types:\n{self.data.dtypes}")
                    self.logger.debug(f"Data sample:\n{self.data.head(3)}")
                except Exception as e:
                    self.logger.exception(f"Error loading data: {str(e)}")
                    raise

        return self.data

    @le.log
    def explore_data(self):
        """Perform exploratory data analysis with detailed logging."""
        if self.data is None:
            self.logger.warning("No data available. Call load_data() first.")
            return

        # Use TemporaryFileHandlerContext to save EDA results to a dedicated file
        with TemporaryFileHandlerContext("eda_results.log", level=logging.DEBUG):
            self.logger.info("Starting exploratory data analysis")

            # Basic statistics
            self.logger.info("Generating statistical summary")
            self.logger.debug(f"Summary statistics:\n{self.data.describe()}")

            # Missing values analysis
            missing_counts = self.data.isnull().sum()
            self.logger.info(f"Missing values per column:\n{missing_counts}")

            # Correlation analysis - use context for visual formatting
            with VisualLoggingContext():
                self.logger.info("Correlation matrix:")
                corr_matrix = self.data.corr().round(2)
                # Convert to string with fixed width formatting for better log readability
                corr_str = "\n".join(
                    [
                        " | ".join([f"{col:>10}" for col in corr_matrix.columns]),
                        "-" * (12 * len(corr_matrix.columns)),
                        *[
                            " | ".join([f"{val:>10.2f}" for val in row])
                            for _, row in corr_matrix.iterrows()
                        ],
                    ]
                )
                self.logger.info(f"\n{corr_str}")

            # Target distribution (for classification tasks)
            if "target" in self.data.columns:
                target_counts = self.data["target"].value_counts()
                self.logger.info(f"Target distribution:\n{target_counts}")
                target_pct = target_counts / len(self.data) * 100
                self.logger.info(f"Target distribution (%):\n{target_pct.round(2)}")

            self.logger.info("Exploratory data analysis completed")

    @le.log
    def preprocess_data(self, test_size: float = 0.2):
        """Preprocess data for modeling."""
        if self.data is None:
            self.logger.warning("No data available. Call load_data() first.")
            return

        self.logger.info("Starting data preprocessing")

        # Handle missing values - suppress detailed logs for routine operations
        with QuietLoggingContext(level=logging.WARNING):
            self.logger.info("Handling missing values")
            # Fill numeric columns with median
            numeric_cols = self.data.select_dtypes(include=["number"]).columns
            self.data[numeric_cols] = self.data[numeric_cols].fillna(
                self.data[numeric_cols].median()
            )

            # Fill categorical columns with mode
            cat_cols = self.data.select_dtypes(include=["object", "category"]).columns
            for col in cat_cols:
                self.data[col] = self.data[col].fillna(self.data[col].mode()[0])

        # Log feature engineering steps in detail
        with LoggingContext(level=logging.DEBUG, log_arguments=True):
            self.logger.info("Performing feature engineering")

            # Identify target and features
            target_col = "target" if "target" in self.data.columns else None
            if not target_col:
                self.logger.warning("No 'target' column found. Using last column as target.")
                target_col = self.data.columns[-1]

            feature_cols = [col for col in self.data.columns if col != target_col]
            self.logger.debug(f"Target column: {target_col}")
            self.logger.debug(f"Feature columns: {feature_cols}")

            # Train-test split
            X = self.data[feature_cols]
            y = self.data[target_col]
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            self.logger.info(
                f"Data split: train={len(self.X_train)} samples, test={len(self.X_test)} samples"
            )

            # Feature scaling
            scaler = StandardScaler()
            self.X_train = pd.DataFrame(
                scaler.fit_transform(self.X_train), columns=feature_cols, index=self.X_train.index
            )
            self.X_test = pd.DataFrame(
                scaler.transform(self.X_test), columns=feature_cols, index=self.X_test.index
            )
            self.logger.debug("Data scaling completed")

        self.logger.info("Data preprocessing completed successfully")
        return self.X_train, self.X_test, self.y_train, self.y_test

    @le.log
    def train_model(self):
        """Train a machine learning model with detailed logging of important metrics."""
        if self.X_train is None or self.y_train is None:
            self.logger.warning("Training data not prepared. Call preprocess_data() first.")
            return

        # Use VerboseLoggingContext to capture all training details in DEBUG level
        with VerboseLoggingContext():
            self.logger.info("Starting model training")

            try:
                # For this example, we'll use RandomForest
                self.logger.debug("Initializing RandomForestClassifier")
                self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)

                # Log model parameters
                self.logger.debug(f"Model parameters: {self.model.get_params()}")

                # Train the model
                self.logger.info("Fitting model to training data")
                self.model.fit(self.X_train, self.y_train)

                # Log training metrics
                train_accuracy = self.model.score(self.X_train, self.y_train)
                self.logger.info(f"Training accuracy: {train_accuracy:.4f}")

                # Feature importance
                if hasattr(self.model, "feature_importances_"):
                    feature_importance = pd.DataFrame(
                        {
                            "feature": self.X_train.columns,
                            "importance": self.model.feature_importances_,
                        }
                    ).sort_values("importance", ascending=False)
                    self.logger.info(f"Feature importance:\n{feature_importance}")

                self.logger.info("Model training completed successfully")
                return self.model

            except Exception as e:
                self.logger.exception(f"Error training model: {str(e)}")
                raise

    @le.log
    def evaluate_model(self) -> Dict:
        """Evaluate the trained model with context managers for logging results at different levels."""
        if self.model is None:
            self.logger.warning("No trained model available. Call train_model() first.")
            return {}

        # Use TemporaryFileHandlerContext to save evaluation metrics to a dedicated file
        with TemporaryFileHandlerContext("model_evaluation.log", level=logging.DEBUG):
            self.logger.info("Starting model evaluation")

            try:
                # Predictions
                y_pred = self.model.predict(self.X_test)

                # Calculate metrics
                accuracy = accuracy_score(self.y_test, y_pred)

                # Basic metrics at INFO level
                self.logger.info(f"Test accuracy: {accuracy:.4f}")

                # Detailed metrics at DEBUG level
                with VerboseLoggingContext(level=logging.DEBUG):
                    report = classification_report(self.y_test, y_pred)
                    self.logger.debug(f"Classification report:\n{report}")

                # Visualize results with enhanced formatting
                with VisualLoggingContext():
                    self.logger.info("=== Model Evaluation Results ===")
                    self.logger.info(f"✓ Accuracy: {accuracy:.4f}")

                    # More metrics could be added here

                    self.logger.info("=== End of Evaluation ===")

                # Return metrics dictionary
                evaluation_metrics = {"accuracy": accuracy, "y_pred": y_pred, "y_true": self.y_test}

                return evaluation_metrics

            except Exception as e:
                self.logger.exception(f"Error evaluating model: {str(e)}")
                return {}


# Demonstrate the pipeline with context managers
def run_demonstration():
    """Run a demonstration of the data science pipeline with context managers."""
    # Use global context for the entire pipeline run
    with LoggingContext(logger_name="datascience_demo", level=logging.INFO):
        logger.info("Starting data science pipeline demonstration")

        try:
            # Initialize pipeline
            pipeline = DataSciencePipeline()

            # Load and explore data
            pipeline.load_data()
            pipeline.explore_data()

            # Preprocessing with quieter logging for routine steps
            with QuietLoggingContext(level=logging.WARNING):
                logger.info("Starting preprocessing with minimal logging")
                pipeline.preprocess_data()

            # Training and evaluation with detailed logging
            with VerboseLoggingContext(level=logging.DEBUG):
                logger.info("Starting model training and evaluation with verbose logging")
                pipeline.train_model()
                metrics = pipeline.evaluate_model()
                logger.info(f"Final accuracy: {metrics.get('accuracy', 'N/A')}")

            logger.info("Data science pipeline demonstration completed successfully")

        except Exception as e:
            logger.exception(f"Error in pipeline demonstration: {str(e)}")


if __name__ == "__main__":
    run_demonstration()
