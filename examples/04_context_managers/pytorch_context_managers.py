"""
Example demonstrating LogEverything integration with PyTorch using context managers.

This example shows how to use LogEverything's context managers to provide appropriate
logging during different phases of PyTorch model development including data loading,
model building, training, evaluation, and inference.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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

# Import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torchvision
    import torchvision.transforms as transforms
    from torch.utils.data import DataLoader, TensorDataset, random_split
    from torch.utils.tensorboard import SummaryWriter

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch not installed. This example requires PyTorch.")
    print("Install with: pip install torch torchvision")
    sys.exit(1)

# Set up logging
logger = le.setup_logging(
    level=logging.INFO, handlers=["console"], log_entry_exit=True, beautify=True
)

# Create dedicated logger for PyTorch operations
torch_logger = le.get_logger("pytorch")


class SimpleConvNet(nn.Module):
    """Simple convolutional neural network for image classification."""

    def __init__(self, num_classes=10):
        super(SimpleConvNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 7 * 7)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class MetricsTracker:
    """Helper class to track and log training and evaluation metrics."""

    def __init__(self):
        self.epoch_metrics = {}
        self.history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
        self.best_val_acc = 0.0
        self.no_improvement_count = 0

    def update(self, phase, loss, accuracy):
        """Update metrics for the current phase (train/val)."""
        self.epoch_metrics[f"{phase}_loss"] = loss
        self.epoch_metrics[f"{phase}_acc"] = accuracy

        if phase == "val":
            if accuracy > self.best_val_acc:
                self.best_val_acc = accuracy
                self.no_improvement_count = 0
                return True  # New best model
            else:
                self.no_improvement_count += 1
                return False
        return False

    def epoch_end(self):
        """Store metrics at the end of an epoch."""
        for k, v in self.epoch_metrics.items():
            self.history[k].append(v)

        # Clear current epoch metrics
        self.epoch_metrics = {}


class PyTorchModel:
    """
    Example PyTorch model manager with LogEverything integration.

    This class demonstrates how to use context managers effectively
    during different phases of PyTorch model lifecycle.
    """

    def __init__(self, device=None):
        self.logger = torch_logger
        self.model = None
        self.criterion = None
        self.optimizer = None
        self.metrics = MetricsTracker()
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Log device information
        with LoggingContext():
            self.logger.info(f"Using device: {self.device}")
            if self.device.type == "cuda":
                self.logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                self.logger.info(f"Memory allocated: {torch.cuda.memory_allocated(0) / 1e6:.2f}MB")

    @le.log
    def build_model(self, num_classes=10):
        """
        Build a simple convolutional model with detailed architecture logging.

        Args:
            num_classes: Number of output classes

        Returns:
            The PyTorch model
        """
        with VerboseLoggingContext(level=logging.DEBUG):
            self.logger.info(f"Building model with {num_classes} output classes")

            # Create model instance
            model = SimpleConvNet(num_classes=num_classes)
            model.to(self.device)

            # Set loss function and optimizer
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.parameters(), lr=0.001)

            # Log model architecture
            self.logger.debug("Model architecture:")
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

            # Format model summary
            model_str = str(model)
            formatted_model = "\n".join(f"  {line}" for line in model_str.split("\n"))
            self.logger.debug(f"{formatted_model}")
            self.logger.debug(f"Total parameters: {total_params:,}")
            self.logger.debug(f"Trainable parameters: {trainable_params:,}")

            # Store model and training components
            self.model = model
            self.criterion = criterion
            self.optimizer = optimizer

            return model

    @le.log
    def load_data(self, batch_size=64):
        """
        Load the MNIST dataset and create data loaders.

        Args:
            batch_size: Batch size for training and evaluation

        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        with LoggingContext(level=logging.INFO):
            self.logger.info(f"Loading MNIST dataset with batch size {batch_size}")
            start_time = time.time()

            # Define transformations
            transform = transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
            )

            # Download and load data
            train_dataset = torchvision.datasets.MNIST(
                root="./data", train=True, download=True, transform=transform
            )
            test_dataset = torchvision.datasets.MNIST(
                root="./data", train=False, download=True, transform=transform
            )

            # Split training data into train and validation
            train_size = int(0.8 * len(train_dataset))
            val_size = len(train_dataset) - train_size
            train_dataset, val_dataset = random_split(train_dataset, [train_size, val_size])

            # Create data loaders
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size)
            test_loader = DataLoader(test_dataset, batch_size=batch_size)

            load_time = time.time() - start_time
            self.logger.info(f"Dataset loaded in {load_time:.2f}s")
            self.logger.info(f"Training set: {len(train_dataset)} samples")
            self.logger.info(f"Validation set: {len(val_dataset)} samples")
            self.logger.info(f"Test set: {len(test_dataset)} samples")

            return train_loader, val_loader, test_loader

    @le.log
    def train_epoch(self, train_loader, epoch, tensorboard_writer=None):
        """
        Train for one epoch with appropriate logging.

        Args:
            train_loader: DataLoader for training data
            epoch: Current epoch number
            tensorboard_writer: Optional SummaryWriter for TensorBoard

        Returns:
            Average loss and accuracy for the epoch
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return 0, 0

        # Use QuietLoggingContext to reduce noise during training iterations
        with QuietLoggingContext():
            self.model.train()
            self.logger.debug(f"Starting epoch {epoch + 1} training phase")

            running_loss = 0.0
            correct = 0
            total = 0
            batch_times = []

            for i, (inputs, labels) in enumerate(train_loader):
                batch_start = time.time()

                inputs, labels = inputs.to(self.device), labels.to(self.device)

                # Zero the parameter gradients
                self.optimizer.zero_grad()

                # Forward + backward + optimize
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()

                # Track statistics
                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                batch_correct = (predicted == labels).sum().item()
                correct += batch_correct
                total += labels.size(0)

                batch_time = time.time() - batch_start
                batch_times.append(batch_time)

                # Log every 10 batches
                if (i + 1) % 10 == 0:
                    batch_acc = 100 * batch_correct / labels.size(0)
                    self.logger.debug(
                        f"Epoch {epoch + 1}, Batch {i + 1}: "
                        f"Loss: {loss.item():.4f}, "
                        f"Acc: {batch_acc:.2f}%, "
                        f"Time: {batch_time*1000:.1f}ms"
                    )

            # Calculate epoch statistics
            avg_loss = running_loss / len(train_loader)
            accuracy = 100 * correct / total
            avg_batch_time = sum(batch_times) / len(batch_times)

            # Log epoch results with VisualLoggingContext for better formatting
            with VisualLoggingContext():
                self.logger.info(
                    f"Epoch {epoch + 1} Training: "
                    f"Loss: {avg_loss:.4f}, "
                    f"Accuracy: {accuracy:.2f}%, "
                    f"Time: {sum(batch_times):.2f}s "
                    f"({avg_batch_time*1000:.1f}ms/batch)"
                )

            # Update metrics
            self.metrics.update("train", avg_loss, accuracy)

            # Log to TensorBoard if available
            if tensorboard_writer:
                tensorboard_writer.add_scalar("Loss/train", avg_loss, epoch)
                tensorboard_writer.add_scalar("Accuracy/train", accuracy, epoch)

            return avg_loss, accuracy

    @le.log
    def validate(self, val_loader, epoch, tensorboard_writer=None):
        """
        Validate the model on validation data with appropriate logging.

        Args:
            val_loader: DataLoader for validation data
            epoch: Current epoch number
            tensorboard_writer: Optional SummaryWriter for TensorBoard

        Returns:
            Average loss and accuracy for validation
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return 0, 0

        # Use LoggingContext for validation
        with LoggingContext(level=logging.DEBUG):
            self.model.eval()
            self.logger.debug(f"Starting epoch {epoch + 1} validation phase")

            running_loss = 0.0
            correct = 0
            total = 0

            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)

                    # Forward pass
                    outputs = self.model(inputs)
                    loss = self.criterion(outputs, labels)

                    # Track statistics
                    running_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    correct += (predicted == labels).sum().item()
                    total += labels.size(0)

            # Calculate validation statistics
            avg_loss = running_loss / len(val_loader)
            accuracy = 100 * correct / total

            # Log validation results
            with VisualLoggingContext():
                self.logger.info(
                    f"Epoch {epoch + 1} Validation: "
                    f"Loss: {avg_loss:.4f}, "
                    f"Accuracy: {accuracy:.2f}%"
                )

            # Update metrics
            is_best = self.metrics.update("val", avg_loss, accuracy)

            # Log to TensorBoard if available
            if tensorboard_writer:
                tensorboard_writer.add_scalar("Loss/val", avg_loss, epoch)
                tensorboard_writer.add_scalar("Accuracy/val", accuracy, epoch)

            return avg_loss, accuracy, is_best

    @le.log
    def train_model(self, train_loader, val_loader, epochs=5, log_dir=None):
        """
        Train the model for multiple epochs with comprehensive logging.

        Args:
            train_loader: DataLoader for training data
            val_loader: DataLoader for validation data
            epochs: Number of epochs to train
            log_dir: Directory for TensorBoard logs

        Returns:
            Training history
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Create directory for best model
        os.makedirs("./models", exist_ok=True)

        # Initialize TensorBoard writer if log_dir provided
        tensorboard_writer = None
        if log_dir:
            log_dir = os.path.join(log_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(log_dir, exist_ok=True)
            tensorboard_writer = SummaryWriter(log_dir)

            # Log model graph to TensorBoard
            dummy_input = torch.zeros(1, 1, 28, 28).to(self.device)
            tensorboard_writer.add_graph(self.model, dummy_input)

        # Use TemporaryFileHandlerContext to save training logs to file
        with TemporaryFileHandlerContext("pytorch_training.log", level=logging.DEBUG):
            self.logger.info(f"Starting model training for {epochs} epochs")

            start_time = time.time()

            for epoch in range(epochs):
                epoch_start = time.time()

                # Train for one epoch
                train_loss, train_acc = self.train_epoch(train_loader, epoch, tensorboard_writer)

                # Validate
                val_loss, val_acc, is_best = self.validate(val_loader, epoch, tensorboard_writer)

                # Update metrics history
                self.metrics.epoch_end()

                # Save best model
                if is_best:
                    with QuietLoggingContext():
                        self.logger.info("New best model! Saving checkpoint...")
                        torch.save(
                            {
                                "epoch": epoch,
                                "model_state_dict": self.model.state_dict(),
                                "optimizer_state_dict": self.optimizer.state_dict(),
                                "val_acc": val_acc,
                                "val_loss": val_loss,
                            },
                            "./models/best_pytorch_model.pth",
                        )

                # Early stopping check
                if self.metrics.no_improvement_count >= 3:
                    with LoggingContext(level=logging.WARNING):
                        self.logger.warning(
                            f"No improvement for 3 epochs. Early stopping at epoch {epoch + 1}"
                        )
                        break

                epoch_time = time.time() - epoch_start
                self.logger.info(f"Epoch {epoch + 1} completed in {epoch_time:.2f}s")

            total_time = time.time() - start_time

            # Print training summary with VisualLoggingContext
            with VisualLoggingContext():
                self.logger.info("=" * 50)
                self.logger.info("Training Summary")
                self.logger.info("=" * 50)
                self.logger.info(f"Total training time: {total_time:.2f} seconds")
                self.logger.info(f"Best validation accuracy: {self.metrics.best_val_acc:.2f}%")
                self.logger.info("=" * 50)

                # Print learning curves as ASCII art
                if len(self.metrics.history["train_loss"]) > 0:
                    self._log_learning_curves()

            # Close TensorBoard writer
            if tensorboard_writer:
                tensorboard_writer.close()

            return self.metrics.history

    def _log_learning_curves(self):
        """Log learning curves as simple ASCII art."""
        epochs = len(self.metrics.history["train_loss"])
        if epochs < 2:
            return

        self.logger.info("Learning Curves:")

        # Find min and max values for scaling
        min_loss = min(
            min(self.metrics.history["train_loss"]), min(self.metrics.history["val_loss"])
        )
        max_loss = max(
            max(self.metrics.history["train_loss"]), max(self.metrics.history["val_loss"])
        )

        height = 10  # Height of the ASCII art
        width = epochs  # Width of the ASCII art

        # Create ASCII art for loss
        loss_chart = [" " * width for _ in range(height)]

        # Plot train loss
        for i, loss in enumerate(self.metrics.history["train_loss"]):
            y = int((loss - min_loss) / (max_loss - min_loss) * (height - 1))
            y = height - 1 - y  # Invert y-axis
            if 0 <= y < height:
                loss_chart[y] = loss_chart[y][:i] + "*" + loss_chart[y][i + 1 :]

        # Plot validation loss
        for i, loss in enumerate(self.metrics.history["val_loss"]):
            y = int((loss - min_loss) / (max_loss - min_loss) * (height - 1))
            y = height - 1 - y  # Invert y-axis
            if 0 <= y < height:
                loss_chart[y] = loss_chart[y][:i] + "+" + loss_chart[y][i + 1 :]

        self.logger.info("Loss curve (* = train, + = validation):")
        for line in loss_chart:
            self.logger.info("|" + line + "|")
        self.logger.info("+" + "-" * width + "+")

        # Print legend and scale
        self.logger.info(f"Scale: {min_loss:.2f} to {max_loss:.2f}")
        self.logger.info(f"Epochs: 1 to {epochs}")

    @le.log
    def evaluate_model(self, test_loader):
        """
        Evaluate the model on test data with detailed metrics.

        Args:
            test_loader: DataLoader for test data

        Returns:
            Dict with evaluation metrics
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Use VisualLoggingContext for enhanced visualization of evaluation results
        with VisualLoggingContext():
            self.logger.info("Evaluating model on test data")

            self.model.eval()
            correct = 0
            total = 0
            all_predicted = []
            all_labels = []
            running_loss = 0.0

            with torch.no_grad():
                for inputs, labels in test_loader:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)

                    outputs = self.model(inputs)
                    loss = self.criterion(outputs, labels)

                    running_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)

                    # Track statistics
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()

                    # Store predictions and labels for confusion matrix
                    all_predicted.extend(predicted.cpu().numpy())
                    all_labels.extend(labels.cpu().numpy())

            # Calculate metrics
            test_loss = running_loss / len(test_loader)
            test_accuracy = 100 * correct / total

            # Create per-class accuracy
            class_correct = [0] * 10
            class_total = [0] * 10

            for label, pred in zip(all_labels, all_predicted):
                class_correct[label] += int(label == pred)
                class_total[label] += 1

            # Log evaluation results
            self.logger.info("=" * 40)
            self.logger.info("Model Evaluation Results")
            self.logger.info("=" * 40)
            self.logger.info(f"Test Loss: {test_loss:.4f}")
            self.logger.info(f"Test Accuracy: {test_accuracy:.2f}%")
            self.logger.info("=" * 40)

            # Per-class accuracy
            self.logger.info("Per-Class Accuracy:")
            for i in range(10):
                if class_total[i] > 0:
                    class_acc = 100 * class_correct[i] / class_total[i]
                    self.logger.info(
                        f"Class {i}: {class_acc:.2f}% ({class_correct[i]}/{class_total[i]})"
                    )

            # Return metrics
            results = {
                "test_loss": test_loss,
                "test_accuracy": test_accuracy,
                "class_accuracy": [
                    100 * c / t if t > 0 else 0 for c, t in zip(class_correct, class_total)
                ],
                "confusion_matrix": None,  # Could compute confusion matrix here
            }

            return results

    @le.log
    def predict(self, inputs):
        """
        Make predictions with the model.

        Args:
            inputs: Input tensor or NumPy array

        Returns:
            Model predictions
        """
        if self.model is None:
            self.logger.error("Model not built. Call build_model() first.")
            return None

        # Use QuietLoggingContext for routine predictions
        with QuietLoggingContext():
            # Ensure inputs are a tensor
            if isinstance(inputs, np.ndarray):
                inputs = torch.from_numpy(inputs).float()

            # Add batch dimension if needed
            if inputs.dim() == 3:
                inputs = inputs.unsqueeze(0)

            # Move to device
            inputs = inputs.to(self.device)

            # Make prediction
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(inputs)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                _, predicted = torch.max(outputs, 1)

            # Convert to CPU and numpy
            predicted = predicted.cpu().numpy()
            probabilities = probabilities.cpu().numpy()

            return predicted, probabilities

    @le.log
    def save_model(self, path="./models/pytorch_model.pth"):
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
                torch.save(
                    {
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": (
                            self.optimizer.state_dict() if self.optimizer else None
                        ),
                        "class_count": self.model.fc2.out_features,
                        "metrics_history": self.metrics.history,
                    },
                    path,
                )

                # Log model size
                model_size_mb = os.path.getsize(path) / (1024 * 1024)
                self.logger.info(f"Model saved successfully ({model_size_mb:.2f} MB)")

                return True
        except Exception as e:
            self.logger.exception(f"Error saving model: {e}")
            return False

    @le.log
    def load_model(self, path="./models/pytorch_model.pth"):
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

                # Load the checkpoint
                checkpoint = torch.load(path, map_location=self.device)

                # Create a model with the right number of classes
                num_classes = checkpoint.get("class_count", 10)
                self.build_model(num_classes=num_classes)

                # Load state dictionaries
                self.model.load_state_dict(checkpoint["model_state_dict"])
                if self.optimizer and "optimizer_state_dict" in checkpoint:
                    self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

                # Load metrics history if available
                if "metrics_history" in checkpoint:
                    self.metrics.history = checkpoint["metrics_history"]

                self.logger.info(f"Model loaded successfully")

                return self.model
        except Exception as e:
            self.logger.exception(f"Error loading model: {e}")
            return None


