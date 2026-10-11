"""Watch the intro without a headset: start a plain desktop client, join the local server,
choose Adam, and save screenshots of the game window at chosen moments.

The server must be running with online-mode=false (the test client has no account).

    python tools\\visual_test.py [--rate 3] [--ticks 100,900,...]
"""
import argparse, ctypes, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rcon import Rcon
from PIL import ImageGrab

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
    return subprocess.Popen(cmd, cwd=GAME, stdout=open(os.path.join(GAME, "client.log"), "w"), stderr=subprocess.STDOUT)


def window_rect():
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
    if not found:
        return None
    pt, rc = (ctypes.c_long * 2)(0, 0), (ctypes.c_long * 4)()
    user32.SetWindowPos(found[0], 0, 0, 0, 0, 0, 0x0001 | 0x0004)   # top-left corner, clear of any dialog in the middle of the screen
    user32.SetForegroundWindow(found[0])
    user32.GetClientRect(found[0], rc)
    user32.ClientToScreen(found[0], pt)
    return (pt[0], pt[1], pt[0] + rc[2], pt[1] + rc[3])


def shot(name):
    rect = window_rect()
    if not rect:
        print("no game window for", name)
        return
    time.sleep(0.15)
    img = ImageGrab.grab(bbox=rect, all_screens=True).convert("RGB")
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
    ticks = sorted(int(t) for t in args.ticks.split(",") if t) or sorted(
        {sched["verse_end"][str(v)] + off for v, off in
         [(2, 20), (3, 40), (3, 150), (4, 110), (5, 90), (6, 60), (7, 180), (9, 150), (9, 320), (10, 150), (11, 200),
          (12, 230), (15, 110), (16, 70), (16, 190), (16, 290), (18, 60), (20, 150), (21, 120), (22, 120), (24, 180),
          (25, 150), (26, -20), (27, 60), (29, 60), (31, 150), (32, 90), (34, 60)]})
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
        r.cmd(f"tp {NAME} 997.5 100 996.5 180 0")
        time.sleep(5)
        r.cmd(f"tick rate {20 * args.rate}")
        e16 = sched["verse_end"]["16"]
        looks = {e16 + 140: "-90 -40", sched["verse_end"]["17"]: "-90 0"}   # look up for the moon and stars
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
        for i, (pos, rot) in enumerate([("-6.5 69 0.5", "-90 0"), ("-100.5 84 0.5", "-90 15"), ("-30.5 72 10.5", "90 5")][:args.after]):
            r.cmd(f"tp {NAME} {pos} {rot}")
            time.sleep(4)
            shot(f"z_free{i}")
    finally:
        r.cmd("tick rate 20")
        client.terminate()


if __name__ == "__main__":
    main()
