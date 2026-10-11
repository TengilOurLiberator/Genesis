"""Watch the intro without a headset: start a plain desktop client, join the local server,
choose Adam, and save screenshots of the game window at chosen moments.

The server must be running with online-mode=false (the test client has no account).

    python tools\\visual_test.py [--rate 3] [--ticks 100,900,...]
"""
import argparse, ctypes, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rcon import Rcon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(os.environ["APPDATA"], ".minecraft")
JAVA = os.path.join(os.environ["LOCALAPPDATA"], r"Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime"
                    r"\java-runtime-epsilon\windows-x64\java-runtime-epsilon\bin\java.exe")
GAME = os.path.join(ROOT, "work", "testgame")
SHOTS = os.path.join(ROOT, "work", "shots")
NAME = "Tester"


def launch():
    v = json.load(open(os.path.join(MC, "versions", "26.3", "26.3.json")))
    ok = lambda lib: all(r.get("os", {}).get("name") in (None, "windows") and "arch" not in r.get("os", {})
                         for r in lib.get("rules", [{}]) if r.get("action") == "allow")
    cp = [os.path.join(MC, "libraries", *lib["downloads"]["artifact"]["path"].split("/"))
          for lib in v["libraries"] if ok(lib) and "artifact" in lib.get("downloads", {})]
    cp.append(os.path.join(MC, "versions", "26.3", "26.3.jar"))
    natives = os.path.join(GAME, "natives")
    jvm = []
    for a in v["arguments"]["jvm"]:
        if isinstance(a, str):
            jvm.append(a)
        elif any(r.get("os", {}).get("name") == "windows" for r in a["rules"]):
            jvm += a["value"] if isinstance(a["value"], list) else [a["value"]]
    sub = {"${natives_directory}": natives, "${launcher_name}": "genesis-test", "${launcher_version}": "1",
           "${classpath}": os.pathsep.join(cp)}
    for k, val in sub.items():
        jvm = [a.replace(k, val) for a in jvm]
    cmd = [JAVA, "-Xmx4G"] + jvm + [v["mainClass"], "--username", NAME, "--version", "26.3", "--gameDir", GAME,
                                   "--assetsDir", os.path.join(MC, "assets"), "--assetIndex", v["assetIndex"]["id"],
                                   "--accessToken", "0", "--userType", "legacy", "--width", "1280", "--height", "720",
                                   "--quickPlayMultiplayer", "localhost:25565"]
    # silent: the test must not play the narration over whatever the person at the computer is doing
    opts = os.path.join(GAME, "options.txt")
    lines = [l for l in open(opts, encoding="utf-8") if not l.startswith("soundCategory_master:")] + ["soundCategory_master:0.0\n"]
    open(opts, "w", encoding="utf-8").writelines(lines)
    return subprocess.Popen(cmd, cwd=GAME, stdout=open(os.path.join(GAME, "client.log"), "w"), stderr=subprocess.STDOUT)


def game_window():
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def each(hwnd, _):
        buf = ctypes.create_unicode_buffer(200)
        user32.GetWindowTextW(hwnd, buf, 200)
        if buf.value.startswith("Minecraft") and "Launcher" not in buf.value and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(each, 0)
    return found[0] if found else None


