#!/usr/bin/env python3
"""
Advanced fast MicroPython uploader for Raspberry Pi Pico over USB serial (raw REPL).

Features:
- Interrupts & safely stops running user code
- FAST uploads using base64 (auto-chunked for large files)
- Upload full folder OR single file
- Optional destination path for single file
- Exclude patterns
- Optional reset after upload
- Optional filesystem format (delete all files)
- Progress bar
- Tree-style file listing on Pico after upload
- Local folder tree display before upload

Usage:
  python pico_upload.py project/
  python pico_upload.py --file main.py --dest app/main.py

Requires:
  pip install pyserial tqdm
"""

import argparse
import os
import time
from datetime import datetime
import serial
import serial.tools.list_ports
import sys
from tqdm import tqdm
import base64
import fnmatch

CTRL_A = b'\x01'
CTRL_B = b'\x02'
CTRL_C = b'\x03'
CTRL_D = b'\x04'

MAX_B64_CHUNK = 96 * 1024  # increased from 48KB for faster upload

# ---------------- SERIAL UTILS ----------------

def find_pico_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if ('Pico' in p.description) or ('ttyACM' in p.device):
            return p.device
    return ports[0].device if ports else None


def open_serial(port, baud=1000000):  # faster default baud
    ser = serial.Serial(port, baudrate=baud, timeout=1)
    time.sleep(2)
    return ser


# ---------------- REPL CONTROL ----------------

def flush_serial(ser):
    while ser.in_waiting:
        ser.read(ser.in_waiting)


def enter_raw_repl(ser):
    ser.write(CTRL_C)
    time.sleep(0.05)
    ser.write(CTRL_C)
    time.sleep(0.05)
    ser.write(CTRL_A)
    time.sleep(0.1)
    flush_serial(ser)


def exit_raw_repl(ser):
    ser.write(CTRL_B)
    time.sleep(0.1)


# ---------------- REMOTE EXEC ----------------

def remote_exec(ser, code):
    if isinstance(code, str):
        code = code.encode()
    ser.write(code)
    ser.write(CTRL_D)
    time.sleep(0.01)
    return read_output(ser)


def read_output(ser, timeout=3):
    start = time.time()
    buf = b''
    while time.time() - start < timeout:
        if ser.in_waiting:
            buf += ser.read(ser.in_waiting)
        time.sleep(0.01)
    return buf.decode(errors='ignore')


# ---------------- SAFE STOP ----------------

def stop_user_code(ser):
    remote_exec(ser, """
import sys, gc
sys.modules.clear()
gc.collect()
""")


# ---------------- FILESYSTEM OPS ----------------

def ensure_dir(ser, path):
    remote_exec(ser, f"""
import os
try:
    os.mkdir('{path}')
except OSError:
    pass
""")


def ensure_dir_tree(ser, path):
    cur = ''
    for p in path.split('/'):
        if not p:
            continue
        cur = f"{cur}/{p}" if cur else p
        ensure_dir(ser, cur)


# ---------------- FORMAT FS ----------------

def format_filesystem(ser):
    print("Formatting Pico filesystem...")
    remote_exec(ser, """
import os

def rm_tree(path=''):
    try:
        for f in os.listdir(path or '/'):
            p = (path + '/' + f) if path else f
            try:
                os.listdir(p)
                rm_tree(p)
                os.rmdir(p)
            except OSError:
                os.remove(p)
    except OSError:
        pass

rm_tree()
""")


# ---------------- FAST WRITE ----------------

def write_file_fast(ser, remote_path, data):
    remote_dir = os.path.dirname(remote_path)
    if remote_dir:
        ensure_dir_tree(ser, remote_dir)

    remote_exec(ser, f"f = open('{remote_path}', 'wb')")

    for i in range(0, len(data), MAX_B64_CHUNK):
        chunk = data[i:i+MAX_B64_CHUNK]
        b64 = base64.b64encode(chunk).decode()
        remote_exec(ser, f"""
import ubinascii
f.write(ubinascii.a2b_base64({b64!r}))
""")
        time.sleep(0.01)  # minimal sleep for reliability

    remote_exec(ser, "f.close()")


# ---------------- LOCAL TREE DISPLAY ----------------

