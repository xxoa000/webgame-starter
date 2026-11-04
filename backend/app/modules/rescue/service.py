"""빈사 상태에서 구조 요청·NPC 구조·동일 맵 플레이어 구조·구조 포기를 처리한다."""
import math
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select
from ...database.base import utc_now
from ..characters.models import Character
from ..characters.repository import lock_owned, get_owned
from ..characters.vitals import limits, require_mobile, spend_stamina
from ..users.models import User
from ..exploration.models import Exploration
from .models import RescueRequest

NPC_RESCUE_SECONDS=60


def rescue_data(db, character_id):
    """구조 대기 상태와 남은 시간을 반환한다."""
    row=db.scalar(select(RescueRequest).where(RescueRequest.character_id==character_id))
    if not row:
        return None
    return {'id':row.id,'status':row.status,'due_at':row.due_at.isoformat()+'Z',
        'remaining_seconds':max(0,math.ceil((row.due_at-utc_now()).total_seconds())),
        'helper':'플레이어' if row.helper_user_id else '치료 NPC'}


def complete(db, character, row, helper_user_id=None):
    """구조 완료 시 HP 30%로 회복하고 탐색을 종료한다."""
    from ..exploration.service import append_event
    if not character.downed or character.status!='ready' or row.status!='waiting':
        return
    character.downed=False
    character.hp_current=max(1,math.ceil(limits(character)[0]*.30))
    row.status,row.helper_user_id='rescued',helper_user_id
    session=db.scalar(select(Exploration).where(Exploration.character_id==character.id).with_for_update())
    session.status,session.combat='ended',None
    session.version+=1
    append_event(session,'rescued',f"{'다른 플레이어' if helper_user_id else '치료 NPC'}가 구조했다. HP {character.hp_current}. 현장 탐색 종료.")


def resolve_due(db, character):
    """기한이 지난 NPC 요청을 서버 시각으로 한 번만 완료한다."""
    if not character.downed:
        return
    row=db.scalar(select(RescueRequest).where(RescueRequest.character_id==character.id).with_for_update())
    if row and row.status=='waiting' and row.due_at<=utc_now():
        complete(db,character,row)


def owner_action(db, user_id, action):
    """빈사 캐릭터 소유자의 요청만 허용하며 포기는 사망 기록으로 남긴다."""
    from ..exploration.service import state_data, append_event
    from ..combat.service import die
    character=lock_owned(db,user_id)
    if not character or character.status!='ready' or not character.downed:
        raise HTTPException(409,'빈사 상태가 아니야.')
    session=db.scalar(select(Exploration).where(Exploration.character_id==character.id).with_for_update())
    row=db.scalar(select(RescueRequest).where(RescueRequest.character_id==character.id).with_for_update())
    if action=='request':
        if not row or row.status!='waiting':
            if row is None:
                row=RescueRequest(character_id=character.id,map_id=session.map_id)
                db.add(row)
            row.map_id,row.status,row.helper_user_id=session.map_id,'waiting',None
            row.requested_at=utc_now();row.due_at=row.requested_at+timedelta(seconds=NPC_RESCUE_SECONDS)
            append_event(session,'rescue_request','구조 요청을 송신했다. 치료 NPC 또는 같은 맵의 플레이어를 기다린다.')
            session.version+=1
    else:
        if row and row.status=='waiting' and row.due_at<=utc_now():
            complete(db,character,row)
        else:
            if row:
                row.status='abandoned'
            append_event(session,'abandon','주무관이 구조를 포기했다. 피계약자의 마지막 상태를 기록한다.')
            die(db,character,session,append_event)
            session.version+=1
    db.commit()
    return state_data(db,session)


def nearby(db,user_id):
    """동일 맵에서 대기 중인 구조 요청만 공개한다."""
    character=get_owned(db,user_id)
    if not character or character.status!='ready' or character.downed:
        return []
    session=db.scalar(select(Exploration).where(Exploration.character_id==character.id,Exploration.status=='active'))
    if not session:
        return []
    rows=db.execute(select(RescueRequest,Character).join(Character,Character.id==RescueRequest.character_id)
        .where(RescueRequest.map_id==session.map_id,RescueRequest.status=='waiting',Character.downed.is_(True),
               Character.status=='ready',Character.user_id!=user_id,RescueRequest.due_at>utc_now())
        .order_by(RescueRequest.requested_at).limit(20)).all()
    return [{'id':request.id,'name':target.name,'remaining_seconds':max(0,math.ceil((request.due_at-utc_now()).total_seconds()))} for request,target in rows]


def help_player(db,user_id,request_id):
    """양쪽 계정을 ID 순으로 잠그고 동일 맵의 정상 캐릭터만 구조를 허용한다."""
    from ..exploration.service import append_event
    request=db.get(RescueRequest,request_id)
    target=db.get(Character,request.character_id) if request else None
    if not target or target.user_id==user_id:
        raise HTTPException(404,'구조 대상을 찾을 수 없어.')
    owner_id=target.user_id
    db.scalars(select(User).where(User.id.in_(sorted([user_id,owner_id]))).order_by(User.id).with_for_update()).all()
    helper=lock_owned(db,user_id);target=lock_owned(db,owner_id)
    require_mobile(helper)
    request=db.scalar(select(RescueRequest).where(RescueRequest.id==request_id).with_for_update().execution_options(populate_existing=True))
    session=db.scalar(select(Exploration).where(Exploration.character_id==helper.id).with_for_update())
    if not request or not target or request.character_id!=target.id or not target.downed or request.status!='waiting' or request.due_at<=utc_now():
        raise HTTPException(409,'이미 처리되었거나 NPC가 도착한 요청이야.')
    if not session or session.status!='active' or session.map_id!=request.map_id or session.combat or session.pending_item_id:
        raise HTTPException(409,'같은 맵에서 전투·물자 회수 대기 없이 탐색 중이어야 해.')
    spend_stamina(helper)
    session.turn+=1;session.version+=1
    complete(db,target,request,user_id)
    append_event(session,'rescue_help',f'{target.name}의 구조를 완료했다. 스태미나 -1.')
    db.commit()
    return {'rescued':True}
