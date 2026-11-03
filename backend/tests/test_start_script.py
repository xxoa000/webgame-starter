"""개발 실행 스크립트가 환경 파일을 덮어쓰지 않는지 검증한다."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def test_port_selection_does_not_write_environment_file(tmp_path, monkeypatch):
    """충돌 시 포트를 바꿔 실행해도 격리된 환경 파일의 원문을 보존한다."""
    script = Path(__file__).resolve().parents[2]/'scripts/start.py'
    spec = importlib.util.spec_from_file_location('safe_start', script)
    start = importlib.util.module_from_spec(spec); spec.loader.exec_module(start)
    monkeypatch.setattr(start, 'ROOT', tmp_path)
    # This is an isolated fixture file; no project environment file is opened.
    dummy = tmp_path/'.env'
    original = 'BACKEND_PORT=8000\nFRONTEND_PORT=5174\nMYSQL_PORT=3308\n'
    dummy.write_text(original)
    config = {'services': {name: {'ports':[{'target':inside,'published':str(outside)}]}
        for name, inside, outside in [('mysql',3306,3308),('backend',8000,8000),('frontend',5174,5174)]}}
    launched = []

    def fake_run(args, **kwargs):
        """Docker 실제 실행 없이 설정과 실행 환경을 검증한다."""
        if args == ['docker','compose','config','--format','json']:
            return SimpleNamespace(stdout=json.dumps(config))
        if args[:3] == ['docker','compose','up']:
            launched.append(kwargs['env'])
        return SimpleNamespace(stdout='')

    monkeypatch.setattr(start, 'run', fake_run)
    monkeypatch.setattr(start, 'available', lambda port: port != 8000)
    start.main()
    assert dummy.read_text() == original
    assert launched[0]['BACKEND_PORT'] == '8001'
    assert launched[0]['NEXT_PUBLIC_API_URL'] == 'http://localhost:8001'
