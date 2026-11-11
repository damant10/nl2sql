import hashlib
import pandas as pd


def get_df_hash_order_independent(df: pd.DataFrame) -> str:
    """Generates a single MD5 hash that ignores row order, but requires matching values/columns."""
    # Step 1: Get 64-bit integer hashes for every row (ignore index so row position doesn't matter)
    row_hashes = pd.util.hash_pandas_object(df, index=False)

    # Step 2: Sort the row hashes so order doesn't affect the final digest
    sorted_hashes = row_hashes.sort_values().values

    # Step 3: Combine sorted hashes into a single string and compute MD5
    return hashlib.md5(sorted_hashes.tobytes()).hexdigest()

if __name__ == "__main__":
    # Example Usage:
    df1 = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    #df1.sort_values(inplace=True)
    df2 = pd.DataFrame({"a": [1, 3, 2], "b": ["x", "z", "y"]})  
    #df2.sort_values(inplace=True)
    df3 = pd.DataFrame({"a": [1, 2, 9], "b": ["x", "y", "z"]})  # Different values

    print(df1)
    print(df2)
    print(get_df_hash_order_independent(df1) == get_df_hash_order_independent(df2))  # Returns True
    print(get_df_hash_order_independent(df1) == get_df_hash_order_independent(df3))  # Returns False