def run_pytorch_example(max_epochs=3, small_dataset=True):
    """Run a complete PyTorch example with LogEverything integration."""
    # Use LoggingContext for the entire example
    with LoggingContext(logger_name="pytorch_demo", level=logging.INFO):
        torch_logger.info("Starting PyTorch integration example")

        try:
            # Create model manager
            torch_model = PyTorchModel()

            # Load data
            train_loader, val_loader, test_loader = torch_model.load_data(batch_size=64)

            # Use smaller dataset for demonstration if requested
            if small_dataset:
                # Create smaller dataloaders for demonstration
                subset_size = 1000
                train_subset = list(train_loader)[: subset_size // 64]
                val_subset = list(val_loader)[: subset_size // 64 // 4]
                test_subset = list(test_loader)[: subset_size // 64 // 4]

                # Convert to dataloaders
                def create_subset_loader(subset):
                    inputs = torch.cat([batch[0] for batch in subset])
                    labels = torch.cat([batch[1] for batch in subset])
                    dataset = TensorDataset(inputs, labels)
                    return DataLoader(dataset, batch_size=64, shuffle=True)

                train_loader = create_subset_loader(train_subset)
                val_loader = create_subset_loader(val_subset)
                test_loader = create_subset_loader(test_subset)

                torch_logger.info(f"Using smaller dataset for demonstration")

            # Build model
            torch_model.build_model(num_classes=10)

            # Train model
            log_dir = "./logs/pytorch"
            torch_model.train_model(train_loader, val_loader, epochs=max_epochs, log_dir=log_dir)

            # Evaluate model
            results = torch_model.evaluate_model(test_loader)

            # Make a sample prediction
            test_images, test_labels = next(iter(test_loader))
            sample_image = test_images[0]
            sample_label = test_labels[0].item()
            predicted, probs = torch_model.predict(sample_image)

            # Log the prediction
            with VisualLoggingContext():
                torch_logger.info(
                    f"Sample prediction: True label={sample_label}, Predicted={predicted[0]}"
                )
                torch_logger.info(f"Class probabilities: {probs[0]}")

            # Save model
            torch_model.save_model("./models/pytorch_demo_model.pth")

            torch_logger.info("PyTorch integration example completed successfully")

        except Exception as e:
            torch_logger.exception(f"Error in PyTorch example: {e}")


if __name__ == "__main__":
    # Check PyTorch availability
    if TORCH_AVAILABLE:
        run_pytorch_example(max_epochs=2, small_dataset=True)
    else:
        print("PyTorch is not available. Please install torch and torchvision packages.")
