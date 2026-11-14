"""Real-motion screen recording of the working app (no narration, no person on screen).

Drives the installed Google Chrome with Playwright, captures frames through the
Chrome DevTools screencast, and returns timestamped JPEG frames that
make_motion_video.py turns into a constant-frame-rate MP4.
"""
import base64
import time

from playwright.sync_api import sync_playwright

W, H = 1920, 1080


class Recorder:
    def __init__(self, url, headless=True):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(channel="chrome", headless=headless,
                                                args=["--hide-scrollbars"])
        self.page = self.browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        self.page.goto(url, wait_until="networkidle")
        self.cdp = self.page.context.new_cdp_session(self.page)
        self.frames = []  # (t, jpeg bytes)
        self.marks = []   # (t, label) for captions
        self.cdp.on("Page.screencastFrame", self._on_frame)

    def _on_frame(self, ev):
        self.frames.append((time.time(), base64.b64decode(ev["data"])))
        self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

    def start(self):
        self.t0 = time.time()
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                               "maxWidth": W, "maxHeight": H, "everyNthFrame": 1})

    def mark(self, label):
        self.marks.append((time.time(), label))

    def wait(self, s):
        end = time.time() + s
        while time.time() < end:
            self.page.wait_for_timeout(20)

    def glide(self, x0, y0, x1, y1, secs=0.8, steps=None):
        steps = steps or max(8, int(secs * 60))
        self.page.mouse.move(x0, y0)
        for i in range(1, steps + 1):
            a = i / steps
            e = a * a * (3 - 2 * a)
            self.page.mouse.move(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
            self.page.wait_for_timeout(secs * 1000 / steps)

    def drag(self, x0, y0, x1, y1, secs=1.0):
        self.page.mouse.move(x0, y0)
        self.page.mouse.down()
        self.glide(x0, y0, x1, y1, secs)
        self.page.mouse.up()

    def wheel(self, x, y, dy, n=10, secs=1.0):
        self.page.mouse.move(x, y)
        for _ in range(n):
            self.page.mouse.wheel(0, dy)
            self.page.wait_for_timeout(secs * 1000 / n)

    def stop(self):
        self.cdp.send("Page.stopScreencast")
        self.page.wait_for_timeout(200)
        self.browser.close()
        self._pw.stop()
        return self.frames, self.marks, self.t0
