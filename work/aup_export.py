"""Read an Audacity project (aup3/aup4 SQLite) and write each track's clips to WAV."""
import sqlite3, struct, sys, wave
import numpy as np

src, outdir = sys.argv[1], sys.argv[2]
con = sqlite3.connect(src)
cur = con.cursor()
row = cur.execute("select dict, doc from project").fetchone()
if row is None or row[1] is None:
    row = cur.execute("select dict, doc from autosave").fetchone()
buf = bytes(row[0]) + bytes(row[1])

names, events, pos, charsize = {}, [], 0, 1


def take(fmt):
    global pos
    v = struct.unpack_from("<" + fmt, buf, pos)
    pos += struct.calcsize("<" + fmt)
    return v if len(v) > 1 else v[0]


def text(n):
    global pos
    raw = buf[pos:pos + n]
    pos += n
    enc = {1: "utf-8", 2: "utf-16-le", 4: "utf-32-le"}[charsize]
    return raw.decode(enc, "replace")


while pos < len(buf):
    op = buf[pos]
    pos += 1
    if op == 0:
        charsize = take("B")
    elif op == 15:
        i, n = take("HH")
        names[i] = text(n)
    elif op == 1:
        events.append(("start", names[take("H")]))
    elif op == 2:
        events.append(("end", names[take("H")]))
    elif op == 3:
        i, n = take("Hi")
        events.append(("attr", names[i], text(n)))
    elif op in (4, 6):
        i, v = take("Hi")
        events.append(("attr", names[i], v))
    elif op == 5:
        i, v = take("HB")
        events.append(("attr", names[i], bool(v)))
    elif op == 7:
        i, v = take("Hq")
        events.append(("attr", names[i], v))
    elif op == 8:
        i, v = take("HI")
        events.append(("attr", names[i], v))
    elif op == 9:
        i, v, _ = take("Hfi")
        events.append(("attr", names[i], v))
    elif op == 10:
        i, v, _ = take("Hdi")
        events.append(("attr", names[i], v))
    elif op in (11, 12):
        n = take("i")
        text(n)
    elif op in (13, 14):
        pass
    elif op == 16:
        # aup4 addition: binary attribute (project thumbnail)
        i, n = take("Hi")
        pos += n
    else:
        raise SystemExit(f"unknown opcode {op} at {pos}")

tracks, stack, cur_tag = [], [], None
for ev in events:
    if ev[0] == "start":
        stack.append(ev[1])
        cur_tag = ev[1]
        if ev[1] == "wavetrack":
            tracks.append({"attrs": {}, "clips": []})
        elif ev[1] == "waveclip" and tracks:
            tracks[-1]["clips"].append({"attrs": {}, "blocks": []})
        elif ev[1] == "waveblock" and tracks and tracks[-1]["clips"]:
            tracks[-1]["clips"][-1]["blocks"].append({})
    elif ev[0] == "end":
        stack.pop()
        cur_tag = stack[-1] if stack else None
    else:
        _, k, v = ev
        if cur_tag == "wavetrack":
            tracks[-1]["attrs"][k] = v
        elif cur_tag == "waveclip":
            tracks[-1]["clips"][-1]["attrs"][k] = v
        elif cur_tag == "waveblock":
            tracks[-1]["clips"][-1]["blocks"][-1][k] = v

print("tags seen:", sorted({e[1] for e in events if e[0] == "start"}))
for ti, t in enumerate(tracks):
    a = t["attrs"]
    rate = int(a.get("rate", 0) or 0)
    print(f"TRACK {ti}: name={a.get('name')!r} rate={rate} channel={a.get('channel')} linked={a.get('linked')} mute={a.get('mute')} clips={len(t['clips'])}")
    for ci, c in enumerate(t["clips"]):
        ca = c["attrs"]
        ids = [b.get("blockid") for b in c["blocks"]]
        print(f"  clip {ci}: offset={ca.get('offset')} trimLeft={ca.get('trimLeft')} trimRight={ca.get('trimRight')} blocks={len(ids)} ids={ids[:4]}..{ids[-2:]}")
        if not ids or not rate:
            continue
        parts = []
        for b in ids:
            if b is None or b <= 0:
                continue
            fmt, blob = cur.execute("select sampleformat, samples from sampleblocks where blockid=?", (b,)).fetchone()
            if fmt != 262159:
                raise SystemExit(f"unexpected sample format {fmt}")
            parts.append(np.frombuffer(blob, dtype="<f4"))
        x = np.concatenate(parts)
        print(f"    samples={len(x)} seconds={len(x) / rate:.1f} peak={np.abs(x).max():.3f}")
        out = f"{outdir}\\track{ti}_clip{ci}.wav"
        with wave.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(3)
            w.setframerate(rate)
            y = np.clip(x, -1.0, 1.0)
            i32 = (y * 8388607.0).astype("<i4")
            w.writeframes(i32.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes())
        print("    wrote", out)
