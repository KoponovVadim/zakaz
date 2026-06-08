import csv
from io import StringIO


def read_csv_rows(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    return list(csv.DictReader(StringIO(text)))
