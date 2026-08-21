#!/usr/bin/env python3
"""Record the `telos view` demo GIF for the README of telos-sdd.

The pipeline is: ``telos view --export`` into a temp directory, serve that
static site on a loopback port, drive a scripted Chromium visit with
Playwright (a fake DOM cursor is injected so moves and clicks are visible
on the recording), then encode the captured webm with ffmpeg into
``docs/demo.mp4`` and an optimised ``docs/demo.gif``.

Requirements on PATH: ``telos`` (or pass --telos) and ``ffmpeg``. Python
side: ``pip install playwright`` and ``playwright install chromium``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

VIEWPORT = {"width": 1280, "height": 800}
GIF_WIDTH = 960
GIF_FPS = 10
GIF_COLORS = 256
MAX_GIF_BYTES = 10_000_000

# Installed on every page: a dot that follows mousemove events (Playwright's
# mouse dispatches real DOM events, the OS cursor is never on the video) and
# a ripple ring on mousedown. Colours match the site's --accent.
CURSOR_JS = """
(() => {
  const install = () => {
    const style = document.createElement('style');
    style.textContent = `
      #demo-cursor{position:fixed;left:0;top:0;width:22px;height:22px;
        margin:-11px 0 0 -11px;border-radius:50%;background:rgba(31,111,74,.85);
        box-shadow:0 0 0 4px rgba(31,111,74,.22),0 2px 8px rgba(0,0,0,.35);
        pointer-events:none;z-index:2147483647;opacity:0;
        transition:opacity .2s,transform .12s;}
      #demo-cursor.down{transform:scale(.65);}
      .demo-ripple{position:fixed;width:80px;height:80px;border-radius:50%;
        border:3px solid rgba(31,111,74,.8);pointer-events:none;
        z-index:2147483646;transform:translate(-50%,-50%);
        animation:demo-ripple .5s ease-out forwards;}
      @keyframes demo-ripple{
        from{transform:translate(-50%,-50%) scale(0);opacity:1;}
        to{transform:translate(-50%,-50%) scale(1);opacity:0;}}
    `;
    document.head.appendChild(style);
    const dot = document.createElement('div');
    dot.id = 'demo-cursor';
    document.body.appendChild(dot);
    document.addEventListener('mousemove', e => {
      dot.style.opacity = '1';
      dot.style.left = e.clientX + 'px';
      dot.style.top = e.clientY + 'px';
    }, true);
    document.addEventListener('mousedown', e => {
      dot.classList.add('down');
      const r = document.createElement('div');
      r.className = 'demo-ripple';
      r.style.left = e.clientX + 'px';
      r.style.top = e.clientY + 'px';
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 600);
    }, true);
    document.addEventListener('mouseup', () => dot.classList.remove('down'), true);
  };
  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', install)
    : install();
})()
"""

SMOOTH_SCROLL_JS = """
([target, ms]) => new Promise(resolve => {
  const start = window.scrollY, delta = target - start, t0 = performance.now();
  const ease = t => t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
  const step = now => {
    const p = Math.min(1, (now - t0) / ms);
    window.scrollTo(0, start + delta * ease(p));
    p < 1 ? requestAnimationFrame(step) : resolve();
  };
  requestAnimationFrame(step);
})
"""


class Cursor:
    """Eased mouse moves so the injected dot glides instead of teleporting."""

    def __init__(self, page: Page, x: float = 640, y: float = 120):
        self.page, self.x, self.y = page, x, y

    def show(self) -> None:
        self.page.mouse.move(self.x, self.y)
        self.page.mouse.move(self.x + 1, self.y)

    def move_to(self, x: float, y: float, duration_ms: int = 500) -> None:
        steps = max(2, duration_ms // 33)
        for i in range(1, steps + 1):
            t = i / steps
            ease = 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
            self.page.mouse.move(
                self.x + (x - self.x) * ease, self.y + (y - self.y) * ease
            )
            self.page.wait_for_timeout(33)
        self.x, self.y = x, y

    def click(self, selector: str, settle_ms: int = 250) -> None:
        box = self.page.locator(selector).bounding_box()
        if box is None:
            raise RuntimeError(f"no bounding box for {selector!r}")
        self.move_to(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.wait_for_timeout(settle_ms)
        self.page.mouse.down()
        self.page.wait_for_timeout(280)
        self.page.mouse.up()


def scroll_to(
    page: Page, selector: str, margin: int = 96, duration_ms: int = 600
) -> None:
    top = page.locator(selector).evaluate(
        "el => el.getBoundingClientRect().top + window.scrollY"
    )
    page.evaluate(SMOOTH_SCROLL_JS, [max(0, top - margin), duration_ms])


def enforce_gif_size(gif: Path) -> None:
    size = gif.stat().st_size
    if size >= MAX_GIF_BYTES:
        raise RuntimeError(
            f"{gif} is {size / 1e6:.1f} MB; the demo GIF must stay below 10.0 MB"
        )


def tour(page: Page, base: str) -> None:
    """The scripted visit; roughly 25 seconds of footage."""
    wait = page.wait_for_timeout
    cursor = Cursor(page)

    # Dashboard: project coherence and the headline coverage metrics.
    page.goto(f"{base}/index.html")
    page.get_by_role("heading", name="Dashboard").wait_for()
    cursor.show()
    wait(1600)

    # Intent index: scan the catalogue before opening a representative intent.
    cursor.click('a.app-header__link[href="#/intents"]')
    page.wait_for_url("**/index.html#/intents")
    page.get_by_role("heading", name="Intents").wait_for()
    wait(900)
    intent_link = 'a[href="#/intent/INT-0008"]'
    scroll_to(page, intent_link, margin=180, duration_ms=700)
    wait(500)
    cursor.click(intent_link)
    page.wait_for_url("**/index.html#/intent/INT-0008")
    page.get_by_role(
        "heading", name="INT-0008 — Starvation is not a lifestyle"
    ).wait_for()
    wait(900)

    # Intent detail: reveal the canonical declaration, then its proved scenario.
    cursor.click("details summary")
    wait(1300)
    cursor.click("details summary")
    wait(300)
    scroll_to(page, "#scenario-SCN-0011", margin=180)
    wait(1300)

    # Graph: overview, relation filtering, then inspect a representative node.
    cursor.click('a.app-header__link[href="#/graph"]')
    page.wait_for_url("**/index.html#/graph")
    page.get_by_role("heading", name="Graph", exact=True).wait_for()
    page.locator(".cyto-graph__canvas").wait_for()
    wait(1400)

    relation_filter = 'select[aria-label="Filter graph by relation"]'
    cursor.click(relation_filter)
    page.locator(relation_filter).select_option("requires")
    wait(900)
    cursor.click('button[data-graph-action="fit"]')
    wait(500)

    graph = page.locator(".cyto-graph__canvas").bounding_box()
    if graph is None:
        raise RuntimeError("no bounding box for the dependency graph")
    cursor.move_to(
        graph["x"] + graph["width"] / 2,
        graph["y"] + graph["height"] * 0.31,
    )
    page.mouse.down()
    wait(280)
    page.mouse.up()
    page.locator(".selection-panel__id").wait_for()
    wait(1800)


def record(site: Path, workdir: Path) -> Path:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,
            record_video_dir=str(workdir),
            record_video_size=VIEWPORT,
        )
        context.add_init_script(CURSOR_JS)
        page = context.new_page()

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(site))
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            tour(page, f"http://127.0.0.1:{server.server_address[1]}")
        finally:
            server.shutdown()
        video = page.video
        context.close()
        browser.close()
        return Path(video.path())


def encode(webm: Path, out_dir: Path) -> None:
    run = partial(subprocess.run, check=True)
    filters = f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos"
    palette = webm.with_name("palette.png")
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-vf",
            "fps=30,scale=1280:-2:flags=lanczos",
            "-c:v",
            "libx264",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out_dir / "demo.mp4"),
        ]
    )
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-vf",
            f"{filters},palettegen=stats_mode=diff:max_colors={GIF_COLORS}",
            str(palette),
        ]
    )
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-i",
            str(palette),
            "-lavfi",
            f"{filters}[x];[x][1:v]paletteuse="
            "dither=bayer:bayer_scale=5:diff_mode=rectangle",
            str(out_dir / "demo.gif"),
        ]
    )
    enforce_gif_size(out_dir / "demo.gif")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--site", type=Path, help="already-exported site (skips telos view --export)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "docs",
        help="output directory (default: docs/)",
    )
    parser.add_argument("--telos", default="telos", help="telos binary")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="telos-demo-") as tmp:
        workdir = Path(tmp)
        site = args.site
        if site is None:
            site = workdir / "site"
            subprocess.run([args.telos, "view", "--export", str(site)], check=True)
        webm = record(site, workdir)
        encode(webm, args.out)

    for name in ("demo.gif", "demo.mp4"):
        size = (args.out / name).stat().st_size
        print(f"{args.out / name}  {size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
