from __future__ import annotations

import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create explainability features required by the new pipeline.
    Assumes the dataset includes at minimum columns:
      - User_ID, Location, Merchant_Category, Authentication_Method, Transaction_Timestamp
    """
    out = df.copy()

    # Ensure datetime
    if 'Transaction_Timestamp' in out.columns:
        out['Transaction_Timestamp'] = pd.to_datetime(out['Transaction_Timestamp'], errors='coerce')

    # is_unusual_location: different from user's most frequent location
    if {'User_ID', 'Location'}.issubset(out.columns):
        user_top_loc = (
            out.groupby('User_ID')['Location']
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else np.nan)
            .rename('UserTopLocation')
        )
        out = out.merge(user_top_loc, on='User_ID', how='left')
        out['is_unusual_location'] = (out['Location'] != out['UserTopLocation']).astype(int)
        out.drop(columns=['UserTopLocation'], inplace=True)

    # is_unusual_merchant: new merchant category in last 30 days for the user
    if {'User_ID', 'Merchant_Category', 'Transaction_Timestamp'}.issubset(out.columns):
        out = out.sort_values(['User_ID', 'Transaction_Timestamp'])
        window_days = pd.Timedelta(days=30)
        seen_flags = []
        # For performance, process per user
        for _, g in out.groupby('User_ID', sort=False):
            seen_recent: list[str] = []
            seen_times: list[pd.Timestamp] = []
            flags: list[int] = []
            for mc, ts in zip(g['Merchant_Category'].tolist(), g['Transaction_Timestamp'].tolist()):
                if pd.isna(ts):
                    flags.append(0)
                    continue
                while seen_times and ts - seen_times[0] > window_days:
                    seen_times.pop(0)
                    seen_recent.pop(0)
                flags.append(0 if mc in seen_recent else 1)
                seen_recent.append(mc)
                seen_times.append(ts)
            seen_flags.extend(flags)
        out['is_unusual_merchant'] = (
            pd.Series(seen_flags, index=out.sort_values(['User_ID','Transaction_Timestamp']).index)
            .sort_index()
            .reindex(out.index)
            .fillna(0)
            .astype(int)
        )

    # is_unusual_auth: weaker than user's typical method
    if {'User_ID', 'Authentication_Method'}.issubset(out.columns):
        strength = {
            'Password': 1,
            'OTP': 2,
            'Biometric': 3,
            'HardwareToken': 4,
        }
        out['__auth_strength'] = out['Authentication_Method'].map(strength).fillna(1)
        user_typical_strength = (
            out.groupby('User_ID')['__auth_strength']
            .agg(lambda s: int(round(s.mean())))
            .rename('UserTypicalAuthStrength')
        )
        out = out.merge(user_typical_strength, on='User_ID', how='left')
        out['is_unusual_auth'] = (out['__auth_strength'] < out['UserTypicalAuthStrength']).astype(int)
        out.drop(columns=['__auth_strength','UserTypicalAuthStrength'], inplace=True)

    return out


