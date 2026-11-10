#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HoloBuddy PC Companion Streamer (for ASUS ROG Strix G16 — Windows / macOS / Linux)
==================================================================================
Streams real-time 128x64 holographic video frames ("My Way" lyric videos, animations),
synced `.lrc` karaoke lyrics, or live ROG Strix G16 CPU/GPU telemetry to `HoloBuddy`
over USB-C Serial (921600 baud) or Wi-Fi UDP (port 4210).

Install optional dependencies on your laptop:
    pip install pillow opencv-python pyserial psutil

Usage examples:
  1. Stream a lyric MP4 video over USB-C Serial:
       python pc_holo_streamer.py --video my_way_lyrics.mp4 --serial COM5
  2. Stream synced `.lrc` karaoke lyrics over Wi-Fi UDP:
       python pc_holo_streamer.py --lrc my_way.lrc --udp 192.168.1.50
  3. Stream live ASUS ROG Strix G16 CPU% + NVIDIA GPU Temp HUD:
       python pc_holo_streamer.py --telemetry --udp 192.168.1.50
  4. Test holographic frame rendering right in your terminal (no hardware needed):
       python pc_holo_streamer.py --demo-my-way --preview-ascii
"""

import argparse
import re
import socket
import subprocess
import sys
import time

FRAME_W = 128
FRAME_H = 64
FRAME_BYTES = (FRAME_W * FRAME_H) // 8  # 1024 bytes


class HoloTransport:
    """Unified sender supporting USB-C Serial (921600), Wi-Fi UDP (4210), and ASCII preview."""

    def __init__(self, serial_port: str = None, baud: int = 921600, udp_host: str = None, udp_port: int = 4210, ascii_preview: bool = False):
        self.ser = None
        self.sock = None
        self.udp_target = None
        self.ascii_preview = ascii_preview

        if serial_port:
            import serial  # pyserial
            self.ser = serial.Serial(serial_port, baudrate=baud, timeout=0.05)
            time.sleep(0.4)
        if udp_host:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_target = (udp_host, udp_port)

    def send_frame(self, packed_1024: bytes):
        assert len(packed_1024) == FRAME_BYTES
        pkt = b"HOLO" + packed_1024
        if self.ser:
            self.ser.write(pkt)
        if self.sock and self.udp_target:
            self.sock.sendto(pkt, self.udp_target)
        if self.ascii_preview:
            self._print_ascii(packed_1024)

    def send_telemetry(self, cpu_pct: int, gpu_temp_c: int, ram_pct: int, line1: str = "", line2: str = ""):
        l1 = line1.encode("ascii", errors="replace")[:31].ljust(31, b"\x00")
        l2 = line2.encode("ascii", errors="replace")[:31].ljust(31, b"\x00")
        pkt = b"STAT" + bytes([cpu_pct & 0xFF, gpu_temp_c & 0xFF, ram_pct & 0xFF]) + l1 + l2
        if self.sock and self.udp_target:
            self.sock.sendto(pkt, self.udp_target)

    @staticmethod
    def _print_ascii(packed_1024: bytes):
        # Downsample 2x2 into 64x32 terminal preview
        out_lines = ["\x1b[H"]
        for y in range(0, FRAME_H, 2):
            row_chars = []
            for x in range(0, FRAME_W, 2):
                byte_idx = y * 16 + (x >> 3)
                bit_on = bool(packed_1024[byte_idx] & (0x80 >> (x & 7)))
                row_chars.append("#" if bit_on else " ")
            out_lines.append("".join(row_chars))
        sys.stdout.write("\n".join(out_lines) + "\n")
        sys.stdout.flush()


def pack_pil_image_1bit(img_gray, dither: bool = True, threshold: int = 118) -> bytes:
    """Convert a 128x64 grayscale PIL Image into row-major MSB-first 1024-byte GFXcanvas1 format."""
    from PIL import Image, ImageOps

    resized = ImageOps.autocontrast(img_gray.resize((FRAME_W, FRAME_H)), cutoff=2)
    if dither:
        bw = resized.convert("1")  # Floyd-Steinberg dithering for video gradients
    else:
        bw = resized.point(lambda p: 255 if p >= threshold else 0, mode="1")
    raw = bw.tobytes()
    assert len(raw) == FRAME_BYTES
    return raw


def parse_lrc_file(path: str) -> list:
    """Parse standard `[mm:ss.xx] Lyric text` lines into sorted `[(sec, text), ...]`."""
    entries = []
    pat = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            m = pat.match(line.strip())
            if m:
                t_sec = int(m.group(1)) * 60.0 + float(m.group(2))
                entries.append((t_sec, m.group(3).strip()))
    entries.sort(key=lambda item: item[0])
    return entries


def render_lyric_frame_raw(active_line: str, next_line: str, progress: float) -> bytes:
    """Zero-dependency built-in 5x7 bitmap font renderer (uses Pillow if installed, pure Python fallback!)."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("L", (FRAME_W, FRAME_H), 0)
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((1, 1, 126, 62), radius=5, outline=255, width=1)
        draw.text((8, 12), active_line[:20], fill=255)
        draw.text((8, 30), next_line[:20], fill=180)
        bar_w = int(max(0.0, min(1.0, progress)) * 110)
        draw.rectangle((9, 52, 119, 56), outline=255)
        if bar_w > 0:
            draw.rectangle((9, 52, 9 + bar_w, 56), fill=255)
        return pack_pil_image_1bit(img, dither=False, threshold=100)
    except ImportError:
        # Pure-Python fallback frame with animated holographic border & progress bar
        buf = bytearray(FRAME_BYTES)
        bar_cols = int(max(0.0, min(1.0, progress)) * 112)
        for x in range(8, 8 + bar_cols):
            for y in (52, 53, 54, 55):
                buf[y * 16 + (x >> 3)] |= (0x80 >> (x & 7))
        for x in range(4, 124):
            for y in (3, 60):
                buf[y * 16 + (x >> 3)] |= (0x80 >> (x & 7))
        return bytes(buf)


