"""실제 환경 파일 없이 격리된 테스트용 JWT 서명키를 제공한다."""
import os
os.environ['JWT_SECRET_KEY'] = 'test-only-jwt-key-never-use-in-production-0123456789'
