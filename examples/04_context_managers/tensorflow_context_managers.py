"""
Example demonstrating LogEverything integration with TensorFlow using context managers.

This example shows how to use LogEverything's context managers to provide appropriate
logging during different phases of TensorFlow model development including data loading,
model building, training, evaluation, and inference.
"""

import logging
import os
import sys
import time
from datetime import datetime

import numpy as np

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

# Import TensorFlow
try:
    import tensorflow as tf
    from tensorflow import keras

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("TensorFlow not installed. This example requires TensorFlow.")
    print("Install with: pip install tensorflow")
    sys.exit(1)

# Set up logging
logger = le.setup_logging(
    level=logging.INFO, handlers=["console"], log_entry_exit=True, beautify=True
)

# Create dedicated logger for TensorFlow operations
tf_logger = le.get_logger("tensorflow")


# Custom TensorFlow callback for logging with LogEverything
class LogEverythingCallback(keras.callbacks.Callback):
    """
    Custom Keras callback that integrates with LogEverything for enhanced logging.

    This callback captures training metrics and logs them using the appropriate
    context managers based on performance and training phase.
    """

    def __init__(self, logger, log_frequency=1):
        super().__init__()
        self.logger = logger
        self.log_frequency = log_frequency
        self.start_time = None
        self.epoch_start_time = None
        self.batch_start_time = None
        self.batch_times = []
        self.metrics_history = {}

    def on_train_begin(self, logs=None):
        # Use VerboseLoggingContext for training start
        with VerboseLoggingContext():
            self.start_time = time.time()
            self.logger.info("Starting model training")

            # Log model summary if available
            if hasattr(self.model, "summary"):
                # Redirect model summary to a string
                summary_list = []
                self.model.summary(print_fn=lambda x: summary_list.append(x))
                summary = "\n".join(summary_list)

                # Log the model summary
                self.logger.debug(f"Model architecture:\n{summary}")

    def on_epoch_begin(self, epoch, logs=None):
        self.epoch_start_time = time.time()
        self.logger.info(f"Starting epoch {epoch + 1}/{self.params['epochs']}")

    def on_batch_begin(self, batch, logs=None):
        self.batch_start_time = time.time()

    def on_batch_end(self, batch, logs=None):
        if self.batch_start_time:
            batch_time = time.time() - self.batch_start_time
            self.batch_times.append(batch_time)

            # Log only every log_frequency batches
            if batch % self.log_frequency == 0 or batch == self.params["steps"] - 1:
                # Use QuietLoggingContext for routine batch logging to reduce noise
                with QuietLoggingContext(level=logging.DEBUG):
                    metrics_str = ", ".join(f"{k}: {v:.4f}" for k, v in logs.items())
                    self.logger.debug(f"Batch {batch + 1}/{self.params['steps']}: {metrics_str}")

    def on_epoch_end(self, epoch, logs=None):
        # Track metrics history
        for metric, value in logs.items():
            if metric not in self.metrics_history:
                self.metrics_history[metric] = []
            self.metrics_history[metric].append(value)

        epoch_time = time.time() - self.epoch_start_time
        avg_batch_time = np.mean(self.batch_times) if self.batch_times else 0

        # Use different context managers based on metrics
        if logs.get("val_loss", float("inf")) > logs.get("loss", float("inf")):
            # Warning for potential overfitting
            with LoggingContext(level=logging.WARNING):
                self.logger.warning(
                    f"Epoch {epoch + 1}/{self.params['epochs']} - Potential overfitting detected"
                )
                metrics_str = ", ".join(f"{k}: {v:.4f}" for k, v in logs.items())
                self.logger.warning(f"Metrics: {metrics_str}")
                self.logger.warning(
                    f"Time: {epoch_time:.2f}s (avg batch: {avg_batch_time * 1000:.2f}ms)"
                )
        else:
            # Use VisualLoggingContext for epoch results with proper formatting
            with VisualLoggingContext():
                self.logger.info(f"Epoch {epoch + 1}/{self.params['epochs']} completed")
                metrics_str = ", ".join(f"{k}: {v:.4f}" for k, v in logs.items())
                self.logger.info(f"Metrics: {metrics_str}")
                self.logger.info(
                    f"Time: {epoch_time:.2f}s (avg batch: {avg_batch_time * 1000:.2f}ms)"
                )

        # Reset batch times for next epoch
        self.batch_times = []

    def on_train_end(self, logs=None):
        # Log training summary with TemporaryFileHandlerContext to save to file
        with TemporaryFileHandlerContext("training_summary.log"):
            total_time = time.time() - self.start_time
            self.logger.info("Training completed")
            self.logger.info(f"Total training time: {total_time:.2f}s")

            # Log final metrics
            if logs:
                metrics_str = ", ".join(f"{k}: {v:.4f}" for k, v in logs.items())
                self.logger.info(f"Final metrics: {metrics_str}")

            # Log metrics history as a table
            if self.metrics_history:
                self.logger.info("Metrics history:")
                header = "Epoch | " + " | ".join(
                    f"{metric:>10}" for metric in self.metrics_history.keys()
                )
                self.logger.info(header)
                self.logger.info("-" * len(header))

                for epoch in range(len(next(iter(self.metrics_history.values())))):
                    row = f"{epoch + 1:5d} | "
                    row += " | ".join(
                        f"{self.metrics_history[metric][epoch]:10.4f}"
                        for metric in self.metrics_history.keys()
                    )
                    self.logger.info(row)


