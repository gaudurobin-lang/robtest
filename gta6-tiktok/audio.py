"""Bande-son : musique synthwave/phonk générée, voix off, effets sonores, ducking."""
import wave, numpy as np
from timing import build, BOUNDS
from render import CUTS, word_t

SR = 44100
DUR = 60.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
LINES = build()

BPM = 100
BEAT = 60 / BPM
ORIGIN = 10.1  # le « drop » tombe ici


def tone_saw(f, n, det=(0.0,)):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in det:
        ph = (t * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / len(det)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * np.asarray(cutoff) / SR)
    y = np.zeros_like(x)
    prev = 0.0
    if np.ndim(a) == 0:
        a = np.full(len(x), a)
    for i in range(len(x)):
        prev = (1 - a[i]) * x[i] + a[i] * prev
        y[i] = prev
    return y


def lp_fast(x, cutoff):
    # filtre passe-bas d'ordre 1 vectorisé par FFT (cutoff fixe)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def hp_fast(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (f / cutoff) ** 2 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def env_exp(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


# ------------------------------------------------------------ instruments
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env_exp(n, 0.18)
    s += 0.3 * rng.standard_normal(n) * env_exp(n, 0.004)
    return np.tanh(s * 1.8)


def snare():
    n = int(0.3 * SR)
    noise = hp_fast(rng.standard_normal(n), 1500) * env_exp(n, 0.07)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * env_exp(n, 0.05)
    return 0.6 * noise + 0.5 * body


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    return hp_fast(rng.standard_normal(n), 7000) * env_exp(n, 0.06 if open_ else 0.012)


def cowbell():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 540 * t)) + np.sign(np.sin(2 * np.pi * 800 * t))
    s = lp_fast(s, 3000) * env_exp(n, 0.07)
    return s * 0.5


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


# Am - F - C - G (une mesure chacun)
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
ROOTS = [45, 41, 36, 43]


def bar_index(t):
    return int(np.floor((t - ORIGIN) / (4 * BEAT)))


def section(t):
    if t < 10.1:
        return 'intro'
    if t < 40.2:
        return 'drop'
    if t < 52.2:
        return 'break'
    if t < 56.8:
        return 'drop'
    return 'outro'


def music():
    L = np.zeros(N)
    R = np.zeros(N)
    K, S, Hh, C = kick(), snare(), hat(), cowbell()
    Ho = hat(True)
    # grille de doubles-croches
    step = BEAT / 4
    k0 = int(np.ceil((0 - ORIGIN) / step))
    k1 = int((DUR - ORIGIN) / step)
    for k in range(k0, k1 + 1):
        t = ORIGIN + k * step
        if t < 0 or t >= DUR:
            continue
        sec = section(t)
        pos = k % 16  # position dans la mesure
        if sec == 'drop':
            if pos % 4 == 0:
                add(L, K, t, 0.9); add(R, K, t, 0.9)
            if pos in (4, 12):
                add(L, S, t, 0.55); add(R, S, t, 0.55)
            if pos % 2 == 0:
                add(L, Hh, t, 0.18); add(R, Hh, t, 0.22)
            if pos % 4 == 2:
                add(L, Ho, t, 0.1); add(R, Ho, t, 0.08)
            if pos in (0, 3, 6, 8, 10, 11, 14):  # cowbell phonk
                b = bar_index(t) % 4
                add(L, C, t, 0.14 * (1.0 if b % 2 == 0 else 0.8)); add(R, C, t, 0.12)
        elif sec == 'intro':
            if t >= 3.1 and pos % 2 == 0:
                add(L, Hh, t, 0.12); add(R, Hh, t, 0.14)
            if pos in (0, 8) or (t >= 6.5 and pos % 4 == 0):
                add(L, K, t, 0.55); add(R, K, t, 0.55)
            if t >= 8.5 and t < 10.1:  # roulement de caisse claire
                if pos % (2 if t < 9.3 else 1) == 0:
                    g = 0.15 + 0.35 * (t - 8.5) / 1.6
                    add(L, S, t, g); add(R, S, t, g)
        elif sec == 'break':
            if pos == 0:
                add(L, K, t, 0.7); add(R, K, t, 0.7)
            if pos == 8:
                add(L, S, t, 0.35); add(R, S, t, 0.35)
            if pos % 2 == 0:
                add(L, Hh, t, 0.12); add(R, Hh, t, 0.14)
        elif sec == 'outro':
            if pos % 4 == 0:
                add(L, K, t, 0.7); add(R, K, t, 0.7)
            if pos % 2 == 0 or t > 58.5:
                g = 0.15 + 0.3 * (t - 56.8) / 3.2
                add(L, S, t, g * 0.6); add(R, S, t, g * 0.6)
        # basse en croches
        if sec in ('drop', 'outro') and pos % 2 == 0:
            b = bar_index(t) % 4
            f = note(ROOTS[b] - 12 + (12 if pos % 4 == 2 else 0))
            n = int(step * 2 * SR * 0.95)
            s = tone_saw(f, n, (0, 0.01)) * env_exp(n, 0.15)
            s = np.tanh(lp_fast(s, 600) * 2.5) * 0.25
            sub = np.sin(2 * np.pi * note(ROOTS[b] - 12) * np.arange(n) / SR) * env_exp(n, 0.25) * 0.25
            add(L, s + sub, t); add(R, s + sub, t)
        # arpège lead
        if (sec == 'drop' and t >= 16.1) or sec == 'outro':
            b = bar_index(t) % 4
            seq = list(CHORDS[b]) + [CHORDS[b][0] + 12]
            m = seq[[0, 1, 2, 3, 2, 1, 2, 3][pos % 8]] + 12
            n = int(step * SR)
            s = tone_saw(note(m), n, (0, 0.006, -0.006)) * env_exp(n, 0.06)
            s = lp_fast(s, 3500) * 0.09
            add(L, s, t, 1.0 if pos % 2 else 0.6); add(R, s, t, 0.6 if pos % 2 else 1.0)
    # nappe d'accords (toute la durée), filtre qui s'ouvre dans l'intro
    bar = 4 * BEAT
    b0 = int(np.floor((0 - ORIGIN) / bar))
    for b in range(b0, int((DUR - ORIGIN) / bar) + 1):
        t = ORIGIN + b * bar
        n = int(bar * SR) + int(0.05 * SR)
        ch = CHORDS[b % 4]
        s = sum(tone_saw(note(m), n, (0, 0.004, -0.005)) for m in ch) / 3
        sec = section(max(t, 0))
        cut = 900 if sec == 'intro' else (2200 if sec != 'break' else 1400)
        s = lp_fast(s, cut)
        a = np.minimum(1, np.arange(n) / (0.04 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.05 * SR))
        g = 0.16 if sec != 'break' else 0.2
        add(L, s * a * g, t); add(R, np.roll(s, 300) * a * g, t)
    # riser avant le drop + avant la boucle
    for (t0, t1, g) in [(6.6, 10.1, 0.45), (57.2, 60.0, 0.35)]:
        n = int((t1 - t0) * SR)
        x = np.arange(n) / n
        noise = hp_fast(rng.standard_normal(n), 2500) * (x ** 2) * g
        sweep = np.sin(2 * np.pi * np.cumsum(200 + 1800 * x ** 2) / SR) * x ** 3 * 0.12
        add(L, noise + sweep, t0); add(R, noise + sweep, t0)
    # coupure courte juste avant le drop (effet « silence puis boom »)
    i0, i1 = int(9.95 * SR), int(10.1 * SR)
    L[i0:i1] *= np.linspace(1, 0.15, i1 - i0)
    R[i0:i1] *= np.linspace(1, 0.15, i1 - i0)
    return np.stack([L, R])


