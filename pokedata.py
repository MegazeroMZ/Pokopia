import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Set


def load_data(csv_path: str) -> List[Dict[str, Any]]:
    """Load CSV and normalize fields: combine specialties, favorites, habitats."""
    rows: List[Dict[str, Any]] = []
    p = Path(csv_path)
    with p.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            record: Dict[str, Any] = dict(r)
            # Normalize number
            num = record.get('Number', '')
            if num and num.startswith('#'):
                record['Number'] = num.lstrip('#')

            # Combine specialties (treat Specialty 1 and Specialty 2 the same)
            sp1 = (record.get('Specialty 1') or '').strip()
            sp2 = (record.get('Specialty 2') or '').strip()
            specialties: Set[str] = set()
            if sp1:
                specialties.add(sp1)
            if sp2:
                specialties.add(sp2)
            record['specialties'] = sorted(x for x in specialties if x)

            # Combine favorites Favorite 1..Favorite 6
            favs: List[str] = []
            for i in range(1, 7):
                key = f'Favorite {i}'
                v = (record.get(key) or '').strip()
                if v:
                    favs.append(v)
            record['favorites'] = favs

            # Combine habitats (Habitat 1/2/3 and Primary Location)
            habitats: Set[str] = set()
            for key in ['Primary Location', 'Habitat 1', 'Habitat 2', 'Habitat 3']:
                v = (record.get(key) or '').strip()
                if v:
                    habitats.add(v)
            record['habitats'] = sorted(x for x in habitats if x)

            # Ideal Habitat (prefer this for related-by-habitat queries)
            record['ideal_habitat'] = (record.get('Ideal Habitat') or '').strip()

            # Litter drop item (preserve both CSV key and a normalized key)
            record['Litter drop item'] = (record.get('Litter drop item') or '').strip()
            record['litter_drop_item'] = record['Litter drop item']

            # For convenience lowercased searchable name
            record['name_lower'] = (record.get('Name') or '').lower()

            rows.append(record)
    return rows


def search_by_name(rows: List[Dict[str, Any]], name: str) -> List[Dict[str, Any]]:
    q = name.strip().lower()
    if not q:
        return []
    return [r for r in rows if q in r.get('name_lower', '')]


def filter_by_specialty(rows: List[Dict[str, Any]], specialty: str) -> List[Dict[str, Any]]:
    q = (specialty or '').strip().lower()
    if not q:
        return rows
    # substring match for flexibility
    return [r for r in rows if any(q in s.lower() for s in r.get('specialties', []))]


def filter_by_favorite(rows: List[Dict[str, Any]], favorite: str) -> List[Dict[str, Any]]:
    q = (favorite or '').strip().lower()
    if not q:
        return rows
    # substring match for flexibility
    return [r for r in rows if any(q in f.lower() for f in r.get('favorites', []))]


def filter_by_ideal_habitat(rows: List[Dict[str, Any]], ideal: str) -> List[Dict[str, Any]]:
    q = (ideal or '').strip().lower()
    if not q:
        return rows
    # use substring match on the ideal_habitat field for flexibility
    return [r for r in rows if q in (r.get('ideal_habitat') or '').strip().lower()]


def sort_records(rows: List[Dict[str, Any]], column: str, reverse: bool = False) -> List[Dict[str, Any]]:
    if not column:
        return rows
    # If column was one of combined fields, handle specially
    key = column
    # Special-case numeric sort for the Number column when possible
    def to_sortable(v):
        if v is None:
            return ''
        if isinstance(v, list):
            return ','.join(v)
        s = str(v)
        # For the Number column, prefer numeric sorting but put any
        # 'E-xxx' prefixed entries after the normal list. We return a
        # tuple (group_priority, is_non_numeric, value) which sorts
        # numerically for typical numbers and puts E- entries later.
        if key.lower() == 'number':
            s_stripped = s.strip()
            is_e = s_stripped.upper().startswith('E-')
            # find the first group of digits
            m = re.search(r"\d+", s_stripped)
            if m:
                num = int(m.group())
                grp = 1 if is_e else 0
                # (group, is_non_numeric_flag, numeric value)
                return (grp, 0, num)
            # no digits -> sort lexicographically but keep E- grouped later
            grp = 1 if is_e else 0
            return (grp, 1, s_stripped.lower())
        elif s.isdigit():
            try:
                return int(s)
            except Exception:
                pass
        return s.lower()

    return sorted(rows, key=lambda r: to_sortable(r.get(key)), reverse=reverse)


def related_by_habitat(rows: List[Dict[str, Any]], record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return other rows that share the same Ideal Habitat with the given record.

    If the selected record has an `Ideal Habitat`, match other rows with the same
    `Ideal Habitat` (case-insensitive). If `Ideal Habitat` is empty, fall back
    to matching any shared item in the combined `habitats` field.
    """
    if not record:
        return []
    ideal = (record.get('ideal_habitat') or '').strip().lower()
    related = []
    if ideal:
        for r in rows:
            if r is record:
                continue
            if (r.get('ideal_habitat') or '').strip().lower() == ideal:
                related.append(r)
        return related

    # fallback: match any shared habitat
    habitats = set(h.lower() for h in record.get('habitats', []))
    if not habitats:
        return []
    for r in rows:
        if r is record:
            continue
        rh = set(h.lower() for h in r.get('habitats', []))
        if habitats & rh:
            related.append(r)
    return related


def group_by_favorite(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        for f in r.get('favorites', []):
            groups.setdefault(f, []).append(r)
    return groups
