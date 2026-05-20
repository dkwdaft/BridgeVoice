# --- APPLE SILICON PORTAUDIO BUG FIX ---
try:
    import sounddevice  # Forces macOS to map Apple Silicon core audio drivers safely
except ImportError:
    pass
# --------------------------------------

import socket
import pyaudio
import threading
from guizero import App, Text, PushButton, Box

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024


class MacAudioReceiver:
    def __init__(self):
        self.running = False
        self.server_socket = None
        self.stream = None
        self.p = pyaudio.PyAudio()

        # Build GUI (increased height to 290 to comfortably fit the IP display)
        self.app = App(title="Wireless Audio Receiver", width=400, height=290)
        self.app.bg = "#f3f4f6"

        # Title text
        Text(self.app, text="Mac Audio Receiver", size=18, bold=True, color="#111827")
        Text(self.app, text="Receives audio from Windows Communication Aid", size=10, color="#6b7280")

        # --- NEW: Local Mac IP Display & Copy Section ---
        self.local_ip = self.get_local_ip()
        ip_display_box = Box(self.app, width=350, height=40)
        Text(ip_display_box, text=f"Mac IP Address: {self.local_ip}", size=11, align="left", bold=True, color="#374151")
        copy_btn = PushButton(ip_display_box, command=self.copy_ip_to_clipboard, text="Copy IP", align="right", width=8)
        copy_btn.bg = "#e5e7eb"
        copy_btn.text_size = 9

        # Status box
        self.status_box = Box(self.app, width=350, height=60, layout="grid")
        self.status_box.bg = "#ffffff"
        self.status_box.set_border(1, "#e5e7eb")

        # --- FIXED LINE 40 BELOW ---
        self.status_label = Text(self.status_box, text="Status: Stopped", grid=[0, 0], size=12, bold=True)
        self.status_label.text_color = "#dc2626"

        # Action button
        self.btn = PushButton(self.app, command=self.toggle_receiver, text="Start Listening", width=15)
        self.btn.bg = "#3b82f6"
        self.btn.text_color = "white"

        self.app.when_closed = self.on_close
        self.app.display()

    # --- NEW METHOD: Finds the Mac's primary local network IP ---
    def get_local_ip(self):
        try:
            # Opens a temporary socket to public DNS to force the OS to pick 
            # the active network interface (Wi-Fi or Ethernet) instead of localhost.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # --- NEW METHOD: Copies IP to clipboard using built-in Tkinter hooks ---
    def copy_ip_to_clipboard(self):
        # Because guizero wraps Tkinter natively, we can use it to touch the macOS clipboard dependency-free
        self.app.tk.clipboard_clear()
        self.app.tk.clipboard_append(self.local_ip)
        
        # Give the user visual feedback in the status bar
        old_status = self.status_label.value
        old_color = self.status_label.text_color
        
        self.status_label.value = "IP Copied to Clipboard!"
        self.status_label.text_color = "#2563eb"
        
        # Revert status back to what it was after 1.5 seconds
        self.app.after(1500, lambda: self.reset_status(old_status, old_color))

    def reset_status(self, text, color):
        # Only revert if a fresh network event didn't rewrite the status panel in the meantime
        if "Copied" in self.status_label.value:
            self.status_label.value = text
            self.status_label.text_color = color

    def get_virtual_device_index(self):
        for i in range(self.p.get_device_count()):
            name = self.p.get_device_info_by_index(i)['name']
            if "BlackHole" in name or "VB-Cable" in name or "Virtual Audio" in name:
                return i
        return None

    def toggle_receiver(self):
        if not self.running:
            self.running = True
            self.btn.text = "Stop Listening"
            self.btn.bg = "#ef4444"
            self.status_label.value = "Status: Listening on port 50005..."
            self.status_label.text_color = "#d97706"

            self.thread = threading.Thread(target=self.audio_worker, daemon=True)
            self.thread.start()
        else:
            self.stop_receiver()

    def audio_worker(self):
        device_index = self.get_virtual_device_index()

        try:
            self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                      output=True, output_device_index=device_index,
                                      frames_per_buffer=CHUNK)

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', 50005))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)

            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    self.status_label.value = f"Status: Connected to Aid ({addr[0]})"
                    self.status_label.text_color = "#16a34a"

                    while self.running:
                        data = conn.recv(CHUNK * 4)
                        if not data:
                            break
                        if self.stream:
                            self.stream.write(data)
                    conn.close()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop_receiver()

    def stop_receiver(self):
        self.running = False
        self.btn.text = "Start Listening"
        self.btn.bg = "#3b82f6"
        if "Connected" not in self.status_label.value and "Copied" not in self.status_label.value:
            self.status_label.value = "Status: Stopped"
            self.status_label.text_color = "#dc2626"

        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def on_close(self):
        self.stop_sender() if hasattr(self, 'stop_sender') else self.stop_receiver()
        self.p.terminate()
        self.app.destroy()


if __name__ == "__main__":
    MacAudioReceiver()
