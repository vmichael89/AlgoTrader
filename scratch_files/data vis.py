import pandas as pd

df = pd.read_csv("../data/model_data_w_candlesize.csv")
import pandas as pd

def filter_by_features_with_thresholds(df, features, percentiles, label_column='label'):
    """
    Filter the DataFrame by percentile thresholds for multiple features.

    Parameters:
    - df: pandas DataFrame containing the data
    - features: a list of feature names to filter by
    - percentiles: a list of corresponding percentile thresholds (same length as features)
    - label_column: the column containing 0s and 1s (default is 'label')

    Returns:
    - filtered_df: DataFrame filtered by the given thresholds
    - percentage_ones: Percentage of 1s in the filtered dataset
    """
    if len(features) != len(percentiles):
        raise ValueError("The length of features and percentiles must be the same.")

    # Start with the original DataFrame
    filtered_df = df.copy()

    # Apply filtering based on each feature and its respective threshold
    for feature, percentile in zip(features, percentiles):
        # Compute the percentile threshold for the feature
        threshold_value = df[feature].quantile(percentile / 100.0)

        # Filter the DataFrame based on the threshold for the current feature
        filtered_df = filtered_df[filtered_df[feature] >= threshold_value]

    # Calculate the percentage of 1s in the filtered dataset
    if len(filtered_df) > 0:  # Avoid division by zero
        percentage_ones = (filtered_df[label_column].sum() / len(filtered_df)) * 100
    else:
        percentage_ones = 0

    return filtered_df, percentage_ones

# Example usage:
# Assuming `df` is your DataFrame and you want to filter by two features
features = ['adx', 'candle_size', 'atr']
percentiles = [50, 50, 50]  # 30th percentile for 'adx' and 50th percentile for 'ATR'

# Get the filtered DataFrame and percentage of 1s
filtered_df, percentage_ones = filter_by_features_with_thresholds(df, features, percentiles)

print(f"Filtered dataset percentage of 1s: {percentage_ones}%")

print(f"Percent remaining: {len(filtered_df)/len(df)*100}")

filtered_df.to_csv('../data/model_data_w_candlesize_adj.csv')