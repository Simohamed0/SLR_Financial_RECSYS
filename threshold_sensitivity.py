import argparse
import csv
import re
import unicodedata
from collections import Counter

CRITERIA = ('problem_contribution_clarity', 'evaluation_soundness',
            'result_credibility', 'slr_relevance')


def identity(row):
    value = row['doi'].strip().lower()
    value = re.sub(r'^https?://(?:dx\.)?doi\.org/|^doi:\s*', '', value)
    if value:
        if not value.startswith('10.'):
            raise ValueError(f'Invalid DOI: {value}')
        return 'doi:' + value
    title = re.sub(r'\W+', '', unicodedata.normalize('NFKC', row['title']).casefold())
    if not title or not row['published year'].strip():
        raise ValueError('Missing DOI requires title and year.')
    return 'title:' + title + ':' + row['published year'].strip()


def load(path):
    records, missing = {}, 0
    with open(path, encoding='utf-8-sig', newline='') as f:
        for line, raw in enumerate(csv.DictReader(f), 2):
            row = {key.strip().lower(): value for key, value in raw.items()}
            key = identity(row)
            scores = tuple(float(row[name]) for name in CRITERIA)
            if not all(0 <= score <= 2 for score in scores):
                raise ValueError(f'{path}:{line}: item score outside 0–2.')
            if key in records:
                raise ValueError(f'{path}:{line}: repeated study identity {key}.')
            records[key] = scores
            missing += not row['doi'].strip()
    return records, missing


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--included', default='included.csv')
    p.add_argument('--excluded', default='exluded.csv')
    p.add_argument('--corpus', default='corpus_data_extraction.csv')
    a = p.parse_args()
    included, missing_i = load(a.included)
    excluded, missing_e = load(a.excluded)
    with open(a.corpus, encoding='utf-8-sig', newline='') as f:
        corpus_rows = list(csv.DictReader(f))
    corpus = {identity(row) for row in corpus_rows}
    if len(corpus) != len(corpus_rows) or corpus != included.keys():
        raise ValueError('Included studies do not match the extraction corpus.')
    overlap = included.keys() & excluded.keys()
    conflicts = [key for key in overlap if included[key] != excluded[key]]
    scores = {key: sum(value) for key, value in (excluded | included).items()}
    baseline = {key for key, score in scores.items() if score >= 5}
    if baseline != corpus:
        raise ValueError('Threshold >=5 does not reproduce the extraction corpus.')
    print(f'Included: {len(included)}; excluded records: {len(excluded)}; '
          f'unique pooled identities: {len(scores)}')
    print(f'Cross-file overlaps: {len(overlap)} ({len(conflicts)} conflicting); '
          'included-file appraisals take precedence.')
    print(f'Missing DOIs: {missing_i + missing_e}; title/year used as fallback.')
    for name, records in [('Included', included), ('Excluded, before overlap removal', excluded)]:
        print(f'{name} scores: {dict(sorted(Counter(map(sum, records.values())).items()))}')
    print('Threshold  Studies  Retained  Removed  Added  Change_%  Jaccard_%')
    for cutoff in (4, 5, 6, 7, 8):
        selected = {key for key, score in scores.items() if score >= cutoff}
        kept = len(selected & corpus)
        print(f'>={cutoff:<8} {len(selected):>7} {kept:>9} '
              f'{len(corpus-selected):>8} {len(selected-corpus):>6} '
              f'{100*(len(selected)/len(corpus)-1):>9.2f} '
              f'{100*kept/len(selected | corpus):>10.2f}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f'Cannot calculate sensitivity: {error}')