# ------------------------------------------------------------ effets
def whoosh(dur=0.45, strong=True):
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    # passe-bande glissant approximé : mélange de deux filtrages
    lo = lp_fast(noise, 900)
    hi = hp_fast(noise, 2500)
    s = lo * (1 - x) + hi * x
    e = np.sin(np.pi * x) ** 2
    return s * e * (0.55 if strong else 0.18)


def boom():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 32 + 70 * np.exp(-t / 0.08)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.55)
    s += lp_fast(rng.standard_normal(n), 400) * env_exp(n, 0.15) * 0.6
    crash = hp_fast(rng.standard_normal(n), 5000) * env_exp(n, 0.5) * 0.25
    return np.tanh(s * 2.2) * 0.9 + crash


def kaching():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    click = np.zeros(n)
    m = int(0.03 * SR)
    click[:m] = hp_fast(rng.standard_normal(n), 2000)[:m] * np.linspace(1, 0, m) * 0.8
    bell = np.zeros(n)
    st = int(0.08 * SR)
    tb = t[: n - st]
    for f, a in [(2093, 0.5), (2637, 0.35), (3136, 0.3), (4186, 0.2)]:
        bell[st:] += a * np.sin(2 * np.pi * f * tb) * np.exp(-tb / 0.35)
    return (click + bell * 0.6) * 0.8


def pop_sfx():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 5000 * t) * t) * env_exp(n, 0.02) * 0.3


# ------------------------------------------------------------ voix
def load_voice(i):
    w = wave.open(f'tts/{i}.wav')
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    tt = np.arange(int(len(a) * SR / sr)) / SR
    return np.interp(tt, np.arange(len(a)) / sr, a)


def main():
    mus = music()
    voice = np.zeros(N)
    for i, l in enumerate(LINES):
        v = load_voice(i)
        v = v / (np.abs(v).max() + 1e-9) * 0.9
        add(voice, v, l['start'])
    # léger « présence » sur la voix
    voice = voice + 0.25 * hp_fast(voice, 3000)
    # ducking de la musique sous la voix
    env = np.abs(voice)
    k = int(0.12 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    env = np.clip(env / (env.max() * 0.25), 0, 1)
    duck = 1 - 0.5 * env
    mus *= duck
    sfx = np.zeros((2, N))
    for c in CUTS:
        strong = any(abs(c - b) < 0.01 for b in BOUNDS[1:-1])
        w = whoosh(0.45 if strong else 0.3, strong)
        add(sfx[0], w, c - 0.25); add(sfx[1], np.roll(w, 200), c - 0.25)
    b = boom()
    for t0, g in [(10.1, 1.0), (0.0, 0.55)]:
        add(sfx[0], b, t0, g); add(sfx[1], b, t0, g)
    kc = kaching()
    tp = word_t(4, '79,99')
    add(sfx[0], kc, tp, 0.9); add(sfx[1], kc, tp + 0.01, 0.9)
    # petite « bass boost » sur la date (deuxième boum plus court)
    tb = word_t(3, '19')
    add(sfx[0], b[: int(0.6 * SR)], tb, 0.5); add(sfx[1], b[: int(0.6 * SR)], tb, 0.5)
    p = pop_sfx()
    for seg in range(3, 8):
        add(sfx[0], p, BOUNDS[seg] + 0.05); add(sfx[1], p, BOUNDS[seg] + 0.05)
    mix = mus * 0.42 + sfx * 0.55 + voice[None, :] * 1.0
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix /= np.abs(mix).max() * 1.02
    out = (mix.T * 32767).astype(np.int16)
    w = wave.open('mix.wav', 'wb')
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())
    w.close()


if __name__ == '__main__':
    main()
