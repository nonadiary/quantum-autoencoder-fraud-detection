import pandas as pd
from sklearn.preprocessing import StandardScaler
from imblearn.under_sampling import RandomUnderSampler
import os

def load_data(filepath: str) -> pd.DataFrame:
    """Loads the dataset from a CSV file."""
    return pd.read_csv(filepath)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing/null values by dropping (if any) and remove duplicate rows.
    """
    df_cleaned = df.dropna()               # drop rows with any nulls (if present)
    df_cleaned = df_cleaned.drop_duplicates()      # drop exact duplicate transactions
    return df_cleaned

def scale_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain 'Time' and 'Amount' columns and apply standard scaling.
    """
    df_scaled = df.copy()
    scaler = StandardScaler()
    # Check if columns exist to avoid KeyErrors in partial testing scenarios
    cols_to_scale = [col for col in ['Time', 'Amount'] if col in df_scaled.columns]
    if cols_to_scale:
        df_scaled[cols_to_scale] = scaler.fit_transform(df_scaled[cols_to_scale])
    return df_scaled

def undersample_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Random undersampling to balance classes (make genuine ≈ fraud in count).
    Expects a 'Class' column in the dataframe.
    """
    if 'Class' not in df.columns:
        raise ValueError("DataFrame must contain 'Class' column for undersampling")

    X = df.drop('Class', axis=1)
    y = df['Class']

    # Check if we have enough data for both classes to undersample
    if len(y.unique()) < 2:
         # If only one class exists, we can't balance. Return as is or handle appropriately.
         # For the purpose of this specific pipeline which expects imbalance,
         # if we only have one class, undersampling usually fails or errors out in imblearn depending on version/settings.
         # But let's assume standard input.
         pass

    rus = RandomUnderSampler(sampling_strategy=1.0, random_state=42)
    try:
        X_res, y_res = rus.fit_resample(X, y)
    except ValueError as e:
        # This might happen if the number of samples in one class is too small or other config issues
        # For now re-raise
        raise e

    # Combine the resampled features and labels into one DataFrame
    df_resampled = pd.DataFrame(X_res, columns=X.columns)
    df_resampled['Class'] = y_res

    # Shuffle the rows of the resampled dataset (optional, to mix class order)
    df_resampled = df_resampled.sample(frac=1, random_state=42).reset_index(drop=True)
    return df_resampled

def preprocess_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs the full preprocessing pipeline: clean, scale, undersample.
    """
    df = clean_data(df)
    df = scale_data(df)
    df = undersample_data(df)
    return df

if __name__ == "__main__":
    try:
        # 1. Load the dataset
        df = load_data('creditcard.csv')

        # Run pipeline
        df_processed = preprocess_pipeline(df)

        # 5. Save the preprocessed balanced dataset
        df_processed.to_csv('preprocessed-creditcard.csv', index=False)
        print("Preprocessing complete. Saved to preprocessed-creditcard.csv")
    except FileNotFoundError:
        print("Error: creditcard.csv not found. Please ensure the file exists.")
    except Exception as e:
        print(f"An error occurred during preprocessing: {e}")
