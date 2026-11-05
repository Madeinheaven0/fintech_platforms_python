from typing import Dict, List, Union
import csv

from src.fintech_cli.engine.domain import MarketEvent
from src.config import bitcoin_path


class DataHandler:
    """The owner of the financial data"""
    def __init__(self, path: str):
        self.path = path
        self._data = self.read_data()
        self._index = 0

    def _parse_row(
            self,
            data: List[Dict[str, Union[str, float]]]
    ) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        parsed_data = []

        for element in data:
            for key, value in element.items():
                try:
                    element[key] = float(value) if '.' in value else int(value)
                except:
                    element[key] = value
            parsed_data.append(element)

        return parsed_data

    def read_data(self):
        with open(self.path, mode='r', encoding='utf-8') as csvfile:
            data_dict = self._parse_row(list(csv.DictReader(csvfile, delimiter=',')))
        return data_dict

    def send_data(self) -> MarketEvent:
        data = self._data[self._index]
        self._index += 1

        return MarketEvent(
            timestamp = data['Date'],
            symbol = data['Asset_Name'],
            close_price = data['Adj Close'],
            high_price = data['High'],
            low_price = data['Low'],
            open_price = data['Open'],
            volume = data['Volume'],
        )

    @property
    def data(self) -> List[Dict[str, Union[str, float]]]:
        return self._data



if __name__ == "__main__":
    handler = DataHandler(bitcoin_path)
    handler.read_data()
    print(handler.data)