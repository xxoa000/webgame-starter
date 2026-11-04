/* 화면 구석의 작은 소리 설정과 독립 볼륨 슬라이더를 표시한다. */
"use client";
import { useRef, useState } from "react";
import { useAudio } from "../../hooks/useAudio";
import styles from "./AudioSettings.module.css";

export function AudioSettingsButton() {
  /* 네이티브 대화상자로 포커스 이동·Escape 닫기·배경 클릭 차단을 지원한다. */
  const audio = useAudio();
  const dialog = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        className={styles.trigger}
        aria-label="소리 설정"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls="audio-settings"
        onClick={() => {
          dialog.current?.showModal();
          setOpen(true);
        }}
      >
        <span aria-hidden="true">⚙</span> 소리
      </button>
      <dialog
        ref={dialog}
        id="audio-settings"
        className={styles.dialog}
        aria-labelledby="audio-settings-title"
        onClose={() => setOpen(false)}
        onClick={(event) => {
          if (event.target === event.currentTarget) dialog.current?.close();
        }}
      >
        <div className={styles.panel}>
          <header>
            <h2 id="audio-settings-title">소리 설정</h2>
            <button
              type="button"
              aria-label="소리 설정 닫기"
              onClick={() => dialog.current?.close()}
            >
              ×
            </button>
          </header>
          <p>관제실과 탐색 지역에 맞는 배경음이 재생됩니다.</p>
          <label htmlFor="music-volume">
            배경음 <output>{audio.settings.music}%</output>
          </label>
          <input
            id="music-volume"
            type="range"
            min="0"
            max="100"
            step="1"
            value={audio.settings.music}
            onChange={(event) =>
              audio.setVolume("music", Number(event.target.value))
            }
          />
          <label htmlFor="effects-volume">
            효과음 <output>{audio.settings.effects}%</output>
          </label>
          <input
            id="effects-volume"
            type="range"
            min="0"
            max="100"
            step="1"
            value={audio.settings.effects}
            onChange={(event) =>
              audio.setVolume("effects", Number(event.target.value))
            }
          />
          <button
            type="button"
            className={styles.preview}
            onClick={() => audio.play("victory")}
          >
            효과음 미리 듣기
          </button>
          <small>0%는 음소거 · 설정은 이 브라우저에 저장됩니다.</small>
          {audio.error ? (
            <p role="status">
              일부 소리를 불러오지 못했습니다. 새로고침 후 다시 시도해 주세요.
            </p>
          ) : !audio.ready ? (
            <p role="status">첫 클릭이나 키 입력 후 소리가 재생됩니다.</p>
          ) : null}
        </div>
      </dialog>
    </>
  );
}
