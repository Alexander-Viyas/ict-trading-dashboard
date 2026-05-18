import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from app.config import DATA_DIR
from app.models.schemas import OHLCV


class CSVLoader:
    @staticmethod
    def load_ohlcv(
        filepath: str,
        time_col: str = "time",
        open_col: str = "open",
        high_col: str = "high",
        low_col: str = "low",
        close_col: str = "close",
        volume_col: str = "volume",
        date_format: Optional[str] = None,
    ) -> pd.DataFrame:
        path = Path(filepath)
        if not path.is_absolute():
            path = DATA_DIR / filepath

        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")

        df = pd.read_csv(path)

        # Normalize column names
        rename_map = {}
        cols_lower = {c.lower(): c for c in df.columns}
        for target, src_key in [
            (time_col, time_col),
            (open_col, open_col),
            (high_col, high_col),
            (low_col, low_col),
            (close_col, close_col),
            (volume_col, volume_col),
        ]:
            if src_key not in df.columns and src_key.lower() in cols_lower:
                rename_map[cols_lower[src_key.lower()]] = target
        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        # Parse datetime
        if date_format:
            df[time_col] = pd.to_datetime(df[time_col], format=date_format)
        else:
            df[time_col] = pd.to_datetime(df[time_col])

        df.sort_values(by=time_col, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def list_available() -> List[str]:
        if not DATA_DIR.exists():
            return []
        csvs = list(DATA_DIR.rglob("*.csv"))
        return [str(p.relative_to(DATA_DIR)) for p in csvs]


csv_loader = CSVLoader()
