import os
import sys

import pandas as pd

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.ml_utils import train_career_model


def main() -> None:
    dataset_path = os.path.join(ROOT_DIR, "dataset", "career_training_data.csv")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Missing training dataset: {dataset_path}")

    dataframe = pd.read_csv(dataset_path)
    bundle = train_career_model(dataframe)
    print("Model trained successfully")
    print(f"Classes: {list(bundle.classes)}")


if __name__ == "__main__":
    main()
