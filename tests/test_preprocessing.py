import unittest
import pandas as pd
import numpy as np
from preprocessing import clean_data, scale_data, undersample_data, preprocess_pipeline

class TestPreprocessing(unittest.TestCase):
    def setUp(self):
        # Create a sample dataframe for testing
        data = {
            'Time': [1.0, 2.0, 3.0, 4.0, 5.0, 1.0], # Note the duplicate at end (if combined with other cols)
            'Amount': [100.0, 200.0, 300.0, 10.0, 20.0, 100.0],
            'V1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.1],
            'Class': [0, 0, 0, 1, 1, 0] # Imbalanced: 4 class 0, 2 class 1
        }
        # Add some duplicate row
        # Row 0: 1.0, 100.0, 0.1, 0
        # Row 5: 1.0, 100.0, 0.1, 0 -> Duplicate of Row 0
        self.df = pd.DataFrame(data)

        # Add a row with NaN
        self.df_with_nan = self.df.copy()
        self.df_with_nan.loc[6] = [np.nan, 100.0, 0.1, 0]

    def test_clean_data_removes_duplicates_and_nans(self):
        # Test removing NaN
        df_clean = clean_data(self.df_with_nan)
        self.assertFalse(df_clean.isnull().values.any(), "DataFrame contains NaNs after cleaning")

        # Test removing duplicates
        # self.df has 6 rows, row 5 is duplicate of row 0. So expected 5 rows.
        # self.df_with_nan has 7 rows. last is NaN.

        # clean_data on self.df (which has duplicate but no NaN)
        df_clean_dups = clean_data(self.df)
        self.assertEqual(len(df_clean_dups), 5, "Duplicates were not removed correctly")

        # Check that the duplicate row is indeed gone (or rather, one instance remains)
        # We started with 6 rows, should have 5.
        pass

    def test_scale_data(self):
        # Test scaling of Time and Amount
        # clean first to avoid nan/dup issues if any (though our fresh df is cleanish)
        df = self.df.iloc[:5].copy() # Use first 5 unique rows
        df_scaled = scale_data(df)

        # Check if Time and Amount are scaled (mean approx 0, std approx 1)
        # With small data, it won't be exactly 0 and 1, but values should change.
        # Let's check if they are different from original
        self.assertFalse(df_scaled['Time'].equals(df['Time']), "Time column was not scaled")
        self.assertFalse(df_scaled['Amount'].equals(df['Amount']), "Amount column was not scaled")

        # Check if other columns are untouched
        self.assertTrue(df_scaled['V1'].equals(df['V1']), "V1 column should not be scaled")
        self.assertTrue(df_scaled['Class'].equals(df['Class']), "Class column should not be scaled")

        # Verify mean is close to 0
        self.assertAlmostEqual(df_scaled['Time'].mean(), 0, places=1)
        self.assertAlmostEqual(df_scaled['Amount'].mean(), 0, places=1)

    def test_undersample_data(self):
        # clean first
        df = self.df.iloc[:5].copy()
        # Class counts: 0: 3, 1: 2.
        # Undersampling should reduce Class 0 to 2 to match Class 1.
        # Total rows should be 4.

        df_resampled = undersample_data(df)

        class_counts = df_resampled['Class'].value_counts()
        self.assertEqual(class_counts[0], class_counts[1], "Classes are not balanced")
        self.assertEqual(len(df_resampled), 4, "Incorrect number of rows after undersampling")

    def test_preprocess_pipeline(self):
        # Integration test
        # self.df has 6 rows (1 duplicate), 4 class 0, 2 class 1.
        # After cleaning: 5 rows (3 class 0, 2 class 1).
        # After scaling: same rows.
        # After undersampling: 4 rows (2 class 0, 2 class 1).

        df_processed = preprocess_pipeline(self.df)

        self.assertEqual(len(df_processed), 4)
        self.assertEqual(df_processed['Class'].value_counts()[0], 2)
        self.assertEqual(df_processed['Class'].value_counts()[1], 2)

        # Check that Time and Amount are scaled (just check they are float)
        self.assertTrue(np.issubdtype(df_processed['Time'].dtype, np.floating))
        self.assertTrue(np.issubdtype(df_processed['Amount'].dtype, np.floating))

if __name__ == '__main__':
    unittest.main()