def shot(name):
    """Copy the game window's own picture. It is not brought to the front and nothing else on screen is captured."""
    from PIL import Image

    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    hwnd = game_window()
    if not hwnd:
        print("no game window for", name)
        return
    rc = (ctypes.c_long * 4)()
    user32.GetClientRect(hwnd, rc)
    w, h = rc[2], rc[3]
    for f in (user32.GetDC, gdi32.CreateCompatibleDC, gdi32.CreateCompatibleBitmap, gdi32.SelectObject):
        f.restype = ctypes.c_void_p
    hdc = user32.GetDC(ctypes.c_void_p(hwnd))
    mem = gdi32.CreateCompatibleDC(ctypes.c_void_p(hdc))
    bmp = gdi32.CreateCompatibleBitmap(ctypes.c_void_p(hdc), w, h)
    gdi32.SelectObject(ctypes.c_void_p(mem), ctypes.c_void_p(bmp))
    user32.PrintWindow(ctypes.c_void_p(hwnd), ctypes.c_void_p(mem), 3)      # client area, full content
    header = (ctypes.c_uint32 * 10)(40, w, ctypes.c_uint32(-h).value, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(ctypes.c_void_p(mem), ctypes.c_void_p(bmp), 0, h, buf, header, 0)
    gdi32.DeleteObject(ctypes.c_void_p(bmp))
    gdi32.DeleteDC(ctypes.c_void_p(mem))
    user32.ReleaseDC(ctypes.c_void_p(hwnd), ctypes.c_void_p(hdc))
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    img.thumbnail((960, 540))
    img.save(os.path.join(SHOTS, name + ".jpg"), quality=80)
    print("shot", name, flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=3.0, help="how many times faster than real time to run")
    ap.add_argument("--ticks", default="")
    ap.add_argument("--after", type=int, default=3, help="screenshots to take in free play")
    args = ap.parse_args()
    os.makedirs(SHOTS, exist_ok=True)
    ctypes.windll.user32.SetProcessDPIAware()
    sched = json.load(open(os.path.join(ROOT, "work", "schedule.json")))
    m, vs, ve = sched["marks"], sched["verse_start"], sched["verse_end"]
    ticks = sorted(int(t) for t in args.ticks.split(",") if t) or sorted({
        vs["2"] + 60, m["light"] - 12, m["light"] + 6, m["light"] + 60, ve["4"] + 5, ve["6"], ve["7"] + 20, m["rise"] + 80,
        ve["9"] + 120, ve["10"], m["green"] + 120, ve["12"] + 60, ve["14"], m["sun"] + 30, m["moon"] + 40, m["stars"] + 70,
        m["swim"] + 50, m["whales"] + 40, ve["21"], ve["22"], ve["24"], ve["25"], m["beam"] + 60, m["him"] + 14, m["her"] + 14,
        m["awake"] + 50, ve["29"], ve["31"], ve["33"]})
    client = launch()
    r = Rcon()
    try:
        deadline = time.time() + 180
        while NAME not in r.cmd("list"):
            if time.time() > deadline or client.poll() is not None:
                sys.exit("the test client did not join; see work\\testgame\\client.log")
            time.sleep(2)
        time.sleep(12)
        shot("000_lobby")
        r.cmd(f"tp {NAME} 1003.5 100 997.5 -90 0")      # onto the gold stone: Adam
        time.sleep(5)
        r.cmd(f"tick rate {20 * args.rate}")
        m = sched["marks"]
        looks = {m["moon"] + 10: "-90 -30", sched["verse_start"]["17"]: "-90 0"}   # look up for the moon and stars
        for t in ticks:
            while True:
                now = int(r.cmd("scoreboard players get #t gen").split(" has ")[1].split()[0])
                for lt in [k for k in looks if k <= now]:
                    r.cmd(f"rotate {NAME} {looks.pop(lt)}")
                if now >= t or int(r.cmd("scoreboard players get #phase gen").split(" has ")[1].split()[0]) == 2:
                    break
                time.sleep(0.05)
            shot(f"t{t:05d}")
        r.cmd("tick rate 20")
        time.sleep(6)
        for i, (pos, rot) in enumerate([("-64.5 69 -1.5", "-90 0"), ("-8.5 64 0.5", "-90 -12"), ("-40.5 71 20.5", "-50 0")][:args.after]):
            r.cmd(f"tp {NAME} {pos} {rot}")
            time.sleep(4)
            shot(f"z_free{i}")
    finally:
        r.cmd("tick rate 20")
        client.terminate()


if __name__ == "__main__":
    main()
