"""
This script turns raw data into cleaned data ready to be analyzed.
"""

from pathlib import Path
import glob
import numpy as np
from PIL import Image, ImageStat
from pandas import DataFrame
from sklearn.model_selection import train_test_split
import yaml
import mlflow


def main():
    """
    Turns raw data into cleaned data and generates a csv file containing metadata.
    """
    mlflow.set_tracking_uri("https://dagshub.com/nico-fi/SemiSupervised-DCEC.mlflow")
    mlflow.set_experiment("Prepare Data")
    mlflow.start_run()

    params_path = Path("params.yaml")
    input_folder_path = Path("data/raw/fashion_mnist")
    prepared_folder_path = Path("data/processed")
    metadata_folder_path = Path("data/ge")

    # Read images and labels
    print("Processing images...")
    x_data, y_data = [], []
    img_format, height, width, mean, std = [], [], [], [], []
    for image_path in glob.glob(str(input_folder_path / "*.png")):
        image = Image.open(image_path)
        x_data.append(np.array(image))
        y_data.append(int(image_path.split('/')[-1].split('_')[1].split('.')[0]))
        img_format.append(image.format)
        height.append(image.height)
        width.append(image.width)
        stat = ImageStat.Stat(image)
        mean.append(sum(stat.mean) / len(stat.mean))
        std.append(sum(stat.stddev) / len(stat.stddev))

    # Create csv file containing metadata
    dataframe = DataFrame(
        {
            "format": img_format,
            "height": height,
            "width": width,
            "mean": mean,
            "std": std,
            "label": y_data
        }
    )
    dataframe.to_csv(metadata_folder_path / "fashion_mnist.csv", index=False)

    # Convert data to numpy array and normalize pixel values to be between 0 and 1
    x_data = np.expand_dims(x_data, axis=-1) / 255.0
    y_data = np.array(y_data)

    # Load and log data preparation parameters
    with open(params_path, "r", encoding="utf-8") as params_file:
        params = yaml.safe_load(params_file)["prepare"]
    mlflow.log_params(
        {
        "supervision": params["supervision"],
        "random_state": params["random_state"]
        }
    )

    # Split data into supervised and unsupervised
    i_train, i_test = train_test_split(
        range(len(x_data)),
        train_size=params["supervision"],
        random_state=params["random_state"],
        stratify=y_data)
    y_train = np.full(len(x_data), -1, dtype=int)
    y_train[i_train] = y_data[i_train]
    x_test = x_data[i_test]
    y_test = y_data[i_test]

    # Save data
    prepared_folder_path.mkdir(exist_ok=True)
    np.save(prepared_folder_path / "x.npy", x_data)
    np.save(prepared_folder_path / "y_train.npy", y_train)
    np.save(prepared_folder_path / "x_test.npy", x_test)
    np.save(prepared_folder_path / "y_test.npy", y_test)

    mlflow.end_run()


if __name__ == "__main__": # pragma: no cover
    main()