def print_local_tree(root, exclude=None):
    print("\nLocal files to be uploaded:")
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        indent = '' if rel == '.' else '  ' * (rel.count(os.sep) + 1)
        if rel != '.':
            print(f"{indent[:-2]}{os.path.basename(dirpath)}/")
        for f in filenames:
            relfile = os.path.relpath(os.path.join(dirpath, f), root).replace('\\', '/')
            if exclude and should_exclude(relfile, exclude):
                continue
            print(f"{indent}{f}")


# ---------------- UPLOAD LOGIC ----------------

def should_exclude(path, patterns):
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def collect_files(local_root, exclude):
    files = []
    for root, _, filenames in os.walk(local_root):
        for f in filenames:
            local = os.path.join(root, f)
            rel = os.path.relpath(local, local_root).replace('\\', '/')
            if exclude and should_exclude(rel, exclude):
                continue
            files.append((local, rel))
    return files


def upload_folder(ser, local_root, exclude):
    files = collect_files(local_root, exclude)
    total_bytes = sum(os.path.getsize(f[0]) for f in files)
    print(f"\nTotal files: {len(files)}, Total size: {total_bytes/1024:.2f} KB")
    for local, remote in tqdm(files, desc='Uploading', unit='file'):
        with open(local, 'rb') as fd:
            write_file_fast(ser, remote, fd.read())


def upload_single_file(ser, local_file, dest):
    remote = dest or os.path.basename(local_file)
    print(f"Uploading {local_file} -> {remote}")
    with open(local_file, 'rb') as fd:
        write_file_fast(ser, remote, fd.read())


# ---------------- REMOTE LISTING ----------------

def list_remote_files(ser):
    output = remote_exec(ser, """
import os

def walk(path='', indent=''):
    try:
        for f in os.listdir(path or '/'):
            p = (path + '/' + f) if path else f
            try:
                os.listdir(p)
                print(indent + f + '/')
                walk(p, indent + '  ')
            except OSError:
                print(indent + f)
    except OSError:
        pass

walk()
""")

    print("\nFiles on Pico:")
    for line in output.splitlines():
        if line.strip():
            print(line)


# ---------------- MAIN ----------------

def main():
    parser = argparse.ArgumentParser(description="Advanced fast MicroPython uploader for Raspberry Pi Pico")
    parser.add_argument('folder', nargs='?', help='Project folder to upload')
    parser.add_argument('--file', help='Upload a single file only')
    parser.add_argument('--list-remote', action='store_true', help='List files on Pico and exit')
    parser.add_argument('--dest', help='Destination path on Pico for --file')
    parser.add_argument('--exclude', action='append', default=[], help='Exclude glob pattern (can repeat)')
    parser.add_argument('--format', action='store_true', help='Delete ALL files on Pico before upload')
    parser.add_argument('--reset-after', action='store_true', help='Reset Pico after upload')
    parser.add_argument('--port', help='Serial port (auto-detect if not set)')
    parser.add_argument('--baud', type=int, default=1000000)
    args = parser.parse_args()

    port = args.port or find_pico_port()
    if not port:
        print('No Pico serial device found')
        sys.exit(1)

    print(f"Connecting to Pico on {port} at {args.baud} baud")
    ser = open_serial(port, args.baud)

    enter_raw_repl(ser)
    stop_user_code(ser)

    if args.format:
        format_filesystem(ser)

    if args.list_remote:
        print("Listing files on Pico...")
        list_remote_files(ser)
        exit_raw_repl(ser)
        ser.close()
        return

    if not args.folder and not args.file:
        parser.error('Specify a folder or --file')

    start = datetime.now()

    if args.file:
        upload_single_file(ser, args.file, args.dest)
    else:
        print_local_tree(args.folder, args.exclude)
        upload_folder(ser, args.folder, args.exclude)

    print("\nUpload complete. Listing files on Pico...")
    list_remote_files(ser)

    if args.reset_after:
        print("Resetting Pico...")
        remote_exec(ser, "import machine; machine.reset()")
        ser.close()
        return

    exit_raw_repl(ser)
    ser.close()

    dt = datetime.now() - start
    print(f"\nDone in {dt.total_seconds():.2f}s")


if __name__ == '__main__':
    main()
