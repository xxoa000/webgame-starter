"""사용 가능한 버전과 성격 조건으로 대사를 추첨하고 비공개 표현을 분리한다."""
import secrets
from collections import defaultdict
from string import Formatter
from sqlalchemy import select, or_, and_
from .models import ScriptPack, ScriptPackVersion, GameScript, GameScriptCondition, UserScriptPack, CharacterScriptPack
from ..characters.vitals import limits

LAYERS = ('SPEECH','THOUGHT','NARRATION')
ALLOWED_VARIABLES = {'character_name','map_name','item_name','monster_name'}


# 이벤트 생성 시에만 추첨하며 저장된 결과는 재추첨하지 않는다.
THOUGHT_CHANCE_PERCENT = 30

def render(content, context):
    """실행 코드나 속성 접근 없이 허용한 단순 치환 변수만 렌더링한다."""
    try:
        for _, field, spec, conversion in Formatter().parse(content):
            if field is not None and (field not in ALLOWED_VARIABLES or spec or conversion):
                return None
        return content.format_map(context)
    except (ValueError, KeyError):
        return None


def available_versions(db, character):
    """ 공통 승인본과 권한을 보유해 캐릭터에 적용한 버전만 허용한다. """

    common = set(db.scalars(
        select(ScriptPackVersion.id)
        .join(ScriptPack)
        .where(
            ScriptPack.kind == 'COMMON',
            ScriptPackVersion.status == 'APPROVED'
        )
    ).all())
    
    owned = set(db.scalars(
        select(UserScriptPack.version_id)
        .where(UserScriptPack.user_id == character.user_id)
    ).all())

    applied = db.execute(
        select(CharacterScriptPack, ScriptPackVersion, ScriptPack)
        .join(ScriptPackVersion, ScriptPackVersion.id == CharacterScriptPack.version_id)
        .join(ScriptPack, ScriptPack.id == ScriptPackVersion.pack_id)
        .where(
            CharacterScriptPack.character_id == character.id,
            ScriptPackVersion.status == 'APPROVED'
        )
    ).all()
    
    personal, preferred = set(), set()

    for link, version, pack in applied:
        if pack.kind == 'COMMON':
            continue

        if pack.author_id == character.user_id or version.id in owned:
            personal.add(version.id)

            if link.mode == 'PREFER':
                preferred.add(version.id)

    return common | personal, preferred


def matches(conditions, keyword_ids, map_id, hp_percent):
    """ 그룹 내부 AND와 그룹 사이 OR 규칙으로 조건을 판정한다. """

    if not conditions:
        return True
    groups = defaultdict(list)

    for condition in conditions:
        groups[condition.condition_group].append(condition)

    for group in groups.values():
        if all(
            (row.keyword_id is None or row.keyword_id in keyword_ids)
            and (row.map_id is None or row.map_id == map_id)
            and (row.hp_min_percent is None or hp_percent >= row.hp_min_percent)
            and (row.hp_max_percent is None or hp_percent <= row.hp_max_percent) 
            for row in group
        ):
            return True
    return False


def weighted_pick(candidates):
    """ 동일 우선순위 후보 중 양수 가중치로 한 개를 추첨한다. """

    pick = secrets.randbelow(
        sum(
            script.weight for script, _ in candidates
        )
    )

    for script, content in candidates:
        if pick < script.weight:
            return script, content
        pick -= script.weight

    return candidates[-1]


def select_output(db, character, event, map_id, context, history, action=None):
    """ 상황별 성격 대사를 층마다 선택해 저장 가능한 스냅샷을 반환한다. """

    if character.hp_current == 0 and event != 'death':
        return []
    
    version_ids, preferred = available_versions(db, character)

    if not version_ids:
        return []
    
    scripts = db.scalars(
        select(GameScript)
        .where(
            GameScript.version_id.in_(version_ids),
            GameScript.situation_code == event,
            GameScript.is_active == 1,
            or_(
                GameScript.action_code.is_(None),
                GameScript.action_code == action
            )
        )
        .order_by(GameScript.id)
    ).all()
    
    if not scripts:
        return []
    rows = db.scalars(
        select(GameScriptCondition)
        .where(GameScriptCondition.script_id
            .in_([script.id for script in scripts]))
    ).all()
    conditions = defaultdict(list)

    for row in rows:
        conditions[row.script_id].append(row)

    keywords = {link.keyword_id for link in character.personality}

    hp = max(0, character.hp_current or 0) / limits(character)[0] * 100
    choices = defaultdict(list)

    for script in scripts:
        if not matches(conditions[script.id], keywords, map_id, hp):
            continue

        content = render(script.content, context)

        if content is not None:
            choices[script.layer].append((script, content))

    versions = {
        row.id:row.version 
        for row 
        in db.scalars(
            select(ScriptPackVersion)
            .where(ScriptPackVersion.id.in_(version_ids))
        ).all()
    }
    result = []

    for layer in LAYERS:
        if layer == "THOUGHT" and secrets.randbelow(100) >= THOUGHT_CHANCE_PERCENT:
            continue

        candidates = choices[layer]

        if not candidates:
            continue

        exclusive = [
            row 
            for row 
            in candidates 
            if row[0].version_id in preferred
        ]

        if exclusive:
            candidates = exclusive

        priority = max(script.priority for script, _ in candidates)

        candidates = [
            (script, content) 
            for script, content 
            in candidates 
            if script.priority == priority
        ]
        recent = {
            output.get('script_id') 
            for record in history[-5:] 
            for output in record.get('scripts',[])
            if output.get('layer') == layer
        }
        fresh = [
            (script, content) 
            for script, content in candidates
            if script.id not in recent
        ]
        script, content = weighted_pick(fresh or candidates)

        result.append(
            {
                'script_id':script.id,
                'version_id':script.version_id,
                'version':versions[script.version_id],
                'layer':layer,
                'content':content
            }
        )
        
    return result


def public_output(outputs):
    """ 향후 상대방과의 통신을 위해 겉마음 대사만 추출하며 온라인 API는 제공하지 않는다. """
    return [
        row 
        for row
        in outputs 
        if row.get('layer') == 'SPEECH'
    ]
