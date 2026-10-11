import json, wave, numpy as np
w = wave.open(r"D:\genesis-vr\Genesis-1.1-2.wav"); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
db = lambda v: 20 * np.log10(max(v, 1e-9))
rms = lambda a, b: db(float(np.sqrt(np.mean(x[int(a*sr):int(b*sr)] ** 2))))
print("noise floor (0.3-3.5s):", round(rms(0.3, 3.5), 1), "dB | mid pause 155-157:", round(rms(155, 157), 1), "| late pause 374-376:", round(rms(374, 376), 1))
print("speech RMS part 1 (0-243s):", round(rms(0, 243.4), 1), "| part 2 (243-387s):", round(rms(243.4, 387), 1))
for a in range(0, 387, 30):
    seg = x[a*sr:(a+30)*sr]; print(f"{a:3d}-{a+30:3d}s peak {db(float(np.abs(seg).max())):6.1f} dB  rms {db(float(np.sqrt(np.mean(seg**2)))):6.1f} dB")
idx = np.where(np.abs(x) > 0.89)[0]
if len(idx):
    t = idx / sr; groups = [t[0]]
    for v in t:
        if v - groups[-1] > 0.5: groups.append(v)
    print("loud peaks (> -1 dB) near seconds:", [round(float(g), 1) for g in groups])
print("clipped samples (>=0.999):", int((np.abs(x) >= 0.999).sum()))
words = json.load(open(r"D:\genesis-vr\work\words.json"))
def show(a, b):
    print(f"{a}-{b}:", " ".join(f"{d['w']}({d['s']:.1f})" for d in words if a <= d['s'] <= b))
show(54, 61); show(98, 112); show(124, 131); show(214, 219); show(143, 148); show(157, 160); show(376, 385)
