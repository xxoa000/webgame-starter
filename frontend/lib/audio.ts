/* 로컬 음원 재생·버스별 볼륨·배경음 전환을 한 AudioContext에서 관리한다. */
export type SoundEffect =
  "click" | "encounter" | "attack" | "damage" | "victory" | "flee";
export type MusicScene = "control-room" | "exploration";
export type AudioSettings = { music: number; effects: number };
export const DEFAULT_AUDIO: AudioSettings = { music: 25, effects: 50 };
export const AUDIO_STORAGE_KEY = "bureau.audio.v1";

export function volume(value: unknown, fallback: number): number {
  /* 손상된 저장값과 범위 밖 입력은 안전한 음량으로 보정한다. */
  return typeof value === "number" && Number.isFinite(value)
    ? Math.round(Math.max(0, Math.min(100, value)))
    : fallback;
}

export class GameAudio {
  private context: AudioContext | null = null;
  private musicBus: GainNode | null = null;
  private effectsBus: GainNode | null = null;
  private buffers = new Map<string, Promise<AudioBuffer>>();
  private scene: MusicScene = "control-room";
  private playing: MusicScene | null = null;
  private music: { source: AudioBufferSourceNode; gain: GainNode } | null =
    null;
  private revision = 0;
  private settings = DEFAULT_AUDIO;
  private lastEffect = new Map<SoundEffect, number>();

  constructor(private reportError: () => void) {}

  async unlock() {
    /* 사용자 동작 안에서만 컨텍스트를 만들고 자동재생 제한을 해제한다. */
    if (!this.context) {
      this.context = new AudioContext();
      this.musicBus = this.context.createGain();
      this.effectsBus = this.context.createGain();
      this.musicBus.gain.value = this.settings.music / 100;
      this.effectsBus.gain.value = this.settings.effects / 100;
      this.musicBus.connect(this.context.destination);
      this.effectsBus.connect(this.context.destination);
      this.setVolumes(this.settings);
    }
    await this.context.resume();
    if (this.context.state !== "running") return false;
    void this.updateMusic();
    for (const effect of [
      "click",
      "encounter",
      "attack",
      "damage",
      "victory",
      "flee",
    ] as const) {
      void this.load(effect).catch(this.reportError);
    }
    return true;
  }

  setVolumes(settings: AudioSettings) {
    /* 0은 각 버스를 완전히 음소거한다. */
    this.settings = settings;
    if (!this.context) return;
    for (const [bus, value] of [
      [this.musicBus, settings.music],
      [this.effectsBus, settings.effects],
    ] as const) {
      if (!bus) continue;
      bus.gain.cancelScheduledValues(this.context.currentTime);
      bus.gain.setValueAtTime(bus.gain.value, this.context.currentTime);
      bus.gain.linearRampToValueAtTime(
        value / 100,
        this.context.currentTime + 0.03,
      );
    }
  }

  setScene(scene: MusicScene) {
    /* 같은 페이지 종류에서는 배경음 위치를 유지한다. */
    if (this.scene === scene) return;
    this.scene = scene;
    this.revision += 1;
    void this.updateMusic();
  }

  private load(name: string) {
    /* 실패한 요청은 캐시에서 지워 다음 사용자 동작에서 재시도한다. */
    let promise = this.buffers.get(name);
    if (!promise) {
      promise = fetch(`/audio/${name}.wav`)
        .then((response) => {
          if (!response.ok) throw new Error("Audio unavailable");
          return response.arrayBuffer();
        })
        .then((data) => this.context!.decodeAudioData(data))
        .catch((error) => {
          this.buffers.delete(name);
          throw error;
        });
      this.buffers.set(name, promise);
    }
    return promise;
  }

  private async updateMusic() {
    const context = this.context;
    if (!context || context.state !== "running" || this.playing === this.scene)
      return;
    const scene = this.scene;
    const revision = ++this.revision;
    try {
      const buffer = await this.load(scene);
      if (revision !== this.revision || context.state !== "running") return;
      const source = context.createBufferSource();
      const gain = context.createGain();
      source.buffer = buffer;
      source.loop = true;
      source.connect(gain);
      gain.connect(this.musicBus!);
      gain.gain.setValueAtTime(0, context.currentTime);
      gain.gain.linearRampToValueAtTime(1, context.currentTime + 0.5);
      if (this.music) {
        const old = this.music;
        old.gain.gain.cancelScheduledValues(context.currentTime);
        old.gain.gain.setValueAtTime(old.gain.gain.value, context.currentTime);
        old.gain.gain.linearRampToValueAtTime(0, context.currentTime + 0.5);
        old.source.stop(context.currentTime + 0.5);
      }
      source.onended = () => {
        source.disconnect();
        gain.disconnect();
      };
      source.start();
      this.music = { source, gain };
      this.playing = scene;
    } catch {
      this.reportError();
    }
  }

  async play(effect: SoundEffect, delay = 0) {
    /* 같은 효과의 과도한 중첩을 막고, 과거 기록은 호출부에서 제외한다. */
    const context = this.context;
    if (!context || context.state !== "running" || !this.settings.effects)
      return;
    const now = performance.now();
    if (now - (this.lastEffect.get(effect) ?? -Infinity) < 65) return;
    this.lastEffect.set(effect, now);
    try {
      const buffer = await this.load(effect);
      if (context.state !== "running") return;
      const source = context.createBufferSource();
      source.buffer = buffer;
      source.connect(this.effectsBus!);
      source.onended = () => source.disconnect();
      source.start(context.currentTime + delay);
    } catch {
      this.reportError();
    }
  }

  visibility(hidden: boolean) {
    /* 숨겨진 탭은 배경음과 효과음을 함께 일시정지한다. */
    if (!this.context || this.context.state === "closed") return;
    if (hidden) void this.context.suspend().catch(() => {});
    else
      void this.context
        .resume()
        .then(() => this.updateMusic())
        .catch(() => {});
  }

  dispose() {
    this.revision += 1;
    if (this.context) void this.context.close().catch(() => {});
  }
}
