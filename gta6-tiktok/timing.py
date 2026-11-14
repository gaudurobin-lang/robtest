"""Calcule le minutage mot par mot des sous-titres à partir des fichiers de voix off."""
import re, wave, numpy as np
from script import LINES

BOUNDS = [0, 3.1, 6.5, 10.1, 16.1, 22.1, 28.1, 34.1, 40.2, 46.2, 52.2, 56.8, 60.0]


def speech_span(path):
    w = wave.open(path)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    env = np.abs(a)
    thr = env.max() * 0.04
    idx = np.where(env > thr)[0]
    return idx[0] / sr, idx[-1] / sr, len(a) / sr


def parse_caption(c):
    """Renvoie la liste (mot, est_mot_clé, ponctuation_forte_après)."""
    words = []
    kw = False
    for tok in c.split():
        start_kw = tok.startswith('*')
        if start_kw:
            kw = True
            tok = tok[1:]
        end_kw = tok.endswith('*')
        if end_kw:
            tok = tok[:-1]
        words.append([tok, kw])
        if end_kw:
            kw = False
    return words


def weight(w):
    if re.fullmatch(r'[\U0001F300-\U0001FAFF☀-➿]+', w):
        return 0
    digits = sum(ch.isdigit() for ch in w)
    if digits:
        return {"79,99": 30, "19": 7, "13": 5, "5": 4, "2": 3, "1": 2, "3": 4, "4": 5, "PS5": 9}.get(w.strip('€'), 4 * digits + 2)
    if w == '€':
        return 4
    if w in ('PS5',):
        return 9
    return max(len(w), 2) + 1


def build():
    """Liste de lignes: dict(start, end, words=[(texte, kw, t_debut)])."""
    out = []
    for i, (s, e, spoken, cap) in enumerate(LINES):
        a, b, _ = speech_span(f'tts/{i}.wav')
        words = parse_caption(cap)
        # numéro d'info "1".."5" collé au début : poids spécial
        ws = []
        for j, (w, k) in enumerate(words):
            ww = weight(w)
            if j == 0 and w in '12345' and len(words) > 3:
                ww = 5
            if w == 'PS5':
                ww = 9
            ws.append(ww)
        tot = sum(ws) or 1
        t = s + a
        dur = b - a
        timed = []
        for (w, k), ww in zip(words, ws):
            timed.append((w, k, t))
            t += dur * ww / tot
        out.append(dict(start=s, end=e, speech_end=s + b, words=timed))
    return out


if __name__ == '__main__':
    for l in build():
        print(round(l['start'], 2), [(w, round(t, 2)) for w, k, t in l['words']])
