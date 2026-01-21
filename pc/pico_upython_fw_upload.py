# Modified for full firmware project upload to Pico Pi
import argparse
import os
import time
from datetime import datetime
import serial
import serial.tools.list_ports
import sys
import select

CTRL_A = b'\x01'  # enter raw REPL
CTRL_B = b'\x02'  # exit raw REPL
CTRL_C = b'\x03'  # interrupt
CTRL_D = b'\x04'  # execute (end of paste)

def wait_for(ser, expected, timeout=5):
    deadline = time.time() + timeout
    buffer = b""
    while time.time() < deadline:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)
            if expected in buffer:
                return buffer
        time.sleep(0.01)
    return buffer

def enter_raw_repl(ser):
    ser.write(b'\r' + CTRL_C*2)  # interrupt any running program
    time.sleep(0.1)
    ser.write(b'\r' + CTRL_A)    # enter raw REPL
    time.sleep(0.1)
    wait_for(ser, b'raw REPL; CTRL-B to exit\r\n>')

def exit_raw_repl(ser):
    ser.write(CTRL_B)
    time.sleep(0.1)

def send_raw_code(ser, code, timeout=10):
    while ser.in_waiting:
        ser.read(ser.in_waiting)
    ser.write(code.encode('utf-8'))
    ser.write(CTRL_D)
    return wait_for(ser, b'OK', timeout=timeout)

def log_and_print(log_file, message):
    current_time = datetime.now()
    timestamp_raw = current_time.strftime("%Y-%m-%d\t%H-%M-%S")
    if not hasattr(log_and_print, 'start_time'):
        log_and_print.start_time = time.time()
    elapsed = time.time() - log_and_print.start_time
    elapsed_str = f"{elapsed:.3f}"
    timestamp_with_elapsed = f"{timestamp_raw}\t{elapsed_str}"
    timestamp_colored = f"\033[96m{timestamp_with_elapsed}\033[0m"

    lines = message.rstrip('\n').split('\n')
    terminal_lines = []
    file_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("--") and stripped_line.endswith("--"):
            clean_line = f"\033[96m{stripped_line[2:-2].strip()}\033[0m"
            terminal_lines.append(f"{timestamp_colored}\t{clean_line}")
        else:
            terminal_lines.append(f"{timestamp_colored}\t{line}")
            file_lines.append(f"{timestamp_with_elapsed}\t{line}")

    print('\n'.join(terminal_lines), end='\n')
    if file_lines:
        with open(log_file, 'a') as f:
            f.write('\n'.join(file_lines) + '\n')

def upload_file(ser, local_path, remote_path, log_file):
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()

    code = f"import os\nos.makedirs(os.path.dirname('{remote_path}'), exist_ok=True)\n"
    code += f"f = open('{remote_path}', 'w')\n"
    for line in content.splitlines():
        line_escaped = line.replace('\\', '\\\\').replace("'", "\\'")
        code += f"f.write('{line_escaped}\\n')\n"
    code += "f.close()\n"

    log_and_print(log_file, f"[INFO] Uploading {local_path} as {remote_path}\n")
    send_raw_code(ser, code)
    log_and_print(log_file, f"[INFO] Uploaded {local_path}\n")

def upload_folder(ser, folder_path, remote_root, log_file, extensions=('.py','.txt')):
    for root, dirs, files in os.walk(folder_path):
        relative_path = os.path.relpath(root, folder_path)
        pico_dir = os.path.join(remote_root, relative_path).replace("\\", "/")
        for file in files:
            if not file.endswith(extensions):
                continue
            local_file = os.path.join(root, file)
            remote_file = f"{pico_dir}/{file}" if pico_dir != "." else f"{file}"
            upload_file(ser, local_file, remote_file, log_file)

def run_script(ser, script_name, log_file):
    log_and_print(log_file, f"[INFO] Running script '{script_name}'... (Press Ctrl+C to stop)\n")
    code = f"exec(open('{script_name}').read())\n"
    send_raw_code(ser, code)

    try:
        while True:
            time.sleep(0.05)
            while ser.in_waiting:
                out = ser.read(ser.in_waiting).decode(errors='ignore')
                log_and_print(log_file, out)
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key in ('t', 'f'):
                    ser.write(key.encode())
    except KeyboardInterrupt:
        log_and_print(log_file, "\n[INFO] Ctrl+C detected.\n")
        answer = input("Stop execution on Pico and soft reset? (y/n): ").strip().lower()
        if answer == 'y':
            ser.write(b'\x03')  # Ctrl-C
            time.sleep(0.5)
            ser.write(b'\x04')  # Ctrl-D soft reset
            time.sleep(1)
            log_and_print(log_file, "[INFO] Pico soft reset done.\n")
        else:
            log_and_print(log_file, "[INFO] Script execution continues on Pico.\n")

def auto_detect_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Pico" in p.description or "USB Serial" in p.description:
            return p.device
    return None

def main():
    parser = argparse.ArgumentParser(description="Upload a firmware project folder to Raspberry Pi Pico.")
    parser.add_argument('--port', help="COM port (e.g., COM3 or /dev/ttyACM0). Auto-detects if not specified.")
    parser.add_argument('--fw-folder', required=True, help="Firmware project folder to upload.")
    parser.add_argument('--main', required=True, help="Main script to run on Pico (relative to fw-folder).")
    parser.add_argument('--filename', required=False, help="Suffix for log file.")
    parser.add_argument('-m', '--monitor', action='store_true', help="Monitor raw REPL without upload/run.")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename_suffix = args.filename or "noname"
    log_file = f"log_{timestamp}_{filename_suffix}.csv"

    port = args.port or auto_detect_port()
    if not port:
        print("[ERROR] Could not auto-detect Pico. Use --port.")
        return

    try:
        with serial.Serial(port, 115200, timeout=1) as ser:
            time.sleep(2)
            enter_raw_repl(ser)

            if args.monitor:
                log_and_print(log_file, "[INFO] Monitoring raw REPL (no upload/run)...\n")
                try:
                    while True:
                        if ser.in_waiting:
                            out = ser.read(ser.in_waiting).decode(errors='ignore')
                            log_and_print(log_file, out)
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    log_and_print(log_file, "[INFO] Monitor stopped by user.\n")
            else:
                upload_folder(ser, args.fw_folder, "/", log_file)
                main_remote = os.path.join("/", args.main).replace("\\","/")
                run_script(ser, main_remote, log_file)

            exit_raw_repl(ser)
    except Exception as e:
        error_msg = f"[ERROR] {e}\n"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(error_msg)

if __name__ == "__main__":
    main()
