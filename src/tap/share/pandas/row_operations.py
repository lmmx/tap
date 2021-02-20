import pandas as pd
import numpy as np

def insert_replacement_rows(df, replacement_rows_dict):
    """
    A trick (suggested at https://stackoverflow.com/a/63736275/2668831)
    to insert rows with floating point row index to put them between
    the (standard, integer-valued) existing row indices.

    This is vectorised using numpy linspace (omitting the first and
    last entries of the linspace so as not to coincide with the pre-existing
    integer-valued row indices), and since the goal is replacement, this is
    followed finally by a call to `drop` each row index in the
    `replacement_rows_dict` (keys are star-expanded on the final line).
    """
    for row_idx, replacement_rows in replacement_rows_dict.items():
        #if row_idx == 19:
        #    breakpoint()
        n_rows_plus_2 = len(replacement_rows) + 2
        row_idx_range = np.linspace(row_idx, row_idx+1, n_rows_plus_2)[1:-1]
        for new_idx, replacement_row in zip(row_idx_range, replacement_rows):
            # Gives ValueError: cannot set a row with mismatched columns
            df.loc[new_idx] = pd.Series(
                dict(
                    zip(df.columns.to_list(), replacement_row)
                )
            )
    return df.drop(index=[*replacement_rows_dict]).sort_index().reset_index(drop=True)