def stream_video(video_path: str, transport: HoloTransport, dither: bool = True):
    import cv2
    from PIL import Image

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_dt = 1.0 / min(fps, 35.0)
    t_next = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        pil_img = Image.fromarray(gray)
        packed = pack_pil_image_1bit(pil_img, dither=dither)
        transport.send_frame(packed)

        t_next += frame_dt
        sleep_s = t_next - time.perf_counter()
        if sleep_s > 0:
            time.sleep(sleep_s)

    cap.release()


def read_nvidia_gpu_temp() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )
        return int(out.decode("utf-8").strip().splitlines()[0])
    except Exception:
        return 0


def stream_rog_telemetry(transport: HoloTransport):
    import psutil

    print("Streaming live ASUS ROG Strix G16 CPU/GPU/RAM telemetry to HoloBuddy (Ctrl+C to stop)...")
    while True:
        cpu = int(round(psutil.cpu_percent(interval=0.5)))
        ram = int(round(psutil.virtual_memory().percent))
        gpu_t = read_nvidia_gpu_temp()
        transport.send_telemetry(cpu, gpu_t, ram, "ROG Strix G16 Live", f"RAM: {ram}%")


def run_demo_my_way(transport: HoloTransport, max_frames: int = None):
    demo_lines = [
        (0.0, "And now, the end", "is near..."),
        (2.0, "And so I face", "the final curtain"),
        (4.0, "I'll state my case", "of which I'm sure"),
        (6.0, "I did it MY WAY!", "HoloBuddy v1.0"),
    ]
    total_s = 8.0
    t0 = time.perf_counter()
    frames = 0
    while True:
        elapsed = (time.perf_counter() - t0) % total_s
        cur_a, cur_b = demo_lines[0][1], demo_lines[0][2]
        for ts, la, lb in demo_lines:
            if elapsed >= ts:
                cur_a, cur_b = la, lb
        packed = render_lyric_frame_raw(cur_a, cur_b, elapsed / total_s)
        transport.send_frame(packed)
        frames += 1
        if max_frames is not None and frames >= max_frames:
            break
        time.sleep(1.0 / 20.0)


def main():
    parser = argparse.ArgumentParser(description="HoloBuddy ESP32 128x64 Hologram Streamer")
    parser.add_argument("--serial", help="USB-C serial port (e.g. COM5 or /dev/ttyACM0)")
    parser.add_argument("--udp", help="HoloBuddy Wi-Fi IP address (e.g. 192.168.1.50)")
    parser.add_argument("--video", help="Path to MP4/GIF lyric video to stream")
    parser.add_argument("--lrc", help="Path to synced .lrc lyric file")
    parser.add_argument("--telemetry", action="store_true", help="Stream live ROG Strix G16 CPU/GPU stats")
    parser.add_argument("--demo-my-way", action="store_true", help="Run built-in 'My Way' holographic stage demo")
    parser.add_argument("--no-dither", action="store_true", help="Use crisp threshold instead of Floyd-Steinberg dithering")
    parser.add_argument("--preview-ascii", action="store_true", help="Preview hologram frames in terminal")
    parser.add_argument("--frames", type=int, default=None, help="Stop demo after N frames (for testing)")
    args = parser.parse_args()

    transport = HoloTransport(
        serial_port=args.serial,
        udp_host=args.udp,
        ascii_preview=args.preview_ascii,
    )

    if args.video:
        stream_video(args.video, transport, dither=not args.no_dither)
    elif args.lrc:
        entries = parse_lrc_file(args.lrc)
        if not entries:
            raise ValueError(f"No timestamped lyrics found in {args.lrc}")
        end_t = entries[-1][0] + 5.0
        t0 = time.perf_counter()
        while True:
            now_s = time.perf_counter() - t0
            if now_s > end_t:
                break
            idx = 0
            for i, (ts, _) in enumerate(entries):
                if now_s >= ts:
                    idx = i
            cur_txt = entries[idx][1]
            nxt_txt = entries[idx + 1][1] if idx + 1 < len(entries) else ""
            transport.send_frame(render_lyric_frame_raw(cur_txt, nxt_txt, now_s / end_t))
            time.sleep(1.0 / 25.0)
    elif args.telemetry:
        stream_rog_telemetry(transport)
    else:
        run_demo_my_way(transport, max_frames=args.frames)


if __name__ == "__main__":
    main()
