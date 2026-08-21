"""Integration smoke test for the Telos demo tour."""

from __future__ import annotations

import subprocess
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tools import record_demo


def encode_test_pattern(directory: Path) -> bytes:
    source = directory / "pattern.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x800:rate=10:duration=0.2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
    )
    record_demo.encode(source, directory)
    return (directory / "demo.gif").read_bytes()


def gif_logical_screen_descriptor(gif: bytes) -> bytes:
    if len(gif) < 13 or gif[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("expected a valid GIF header")
    return gif[6:13]


def gif_dimensions(gif: bytes) -> tuple[int, int]:
    descriptor = gif_logical_screen_descriptor(gif)
    return (
        int.from_bytes(descriptor[0:2], "little"),
        int.from_bytes(descriptor[2:4], "little"),
    )


def gif_global_palette(gif: bytes) -> set[bytes]:
    descriptor = gif_logical_screen_descriptor(gif)
    packed = descriptor[4]
    if not packed & 0x80:
        raise ValueError("GIF has no global color table")
    palette_size = 2 ** ((packed & 0b111) + 1)
    palette_end = 13 + palette_size * 3
    if len(gif) < palette_end:
        raise ValueError("GIF has a truncated global color table")
    palette = gif[13:palette_end]
    return {palette[index : index + 3] for index in range(0, len(palette), 3)}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class DemoTourTest(unittest.TestCase):
    def test_gif_parser_rejects_an_invalid_header(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid GIF header"):
            gif_dimensions(b"not a gif")

    def test_gif_palette_parser_rejects_a_missing_global_table(self) -> None:
        gif = b"GIF89a\x01\x00\x01\x00\x00\x00\x00"

        with self.assertRaisesRegex(ValueError, "global color table"):
            gif_global_palette(gif)

    def test_gif_palette_parser_rejects_a_truncated_global_table(self) -> None:
        gif = b"GIF89a\x01\x00\x01\x00\x87\x00\x00\x00\x00\x00"

        with self.assertRaisesRegex(ValueError, "truncated global color table"):
            gif_global_palette(gif)

    def test_gif_uses_readable_width(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telos-demo-encode-test-") as tmp:
            gif = encode_test_pattern(Path(tmp))

        self.assertEqual((960, 600), gif_dimensions(gif))

    def test_gif_keeps_a_full_palette(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telos-demo-palette-test-") as tmp:
            gif = encode_test_pattern(Path(tmp))

        self.assertGreaterEqual(len(gif_global_palette(gif)), 192)

    def test_gif_size_limit_is_strict(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telos-demo-size-test-") as tmp:
            gif = Path(tmp) / "demo.gif"
            with gif.open("wb") as output:
                output.truncate(10_000_000)

            try:
                enforce_gif_size = record_demo.enforce_gif_size
            except AttributeError as error:
                self.fail(f"the GIF size limit is not enforced: {error}")
            with self.assertRaisesRegex(RuntimeError, "below 10.0 MB"):
                enforce_gif_size(gif)

    def test_tour_visits_the_telos_082_overview(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telos-demo-test-") as tmp:
            site = Path(tmp) / "site"
            subprocess.run(["telos", "view", "--export", str(site)], check=True)
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), partial(QuietHandler, directory=str(site))
            )
            threading.Thread(target=server.serve_forever, daemon=True).start()

            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    page = browser.new_page(viewport=record_demo.VIEWPORT)
                    page.set_default_timeout(2_000)
                    visited: list[str] = []
                    page.on(
                        "framenavigated",
                        lambda frame: visited.append(urlsplit(frame.url).fragment),
                    )

                    try:
                        try:
                            record_demo.tour(
                                page,
                                f"http://127.0.0.1:{server.server_address[1]}",
                            )
                        except Exception as error:
                            self.fail(f"the Telos 0.8.2 tour did not complete: {error}")
                        self.assertEqual(
                            ["/", "/intents", "/intent/INT-0008", "/graph"],
                            [route for route in dict.fromkeys(visited) if route],
                        )
                        self.assertEqual(
                            "requires",
                            page.get_by_label("Filter graph by relation").input_value(),
                        )
                        self.assertIn(
                            "SELECTED NODE", page.locator(".selection-panel").inner_text()
                        )
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
