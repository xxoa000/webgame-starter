"""두 CSV로 초기 공통 대사를 트랜잭션 안에서 교체하며 개인 원고와 기록은 보존한다."""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from string import Formatter
from sqlalchemy import select, delete, func
from ...database import metadata as _metadata
from ...database.session import SessionLocal
from ..personality.models import PersonalityKeyword
from ..maps.models import Map
from .models import ScriptPack, ScriptPackVersion, GameScript, GameScriptCondition

CODE = re.compile(r'^[a-z][a-z0-9_]*$')
FIELDS = {'character_name', 'map_name', 'item_name', 'monster_name'}


def read_csv(path, required):
    """UTF-8 CSV의 헤더와 행을 검사하며 값의 위치가 밀린 파일은 거부한다."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f'{Path(path).name}: 필수 컬럼 누락')
        rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f'{Path(path).name}: 빈 파일 또는 잘못된 CSV 행')
    return rows


def integer(value, low=None, high=None):
    """정수와 허용 범위를 검사한다."""
    result = int(value)
    if low is not None and result < low or high is not None and result > high:
        raise ValueError(f'범위를 벗어난 값: {value}')
    return result


def code_value(value, maximum):
    """식별 코드에 영문 소문자·숫자·밑줄만 허용한다."""
    if not CODE.fullmatch(value) or len(value) > maximum:
        raise ValueError(f'코드는 영문 소문자 형식이어야 함: {value}')
    return value


def load_seed(scripts_path, conditions_path):
    """DB를 변경하기 전에 대사·조건·치환 변수와 파일 간 연결을 검증한다."""
    scripts = read_csv(scripts_path, {'code','situation_code','action_code','layer','content','priority','weight','is_active'})
    conditions = read_csv(conditions_path, {'script_code','condition_group','keyword_code','map_id','hp_min_percent','hp_max_percent'})
    codes = set()
    for row in scripts:
        code_value(row['code'],100)
        code_value(row['situation_code'],40)
        if row['action_code']:
            code_value(row['action_code'],40)
        if row['code'] in codes:
            raise ValueError('중복 대사 코드: '+row['code'])
        codes.add(row['code'])
        if row['layer'] not in {'SPEECH','THOUGHT','NARRATION'}:
            raise ValueError('잘못된 layer: '+row['layer'])
        if row['situation_code']=='death' and row['layer']!='NARRATION':
            raise ValueError('사망 상황에는 NARRATION만 사용')
        text = row['content']
        if not text.strip() or len(text.encode('utf-8'))>65000:
            raise ValueError('빈 본문 또는 너무 긴 본문: '+row['code'])
        if text.startswith(('"','“')) or text.endswith(('"','”')):
            raise ValueError('본문 양끝의 큰따옴표를 제거해: '+row['code'])
        for _, field, spec, conversion in Formatter().parse(text):
            if field is not None and (field not in FIELDS or spec or conversion):
                raise ValueError('허용되지 않은 치환 변수: '+row['code'])
        row['priority'] = integer(row['priority'])
        row['weight'] = integer(row['weight'],1)
        row['is_active'] = integer(row['is_active'],0,1)
    by_code = {row['code']:row for row in scripts}
    seen = set()
    for row in conditions:
        if row['script_code'] not in by_code:
            raise ValueError('연결할 대사가 없음: '+row['script_code'])
        if row.get('situation_code') and row['situation_code'] != by_code[row['script_code']]['situation_code']:
            raise ValueError('상황 코드 불일치: '+row['script_code'])
        code_value(row['keyword_code'],40)
        row['condition_group'] = integer(row['condition_group'],1)
        for field in ('map_id','hp_min_percent','hp_max_percent'):
            row[field] = integer(row[field],1 if field=='map_id' else 0,None if field=='map_id' else 100) if row[field] else None
        if row['hp_min_percent'] is not None and row['hp_max_percent'] is not None and row['hp_min_percent']>row['hp_max_percent']:
            raise ValueError('잘못된 HP 범위')
        identity=tuple(row.get(key) for key in ('script_code','condition_group','keyword_code','map_id','hp_min_percent','hp_max_percent'))
        if identity in seen:
            raise ValueError('중복 조건: '+row['script_code'])
        seen.add(identity)
    return scripts, conditions


def signature(event, action, layer, conditions):
    """기존 대사의 ID를 재사용하기 위한 상황·층·조건 조합을 만든다."""
    normalized = sorted((group,key.lower(),map_id or 0,low if low is not None else -1,high if high is not None else -1)
                        for group,key,map_id,low,high in conditions)
    return event, action or '', layer, tuple(normalized)


def sync_seed(db, scripts, conditions):
    """초기 공통 묶음 1판을 CSV와 일치시키고 동일 조건의 기존 ID는 재사용한다."""
    pack = db.scalar(select(ScriptPack).where(func.lower(ScriptPack.code)=='initial_common').with_for_update())
    if pack is None or pack.kind!='COMMON':
        raise ValueError('초기 공통 묶음이 없음. 먼저 alembic upgrade head를 실행해.')
    version = db.scalar(select(ScriptPackVersion).where(ScriptPackVersion.pack_id==pack.id,ScriptPackVersion.version==1).with_for_update())
    if version is None:
        raise ValueError('초기 공통 묶음 1판이 없음')
    keywords = db.scalars(select(PersonalityKeyword).order_by(PersonalityKeyword.id).with_for_update()).all()
    keyword_by_code = {}
    for keyword in keywords:
        normalized = keyword.code.lower()
        if normalized in keyword_by_code:
            raise ValueError('대소문자만 다른 키워드 코드가 중복됨: '+normalized)
        keyword_by_code[normalized] = keyword
    incoming = defaultdict(list)
    for row in conditions:
        keyword = keyword_by_code.get(row['keyword_code'])
        if keyword is None:
            raise ValueError('DB에 없는 키워드: '+row['keyword_code'])
        if row.get('keyword_name') and row['keyword_name'] != keyword.name:
            raise ValueError('키워드 코드와 이름 불일치: '+row['keyword_code'])
        if row['map_id'] is not None and db.get(Map,row['map_id']) is None:
            raise ValueError('DB에 없는 맵 ID')
        incoming[row['script_code']].append(row)
    existing = db.scalars(select(GameScript).where(GameScript.version_id==version.id).order_by(GameScript.id).with_for_update()).all()
    old_ids = [row.id for row in existing]
    old_conditions = db.scalars(select(GameScriptCondition).where(GameScriptCondition.script_id.in_(old_ids))).all() if old_ids else []
    old_by_id = defaultdict(list)
    by_keyword_id = {row.id:row for row in keywords}
    for row in old_conditions:
        key = by_keyword_id[row.keyword_id].code if row.keyword_id is not None else ''
        old_by_id[row.script_id].append((row.condition_group,key,row.map_id,row.hp_min_percent,row.hp_max_percent))
    groups = defaultdict(list)
    for row in existing:
        groups[signature(row.situation_code,row.action_code,row.layer,old_by_id[row.id])].append(row)
    existing_by_code = {row.code:row for row in existing}
    desired_codes = {row['code'] for row in scripts}
    collisions = db.scalars(select(GameScript).where(func.lower(GameScript.code).in_(desired_codes),GameScript.version_id!=version.id)).all()
    if collisions:
        raise ValueError('다른 원고 묶음에서 사용 중인 코드: '+collisions[0].code)
    assignments=[]
    used=set()
    # 같은 코드가 존재하면 조건 변경 여부와 관계없이 해당 ID를 우선 유지한다.
    for row in scripts:
        match=existing_by_code.get(row['code'])
        if match is not None:
            used.add(match.id)
        assignments.append([row,match])
    for assignment in assignments:
        row,match=assignment
        if match is not None:
            continue
        condition_values=[(c['condition_group'],c['keyword_code'],c['map_id'],c['hp_min_percent'],c['hp_max_percent']) for c in incoming[row['code']]]
        candidates=groups[signature(row['situation_code'],row['action_code'],row['layer'],condition_values)]
        match=next((candidate for candidate in candidates if candidate.id not in used),None)
        if match is not None:
            used.add(match.id)
        assignment[1]=match
    if old_ids:
        db.execute(delete(GameScriptCondition).where(GameScriptCondition.script_id.in_(old_ids)))
    # 코드 교환 중 UNIQUE 충돌을 피하며 트랜잭션 밖에는 임시 값이 보이지 않는다.
    from uuid import uuid4
    temporary_prefix='seed_tmp_'+uuid4().hex+'_'
    for row in existing:
        row.code=temporary_prefix+str(row.id)
    db.flush()
    for row in existing:
        if row.id not in used:
            db.delete(row)
    referenced = {row['keyword_code'] for row in conditions}
    for key in referenced:
        keyword_by_code[key].code=key
    pack.code='initial_common'
    version.status='APPROVED'
    inserted=updated=0
    for values,script in assignments:
        if script is None:
            script=GameScript(version_id=version.id)
            db.add(script)
            inserted+=1
        else:
            updated+=1
        for key in ('code','situation_code','layer','content','priority','weight','is_active'):
            setattr(script,key,values[key])
        script.action_code=values['action_code'] or None
        db.flush()
        for condition in incoming[values['code']]:
            db.add(GameScriptCondition(script_id=script.id,condition_group=condition['condition_group'],
                keyword_id=keyword_by_code[condition['keyword_code']].id,map_id=condition['map_id'],
                hp_min_percent=condition['hp_min_percent'],hp_max_percent=condition['hp_max_percent']))
    db.flush()
    return {'updated':updated,'inserted':inserted,'removed':len(existing)-len(used),
            'scripts':len(scripts),'conditions':len(conditions),'pack':'initial_common','version':1}


def main():
    """컨테이너에 전달한 CSV를 읽고 성공한 경우에만 한 번에 반영한다."""
    parser=argparse.ArgumentParser(description='CSV로 초기 공통 대사 교체')
    parser.add_argument('--scripts',default='/seed/SCRIPTS-SEED.csv')
    parser.add_argument('--conditions',default='/seed/SCRIPT-CONDITIONS-SEED.csv')
    args=parser.parse_args()
    scripts,conditions=load_seed(args.scripts,args.conditions)
    with SessionLocal() as db:
        with db.begin():
            result=sync_seed(db,scripts,conditions)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
