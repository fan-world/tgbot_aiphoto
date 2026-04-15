from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


WIDTH = 1280
HEIGHT = 720
OUT_DIR = Path("src/razdevator/assets/screens")


class Canvas:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        index = (y * self.width + x) * 3
        self.pixels[index : index + 3] = bytes(color)

    def blend_pixel(self, x: int, y: int, color: tuple[int, int, int], alpha: float) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        index = (y * self.width + x) * 3
        base = self.pixels[index : index + 3]
        mixed = [
            int(base[i] * (1 - alpha) + color[i] * alpha)
            for i in range(3)
        ]
        self.pixels[index : index + 3] = bytes(mixed)

    def vertical_gradient(
        self,
        top: tuple[int, int, int],
        bottom: tuple[int, int, int],
    ) -> None:
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = tuple(
                int(top[i] * (1 - t) + bottom[i] * t)
                for i in range(3)
            )
            row = bytes(color) * self.width
            start = y * self.width * 3
            self.pixels[start : start + self.width * 3] = row

    def diagonal_glow(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        color: tuple[int, int, int],
        strength: float,
    ) -> None:
        min_x = max(0, int(center_x - radius))
        max_x = min(self.width, int(center_x + radius))
        min_y = max(0, int(center_y - radius))
        max_y = min(self.height, int(center_y + radius))
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                dx = x - center_x
                dy = y - center_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    continue
                alpha = (1 - dist / radius) ** 2 * strength
                self.blend_pixel(x, y, color, alpha)

    def stripe(self, offset: int, color: tuple[int, int, int], alpha: float) -> None:
        for y in range(self.height):
            x = int((y * 1.7 + offset) % self.width)
            for thickness in range(-18, 19):
                self.blend_pixel(x + thickness, y, color, max(0.0, alpha - abs(thickness) * 0.01))

    def frame(self, color: tuple[int, int, int], alpha: float) -> None:
        border = 18
        for y in range(self.height):
            for x in range(self.width):
                if x < border or x >= self.width - border or y < border or y >= self.height - border:
                    self.blend_pixel(x, y, color, alpha)

    def dots(self, spacing: int, radius: int, color: tuple[int, int, int], alpha: float) -> None:
        for cy in range(spacing // 2, self.height, spacing):
            for cx in range(spacing // 2, self.width, spacing):
                for y in range(cy - radius, cy + radius + 1):
                    for x in range(cx - radius, cx + radius + 1):
                        dx = x - cx
                        dy = y - cy
                        if dx * dx + dy * dy <= radius * radius:
                            self.blend_pixel(x, y, color, alpha)

    def save_png(self, path: Path) -> None:
        raw = bytearray()
        stride = self.width * 3
        for y in range(self.height):
            raw.append(0)
            start = y * stride
            raw.extend(self.pixels[start : start + stride])

        def chunk(chunk_type: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + chunk_type
                + data
                + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
            )

        ihdr = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
        path.write_bytes(png)


def build_screen(
    name: str,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
    glow: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> None:
    canvas = Canvas(WIDTH, HEIGHT)
    canvas.vertical_gradient(top, bottom)
    canvas.diagonal_glow(WIDTH * 0.15, HEIGHT * 0.22, 290, glow, 0.48)
    canvas.diagonal_glow(WIDTH * 0.82, HEIGHT * 0.78, 420, accent, 0.28)
    canvas.diagonal_glow(WIDTH * 0.68, HEIGHT * 0.18, 210, accent, 0.18)
    canvas.stripe(120, accent, 0.20)
    canvas.stripe(480, glow, 0.15)
    canvas.frame((255, 255, 255), 0.12)
    canvas.dots(120, 3, (255, 255, 255), 0.05)
    canvas.save_png(OUT_DIR / f"{name}.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    screens = {
        "admin_home": ((245, 167, 52), (39, 43, 52), (255, 231, 162), (255, 196, 87)),
        "admin_general": ((78, 108, 139), (38, 43, 53), (124, 220, 255), (255, 186, 94)),
        "admin_bots": ((244, 178, 84), (34, 36, 42), (255, 214, 138), (255, 165, 69)),
        "admin_profile": ((57, 102, 118), (36, 43, 49), (129, 255, 241), (88, 210, 255)),
        "admin_owner": ((125, 64, 72), (28, 29, 35), (255, 178, 178), (255, 107, 129)),
        "admin_bot": ((245, 157, 66), (37, 41, 49), (255, 218, 160), (121, 194, 255)),
        "client_home": ((113, 74, 214), (24, 26, 52), (224, 155, 255), (112, 214, 255)),
        "client_profile": ((74, 111, 141), (32, 37, 47), (170, 232, 255), (136, 196, 255)),
        "client_templates": ((44, 81, 184), (19, 24, 48), (129, 180, 255), (139, 246, 255)),
        "client_upload": ((96, 76, 190), (26, 31, 56), (192, 155, 255), (100, 211, 255)),
        "client_shop": ((37, 118, 96), (23, 37, 41), (170, 255, 214), (255, 220, 121)),
        "client_language": ((54, 111, 124), (21, 36, 44), (163, 255, 247), (125, 201, 255)),
        "client_done": ((45, 133, 98), (23, 43, 35), (174, 255, 217), (149, 255, 193)),
    }
    for name, palette in screens.items():
        build_screen(name, *palette)


if __name__ == "__main__":
    main()
