"""Effective-date snapshots. Never substitute today's constituents for history."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from config import DATA_DIR


def normalize_ticker(value):
    return str(value).strip().upper().replace('.', '-')


class MembershipHistory:
    def __init__(self, snapshots, valid_through, metadata=None):
        self.snapshots = snapshots.copy()
        self.snapshots['date'] = pd.to_datetime(self.snapshots['date']).dt.normalize()
        self.snapshots = self.snapshots.sort_values('date').reset_index(drop=True)
        if self.snapshots.empty or self.snapshots.date.duplicated().any():
            raise ValueError('Empty/duplicate membership snapshot dates')
        self.valid_through = pd.Timestamp(valid_through).normalize()
        self.metadata = metadata or {}
        self._sets = []
        for value in self.snapshots.tickers:
            symbols = [normalize_ticker(x) for x in str(value).split(',') if str(x).strip()]
            if not symbols or len(symbols) != len(set(symbols)):
                raise ValueError('Empty/duplicate symbols in membership snapshot')
            self._sets.append(set(symbols))

    def as_of(self, date):
        date = pd.Timestamp(date).normalize()
        index = self.snapshots.date.searchsorted(date, side='right')-1
        if index < 0 or date > self.valid_through:
            raise ValueError(f'Membership history does not cover {date.date()}')
        return self._sets[index].copy(), self.snapshots.date.iloc[index]

    def union(self, formation_dates):
        result = set()
        for date in formation_dates:
            result.update(self.as_of(date)[0])
        return sorted(result)


def formation_dates(start, end):
    first = pd.Timestamp(start).to_period('M')
    last = pd.Timestamp(end).to_period('M')
    if not pd.Timestamp(end).is_month_end:
        last -= 1
    return pd.period_range(first-1, last-1, freq='M').to_timestamp('M')


def load_membership(path=None, valid_through=None):
    path = Path(path) if path else DATA_DIR/'membership'/'snapshots.csv'
    manifest_path = path.with_suffix('.metadata.json')
    metadata = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    through = valid_through or metadata.get('valid_through')
    if not through:
        raise ValueError('Membership CSV needs --membership-through or a .metadata.json valid_through')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if metadata.get('sha256') and digest != metadata['sha256']:
        raise ValueError('Membership snapshot hash does not match provenance manifest')
    metadata.update({'file': str(path.resolve()), 'sha256': digest, 'valid_through':str(pd.Timestamp(through).date())})
    return MembershipHistory(pd.read_csv(path), through, metadata)
