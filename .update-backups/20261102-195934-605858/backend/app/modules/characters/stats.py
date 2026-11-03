"""Server-authoritative stat allocation. Change ranges in app/config.py."""
import secrets
from ...config import CORE_STATS, STAT_TOTAL, STAT_RANGES

def roll():
    # Uniformly sample positive integer compositions of 20 into five parts.
    cuts = [0, *sorted(secrets.SystemRandom().sample(range(1, STAT_TOTAL), len(CORE_STATS)-1)), STAT_TOTAL]
    stats = {key: cuts[i+1]-cuts[i] for i, key in enumerate(CORE_STATS)}
    stats.update({key: low + secrets.randbelow(high-low+1)
                  for key, (low, high) in STAT_RANGES.items() if key not in CORE_STATS})
    return stats
