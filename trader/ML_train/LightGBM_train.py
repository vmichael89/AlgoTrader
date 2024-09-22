import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from boruta import BorutaPy
import re


# Load CSV file into DataFrame
def load_data(file_path):
    df = pd.read_csv(file_path)
    df = df.rename(columns=lambda x: re.sub('[^A-Za-z0-9_]+', '', x))
    return df


# Prepare the data
def prepare_data(df):
    X = df.drop(columns=['label'])  # Drop the 'label' column to get features
    y = df['label']  # Use the 'label' column as the target
    return X, y


def split_at_percentile(X, y, percentile=0.8):
    # Determine the index to split at
    split_index = int(len(X) * percentile)

    # Split X and y at the calculated index
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    zeroes = y_train.tolist().count(0)
    ones = y_train.tolist().count(1)

    print(f"Proportion of zeroes: {zeroes / (ones + zeroes):.4f}")

    return X_train, X_test, y_train, y_test


# Feature Selection using Boruta
def select_features_boruta(X_train, y_train):
    # Create a random forest classifier
    rf = RandomForestClassifier(n_estimators=100, random_state=15)

    # Initialize Boruta feature selection method
    boruta_selector = BorutaPy(rf, n_estimators='auto', random_state=15)

    # Fit Boruta to the training data
    boruta_selector.fit(X_train.values, y_train.values)

    # Select the features marked as important by Boruta
    X_train_selected = X_train.loc[:, boruta_selector.support_]

    # Output the selected features
    selected_features = X_train.columns[boruta_selector.support_].tolist()
    print(f"Selected Features: {selected_features}")

    return X_train_selected


# Train Random Forest and evaluate NPV
def train_and_evaluate(X, y, **kwargs):
    # Split the data into training and testing sets
    percentile = kwargs.get('percentile', 0.8)
    X_train, X_test, y_train, y_test = split_at_percentile(X, y, percentile)

    # Perform Boruta feature selection
    X_train_selected = select_features_boruta(X_train, y_train)
    X_test_selected = X_test[X_train_selected.columns]  # Ensure X_test has the same selected features

    # Create and configure the Random Forest model
    rf = RandomForestClassifier(n_estimators=100, random_state=15)

    # Train the model on the selected features
    rf.fit(X_train_selected, y_train)

    # Make predictions on the test set
    y_pred = rf.predict(X_test_selected)

    # Compute confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # Extract true negatives, false positives, false negatives, and true positives
    tn, fp, fn, tp = cm.ravel()

    # Calculate NPV
    npv = tp / (tp + fp)
    return npv


if __name__ == "__main__":
    # Define the relative path to model_data.csv
    file_path = os.path.join("..", "..", "data", "model_data_144.csv")

    # Load the CSV file
    df = load_data(file_path).dropna()

    # Prepare the data
    X, y = prepare_data(df)

    select_features_boruta(X,y)