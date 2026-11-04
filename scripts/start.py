""" 포트 충돌을 확인하고 Docker Compose를 실행해주는 보조 스크립트. (선택사항) """

import json
import os
import socket
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 현재 파일의 한 단계 상위 폴더를 찾는다.
PORT_SETTINGS = (
    ("mysql", "MYSQL_PORT", 3306),
    ("backend", "BACKEND_PORT", 8000),
    ("frontend", "FRONTEND_PORT", 5174)
)


def run(args, **kwargs):
    """ 프로젝트 경로에서 외부 명령을 실행한다. """
    return subprocess.run(args, cwd=ROOT, check=True, text=True, **kwargs)


def available(port):
    """ 지정한 로컬 포트를 사용할 수 있는지 확인한다. """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", port))
        return True
    
    except OSError:
        return False


def main():
    """ 환경 파일을 보존하며 선택한 실행 환경으로 서비스를 시작한다. """
    env_file = ROOT / ".env"

    if not env_file.exists():
        raise RuntimeError(".env 파일을 먼저 복구해. 기존 DB 비밀번호를 사용해야 해.")
    
    config = json.loads(
        run(
            ["docker", "compose", "config", "--format", "json"],
            capture_output=True
        ).stdout
    )

    own_ids = {
        service: run(
            ["docker", "compose", "ps", "-q", service],
            capture_output=True
        ).stdout.strip()
        for service, _, _ in PORT_SETTINGS
    }
    
    ids = run(
        ["docker", "ps", "-q"], capture_output=True
    ).stdout.split()

    containers = json.loads(
        run(
            ["docker", "inspect", *ids],
            capture_output=True
        ).stdout
    ) if ids else []
    bindings = []

    for container in containers:
        for target, entries in (
            container.get("NetworkSettings", {}).get("Ports") or {}
        ).items():
            for entry in entries or []:
                bindings.append(
                    (
                        container["Id"],
                        target,
                        int(entry["HostPort"])
                    )
                )
    selected, reserved = {}, set()
    for service, variable, internal in PORT_SETTINGS:
        ports = config["services"][service].get("ports", [])

        start = int(
            next(
                port["published"]
                for port 
                in ports if int(port["target"]) == internal
            )
        )

        if not 1 <= start <= 65535:
            raise RuntimeError(f"{variable}는 1~65535여야 해.")
        
        own_ports, occupied = set(), set()

        for container_id, target, port in bindings:
            if own_ids[service] and container_id == own_ids[service] and target == f"{internal}/tcp":
                own_ports.add(port)
            else:
                occupied.add(port)

        chosen = next(
            (
                port for port in range(start, 65536)
                    if port not in reserved and port not in occupied and (
                        port in own_ports or available(port)
                    )
            ), None
        )
        
        if chosen is None:
            raise RuntimeError(f"{service}에 사용할 포트가 없어.")
        
        selected[variable] = str(chosen)
        reserved.add(chosen)
        print(f"{service}: {start} → {chosen}", flush=True)

    # 선택한 포트에 맞춰 프론트 연결 주소도 정한다.
    selected["NEXT_PUBLIC_API_URL"] = f"http://localhost:{selected['BACKEND_PORT']}"
    selected["FRONTEND_ORIGIN"] = f"http://localhost:{selected['FRONTEND_PORT']}"
    
    # 포트 선택값은 현재 Compose 프로세스에만 전달하고 .env는 저장하지 않는다.
    """ docker compose 실행. """
    run(
        ["docker", "compose", "up", "--build", "-d"],
        env={**os.environ, **selected}
    )
    
    print(
        f"화면: {selected['FRONTEND_ORIGIN']}\nAPI: {selected['NEXT_PUBLIC_API_URL']}/docs\nMySQL: 127.0.0.1:{selected['MYSQL_PORT']}"
    )


if __name__ == "__main__":
    try:
        main()
    except (
        RuntimeError,
        ValueError,
        StopIteration,
        OSError,
        subprocess.CalledProcessError
    ) as exc:
        raise SystemExit(f"실행 실패: {exc}")