class TensorFlowModel:
    """
    Example TensorFlow model manager with LogEverything integration.

    This class demonstrates how to use context managers effectively
    during different phases of model lifecycle.
    """

    def __init__(self):
        self.logger = tf_logger
        self.model = None
        self.history = None

    @le.log
    def build_model(self, input_shape, num_classes):
        """Build a simple CNN model with detailed architecture logging."""
        with VerboseLoggingContext(level=logging.DEBUG):
            self.logger.info(
                f"Building model with input_shape={input_shape}, num_classes={num_classes}"
            )

            # Use Sequential API for simplicity
            model = keras.Sequential(
                [
                    keras.layers.InputLayer(input_shape=input_shape),
                    # Convolutional layers
                    keras.layers.Conv2D(32, kernel_size=3, activation="relu", padding="same"),
                    keras.layers.MaxPooling2D(pool_size=2),
                    keras.layers.Conv2D(64, kernel_size=3, activation="relu", padding="same"),
                    keras.layers.MaxPooling2D(pool_size=2),
                    # Flatten and dense layers
                    keras.layers.Flatten(),
                    keras.layers.Dense(128, activation="relu"),
                    keras.layers.Dropout(0.5),
                    keras.layers.Dense(num_classes, activation="softmax"),
                ]
            )

            # Compile the model
            model.compile(
                optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
            )

            # Log model size and parameters
            self.logger.debug(f"Model has {model.count_params():,} parameters")

            # Store the model
            self.model = model
            return model

    @le.log
    def load_data(self):
        """
        Load the MNIST dataset with performance logging.

        Returns:
            Tuple of training and testing data
        """
        with LoggingContext(level=logging.INFO):
            self.logger.info("Loading MNIST dataset")
            start_time = time.time()

            # Load MNIST dataset from TensorFlow
            (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

            # Preprocess the data
            x_train = x_train.astype("float32") / 255
            x_test = x_test.astype("float32") / 255

            # Reshape for CNN input
            x_train = np.expand_dims(x_train, -1)
            x_test = np.expand_dims(x_test, -1)

            load_time = time.time() - start_time
            self.logger.info(f"Dataset loaded in {load_time:.2f}s")
            self.logger.info(f"Training set: {x_train.shape}, {y_train.shape}")
            self.logger.info(f"Test set: {x_test.shape}, {y_test.shape}")

            return (x_train, y_train), (x_test, y_test)

    @le.log
    def train_model(self, x_train, y_train, validation_data=None, epochs=5, batch_size=128):
        """
        Train the model with comprehensive logging via custom callback.

        Args:
            x_train: Training features
            y_train: Training labels
            validation_data: Tuple of (x_val, y_val) for validation
            epochs: Number of epochs to train
            batch_size: Batch size for training

        Returns:
            Training history
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Use TemporaryFileHandlerContext to save detailed training logs to file
        with TemporaryFileHandlerContext("tensorflow_training.log", level=logging.DEBUG):
            self.logger.info("Starting model training")

            # Create custom callback for LogEverything integration
            log_callback = LogEverythingCallback(self.logger)

            # Add TensorBoard callback for visualization
            tensorboard_dir = "./logs/tf_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            tensorboard_callback = keras.callbacks.TensorBoard(
                log_dir=tensorboard_dir, histogram_freq=1
            )

            # Train the model
            history = self.model.fit(
                x_train,
                y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=validation_data,
                verbose=0,  # Disable default output, we'll use our callback
                callbacks=[log_callback, tensorboard_callback],
            )

            self.history = history
            return history

    @le.log
    def evaluate_model(self, x_test, y_test):
        """
        Evaluate the model with visual logging of metrics.

        Args:
            x_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Use VisualLoggingContext for enhanced visualization of evaluation results
        with VisualLoggingContext():
            self.logger.info("Evaluating model on test data")

            # Evaluate the model
            scores = self.model.evaluate(x_test, y_test, verbose=0)
            metrics = dict(zip(self.model.metrics_names, scores))

            # Log evaluation results
            self.logger.info("=" * 40)
            self.logger.info("Model Evaluation Results")
            self.logger.info("=" * 40)

            for metric_name, metric_value in metrics.items():
                self.logger.info(f"• {metric_name}: {metric_value:.4f}")

            self.logger.info("=" * 40)

            return metrics

    @le.log
    def predict(self, x, batch_size=None):
        """
        Make predictions with the model and log performance metrics.

        Args:
            x: Input data
            batch_size: Batch size for prediction

        Returns:
            Model predictions
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Use QuietLoggingContext for routine predictions to reduce log noise
        with QuietLoggingContext(level=logging.DEBUG):
            self.logger.debug(f"Making predictions on data with shape {x.shape}")

            # Time the prediction
            start_time = time.time()
            predictions = self.model.predict(x, batch_size=batch_size, verbose=0)
            predict_time = time.time() - start_time

            # Log timing information
            samples_per_second = x.shape[0] / predict_time
            self.logger.debug(
                f"Prediction completed in {predict_time:.4f}s ({samples_per_second:.1f} samples/sec)"
            )

            return predictions

    @le.log
    def save_model(self, path):
        """
        Save the model with logging.

        Args:
            path: Path to save the model

        Returns:
            True if successful, False otherwise
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return False

        try:
            # Use VerboseLoggingContext to capture detailed information during model saving
            with VerboseLoggingContext():
                self.logger.info(f"Saving model to {path}")

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # Save the model
                self.model.save(path)

                # Log model size
                model_size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.exists(path) else 0
                self.logger.info(f"Model saved successfully ({model_size_mb:.2f} MB)")

                return True
        except Exception as e:
            self.logger.exception(f"Error saving model: {e}")
            return False

    @le.log
    def load_model(self, path):
        """
        Load a saved model with logging.

        Args:
            path: Path to load the model from

        Returns:
            Loaded model
        """
        try:
            # Use VerboseLoggingContext to capture detailed information during model loading
            with VerboseLoggingContext():
                self.logger.info(f"Loading model from {path}")

                # Check if file exists
                if not os.path.exists(path):
                    self.logger.error(f"Model file not found: {path}")
                    return None

                # Load the model
                self.model = keras.models.load_model(path)

                # Log model information
                self.logger.info(
                    f"Model loaded successfully with {self.model.count_params():,} parameters"
                )

                return self.model
        except Exception as e:
            self.logger.exception(f"Error loading model: {e}")
            return None


def run_tensorflow_example():
    """Run a complete TensorFlow example with LogEverything integration."""
    # Use LoggingContext for the entire example
    with LoggingContext(logger_name="tensorflow_demo", level=logging.INFO):
        tf_logger.info("Starting TensorFlow integration example")

        try:
            # Create model manager
            tf_model = TensorFlowModel()

            # Load data
            (x_train, y_train), (x_test, y_test) = tf_model.load_data()

            # Use a small subset for faster demonstration
            x_train = x_train[:5000]
            y_train = y_train[:5000]
            x_test = x_test[:1000]
            y_test = y_test[:1000]

            # Build model
            input_shape = x_train[0].shape
            num_classes = len(np.unique(y_train))
            tf_model.build_model(input_shape, num_classes)

            # Train model with different context managers for different epochs
            # First epoch with verbose logging
            with VerboseLoggingContext():
                tf_logger.info("Training first epoch with detailed logging")
                tf_model.train_model(x_train, y_train, validation_data=(x_test, y_test), epochs=1)

            # Remaining epochs with standard logging
            tf_model.train_model(x_train, y_train, validation_data=(x_test, y_test), epochs=2)

            # Evaluate model
            metrics = tf_model.evaluate_model(x_test, y_test)

            # Make predictions
            sample_predictions = tf_model.predict(x_test[:10])

            # Save model
            model_path = "./models/tensorflow_demo_model"
            tf_model.save_model(model_path)

            tf_logger.info("TensorFlow integration example completed successfully")

        except Exception as e:
            tf_logger.exception(f"Error in TensorFlow example: {e}")


if __name__ == "__main__":
    # Check TensorFlow availability
    if TF_AVAILABLE:
        run_tensorflow_example()
    else:
        print("TensorFlow is not available. Please install tensorflow package.")
