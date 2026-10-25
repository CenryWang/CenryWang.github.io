import subprocess, time, os, io, datetime

PY = r"C:/TrendRadar/.venv/Scripts/python.exe"
PROJ = r"C:/TrendRadar"
LOG = r"C:/TrendRadar/crawler.log"
INTERVAL = 21600  # 6h
RETRIES = 3
RETRY_WAIT = 300  # 5min


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    try:
        with io.open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def run_once():
    cmd = [PY, "-m", "trendradar"] if os.path.isfile(PY) else ["uv", "run", "--frozen", "python", "-m", "trendradar"]
    proc = subprocess.run(
        cmd, cwd=PROJ, timeout=1800,
        capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return proc.returncode, proc.stdout, proc.stderr


while True:
    ok = False
    detail = ""
    for attempt in range(1, RETRIES + 1):
        try:
            rc, out, err = run_once()
            if rc == 0:
                ok = True
                detail = "rc=0"
                break
            detail = "rc=%s" % rc
        except subprocess.TimeoutExpired:
            detail = "timeout>1800s"
        except Exception as e:
            detail = "exception: %s" % e
        log("crawl attempt %d/%d FAILED: %s" % (attempt, RETRIES, detail))
        if attempt < RETRIES:
            time.sleep(RETRY_WAIT)
    if ok:
        log("crawl OK (%s)" % detail)
    else:
        log("crawl GAVE UP after %d attempts" % RETRIES)
    time.sleep(INTERVAL)
