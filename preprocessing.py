import pandas as pd
from sklearn.preprocessing import StandardScaler
from imblearn.under_sampling import RandomUnderSampler

# 1. Load the dataset
df = pd.read_csv('creditcard.csv')

# 2. Handle missing/null values by dropping (if any) and remove duplicate rows
df = df.dropna()               # drop rows with any nulls (if present)
df = df.drop_duplicates()      # drop exact duplicate transactions

# 3. Retain 'Time' and 'Amount' columns and apply standard scaling
scaler = StandardScaler()
df[['Time', 'Amount']] = scaler.fit_transform(df[['Time', 'Amount']])

# (Optional) 3.5. PCA dimensionality reduction if needed.
# The dataset's features V1-V28 are already PCA components:contentReference[oaicite:0]{index=0},
# so additional PCA is not applied here. If using a non-PCA dataset, you could apply PCA:
# from sklearn.decomposition import PCA
# pca = PCA(n_components=<desired_dim>)
# principal_components = pca.fit_transform(df.drop('Class', axis=1))
# (and then replace features with principal_components, keeping Time and Amount as needed)

# 4. Random undersampling to balance classes (make genuine ≈ fraud in count)
X = df.drop('Class', axis=1)
y = df['Class']
rus = RandomUnderSampler(sampling_strategy=1.0, random_state=42)
X_res, y_res = rus.fit_resample(X, y)

# Combine the resampled features and labels into one DataFrame
df_resampled = pd.DataFrame(X_res, columns=X.columns)
df_resampled['Class'] = y_res

# Shuffle the rows of the resampled dataset (optional, to mix class order)
df_resampled = df_resampled.sample(frac=1, random_state=42).reset_index(drop=True)

# 5. Save the preprocessed balanced dataset
df_resampled.to_csv('preprocessed-creditcard.csv', index=False)
