"""서버에서 기본 스탯 5개를 합계 20으로 분배한다. 설정은 rules.py."""
import secrets
from .rules import CORE_STATS, STAT_TOTAL

def roll():
    # Uniformly sample positive integer compositions of 20 into five parts.
    """합계와 범위를 만족하는 기본 능력치를 추첨한다."""
    cuts = [0, *sorted(secrets.SystemRandom().sample(range(1, STAT_TOTAL), len(CORE_STATS)-1)), STAT_TOTAL]
    stats = {key: cuts[i+1]-cuts[i] for i, key in enumerate(CORE_STATS)}
    return stats
