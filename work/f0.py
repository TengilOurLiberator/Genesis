"""Print the median speaking pitch of each audio file given (rough male/female check)."""
import subprocess, sys
import numpy as np

SR = 16000


def median_f0(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<f4")
    win, hop, f0s = 640, 320, []
    for i in range(0, len(x) - win, hop):
        fr = x[i:i + win] - x[i:i + win].mean()
        if np.sqrt(np.mean(fr ** 2)) < 0.02:
            continue
        ac = np.correlate(fr, fr, "full")[win - 1:]
        lo, hi = SR // 400, SR // 60
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45 * ac[0]:
            f0s.append(SR / k)
    return (float(np.median(f0s)) if f0s else 0.0), len(x) / SR


if __name__ == "__main__":
    for p in sys.argv[1:]:
        f, d = median_f0(p)
        print(f"{f:6.0f} Hz  {d:5.1f}s  {p}")
