import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

# Optional logger configuration (can also be configured at the root level of your app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MarketDataParser:
    def __init__(self) -> None:
        self._data: Dict[str, List[Dict[str, Union[str, float]]]] = {}

    def _clean_row(self, row: dict) -> dict:
        """Convert string values to numbers (int or float) when possible."""
        cleaned_row = {}
        for key, value in row.items():
            try:
                cleaned_row[key] = float(value) if '.' in str(value) else int(value)
            except (ValueError, TypeError):
                cleaned_row[key] = value
        return cleaned_row

    def _process_record(self, record: dict, pathfile: Path, default_ticker: Optional[str]) -> None:
        """Process a single data record (cleaning, ticker extraction, and storage)."""
        row_cleaned = self._clean_row(record)

        # Case-insensitive ticker extraction
        ticker = (
            row_cleaned.pop("Ticker", None)
            or row_cleaned.pop("ticker", None)
            or row_cleaned.pop("symbol", None)
            or row_cleaned.pop("Symbol", None)
            or default_ticker
        )

        if not ticker:
            raise ValueError(f"Cannot find ticker in file {pathfile}")

        ticker_str = str(ticker).upper()
        if ticker_str not in self._data:
            self._data[ticker_str] = []

        self._data[ticker_str].append(row_cleaned)

    def parse_csv_file(self, pathfile: Path, default_ticker: Optional[str] = None) -> None:
        """Parse a CSV file and update the internal data storage."""
        with open(file=pathfile, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self._process_record(row, pathfile, default_ticker)

    def parse_json_file(self, pathfile: Path, default_ticker: Optional[str] = None) -> None:
        """Parse a JSON file (handles both single dict objects and lists of dicts)."""
        with open(file=pathfile, mode="r", encoding="utf-8") as json_file:
            content = json.load(json_file)

        records = content if isinstance(content, list) else [content]
        for row in records:
            self._process_record(row, pathfile, default_ticker)

    def load_path(self, path_str: str) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        """Load files or directories, skipping corrupted ones while logging errors."""
        path = Path(path_str)

        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = list(path.glob("*.csv")) + list(path.glob("*.json"))
        else:
            raise FileNotFoundError(f"Path not found: {path_str}")

        for file in files:
            default_ticker = file.stem.upper()

            try:
                if file.suffix.lower() == ".csv":
                    self.parse_csv_file(file, default_ticker=default_ticker)
                elif file.suffix.lower() == ".json":
                    self.parse_json_file(file, default_ticker=default_ticker)
            except (json.JSONDecodeError, csv.Error) as e:
                logger.error(f"Failed to parse corrupted file {file}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while processing {file}: {e}")

        return self._data

    @property
    def data(self) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        return self._data