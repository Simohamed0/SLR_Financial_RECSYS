import argparse
import csv
from collections import Counter
from pathlib import Path

FLAGS = ('code_available', 'dataset_proprietary', 'explainability',
         'market_context', 'portfolio_relevant', 'output_portfolio',
         'market_only_input', 'personalization_user_model')


def main():
    parser = argparse.ArgumentParser(description='Count all available yes/no study flags.')
    parser.add_argument('files', nargs='*', type=Path)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    files = args.files or [folder / 'corpus_data_extraction.csv',
                           folder / 'investment_studies_subset.csv']
    results = []
    for path in files:
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            columns = [name for name in FLAGS if name in (reader.fieldnames or [])]
            rows = list(reader)
        if not rows or not columns:
            raise ValueError(f'{path.name}: requires study rows and recognized flag columns.')
        for column in columns:
            counts = Counter((row.get(column) or '').strip().lower() for row in rows)
            if set(counts) - {'yes', 'no'}:
                raise ValueError(f'{path.name}/{column}: every value must be yes or no.')
            results.append((path.name, len(rows), column, counts['yes'], counts['no']))
    print(f'{"Dataset":<31} {"N":>3} {"Flag":<26} {"Yes":>4} {"Yes %":>8} {"No":>4} {"No %":>8}')
    for name, total, column, yes, no in results:
        print(f'{name:<31} {total:>3} {column:<26} {yes:>4} {100*yes/total:>7.2f}% '
              f'{no:>4} {100*no/total:>7.2f}%')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
