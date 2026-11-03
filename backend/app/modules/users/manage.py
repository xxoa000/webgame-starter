"""기존 계정의 권한을 로컬 운영 명령으로 설정한다. 비밀번호나 환경 파일은 수정하지 않는다."""
import argparse
from sqlalchemy import select
from ...database.session import SessionLocal
from ...database import metadata as _metadata
from .models import User


def main():
    """지정한 기존 계정의 권한만 갱신한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--auth', type=int, choices=[0, 1, 9], required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == args.username.lower()).with_for_update())
        if not user:
            parser.error('존재하는 계정을 지정해야 합니다.')
        user.auth = args.auth
        db.commit()
        print(f'{user.username}: auth={user.auth}')


if __name__ == '__main__':
    main()
