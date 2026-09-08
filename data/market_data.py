import csv
import json
from pathlib import Path
from typing import List, Dict, Union



class MarketDataParser:
    def __init__(self) -> None:
        self._data: Dict[str, List[Dict[str, Union[str, float]]]] = {}

    def _clean_row(self, row: dict) -> dict:
        """
        Convert a string into number if it's possible
        :param row: the dictionary to convert
        :return: the cleaned dictionary
        """
        cleaned_row = {}
        for key, value in row.items():
            try:
                cleaned_row[key] = float(value) if '.' in str(value) else int(value)
            except (ValueError, TypeError):
                cleaned_row[key] = value

        return cleaned_row

    def parse_csv_file(self, pathfile: Path, default_ticker = None):
        """
        Parse a CSV file and convert it into a list of dictionaries (multi-asset or mono-assets)
        :param pathfile:
        :param default_ticker:
        :return:
        """
        with open(file=pathfile, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                row_cleaned = self._clean_row(row)

                ticker = row_cleaned.pop("Ticker", None) or row_cleaned.pop("symbol", None) or default_ticker

                if not ticker:
                    raise ValueError("Cannot find ticker in the CSV file")

                ticker = str(ticker).upper()
                if ticker not in self.data:
                    self.data[ticker] = []
                    self.data[ticker].append(row_cleaned)

    def parse_json_file(self, pathfile: Path, default_ticker = None):
        """Parse a JSON file and convert it into a list of dictionaries (multi-objects or mono-object)"""
        with open(file=pathfile, mode="r", encoding="utf-8") as json_file:
            content = json.load(json_file)

            records = content if isinstance(content, list) else [content]

            for row in records:
                row_cleaned = self._clean_row(row)

                ticker = row_cleaned.pop("Ticker", None) or row_cleaned.pop("symbol", None) or default_ticker

                if not ticker:
                    raise ValueError("Cannot find ticker in the JSON file")

                ticker = str(ticker).upper()

                if ticker not in self.data:
                    self.data[ticker] = []
                self.data[ticker].append(row_cleaned)

    def load_path(self, path_str: str):
        """Load the files and convert them"""
        path = Path(path_str)

        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = list(path.glob("*.csv")) + list(path.glob("*.json"))
        else:
            raise FileNotFoundError(f"Not found the path : {path_str}")

        for file in files:
            # Si the name of the file is the style 'AAPL.csv', we extract 'AAPL' as the default ticker
            default_ticker = file.stem.upper()

            if file.suffix.lower() == ".csv":
                self.parse_csv_file(file, default_ticker=default_ticker)
            elif file.suffix.lower() == ".json":
                self.parse_json_file(file, default_ticker=default_ticker)

    @property
    def data(self) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        return self._data


if __name__ == "__main__":
    parser = MarketDataParser()

    # load a unique multi-assets file or a complete folder
    # parser.load_path("donnees_marche.csv")
    # parser.load_path("./dossier_fichiers_actifs/")

    # aapl_prices = parser.data.get("AAPL", [])
    # print(f"Number of candle for AAPL : {len(aapl_prices)}")