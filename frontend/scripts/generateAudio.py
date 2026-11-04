"""외부 음원 없이 게임 전용 신스 음악과 효과음을 PCM WAV로 생성한다."""
from array import array
from pathlib import Path
import math
import random
import sys
import wave

RATE = 22050
OUTPUT = Path(__file__).resolve().parents[1] / 'public/audio'


def note(buffer, start, length, midi, volume, pad=False, slide=0):
    """부드러운 어택·릴리스와 배음으로 원음을 합성한다."""
    frequency = 440 * 2 ** ((midi - 69) / 12)
    count = int(length * RATE)
    phase = 0.0
    for index in range(count):
        at = int(start * RATE) + index
        if at >= len(buffer):
            at %= len(buffer)
        t = index / RATE
        envelope = min(1, t / (.35 if pad else .012)) * min(1, (length - t) / (.6 if pad else .07))
        envelope *= math.exp(-t / (length if pad else .35))
        phase += 2 * math.pi * frequency * 2 ** (slide * t / max(length, .001) / 12) / RATE
        tone = math.sin(phase) + .22 * math.sin(phase * 2) + .08 * math.sin(phase * 3)
        buffer[at] += tone * volume * envelope


def save(name, samples):
    """음량 여유를 유지한 16비트 모노 WAV를 저장한다."""
    peak = max(abs(value) for value in samples) or 1
    scale = min(1, .85 / peak)
    pcm = array('h', (round(max(-1, min(1, value * scale)) * 32767) for value in samples))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(OUTPUT / name), 'wb') as output:
        output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        output.writeframes(pcm.tobytes())


def music(name, exploring=False):
    """관제실은 느린 아르페지오, 탐색은 낮은 펄스로 32초 루프를 작곡한다."""
    samples = [0.0] * (RATE * 32)
    chords = [(45, 52, 59, 60), (41, 48, 55, 57), (48, 55, 62, 64), (43, 50, 57, 59)]
    for bar in range(8):
        chord = chords[bar % 4]
        for pitch in chord:
            note(samples, bar * 4, 4.8, pitch + (0 if exploring else 12), .025, pad=True)
        steps = 8 if exploring else 4
        for step in range(steps):
            start = bar * 4 + step * 4 / steps
            pitch = chord[(step * 3 + bar) % 4] + 24
            note(samples, start, .75, pitch, .045 if exploring else .035)
            note(samples, start + .28, .65, pitch, .012)
        for beat in range(4 if exploring else 2):
            note(samples, bar * 4 + beat * (1 if exploring else 2), .8, chord[0] - 12, .075)
    save(name, samples)


def effects():
    """클릭·조우·공격·피격·승리·후퇴 신호음을 만든다."""
    notes = {
        'click.wav': [(.0, .07, 85, .2, -7)],
        'encounter.wav': [(0, .22, 45, .19, 12), (.16, .3, 51, .16, 7)],
        'attack.wav': [(0, .15, 78, .22, -28), (.045, .1, 43, .18, -12)],
        'damage.wav': [(0, .2, 40, .22, -14), (.03, .18, 41, .1, -14)],
        'victory.wav': [(i * .12, .3, pitch, .17, 0) for i, pitch in enumerate([60, 64, 67, 72])],
        'flee.wav': [(i * .08, .14, pitch, .12, 0) for i, pitch in enumerate([72, 67, 60])],
    }
    for name, sequence in notes.items():
        samples = [0.0] * int(RATE * max(start + length + .02 for start, length, *_ in sequence))
        for start, length, pitch, volume, slide in sequence:
            note(samples, start, length, pitch, volume, slide=slide)
        if name in {'attack.wav', 'damage.wav'}:
            noise = random.Random(17)
            for index in range(min(len(samples), int(RATE * .08))):
                samples[index] += noise.uniform(-.07, .07) * (1 - index / (RATE * .08))
        save(name, samples)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    music('control-room.wav')
    music('exploration.wav', exploring=True)
    effects()
