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
        
        # Build GUI
        self.app = App(title="Wireless Audio Receiver", width=400, height=250)
        self.app.bg = "#f3f4f6"
        
        # Title text
        Text(self.app, text="Mac Audio Receiver", size=18, weight="bold", color="#111827")
        Text(self.app, text="Receives audio from Windows Communication Aid", size=10, color="#6b7280")
        
        # Status box
        self.status_box = Box(self.app, width=350, height=60, layout="grid")
        self.status_box.bg = "#ffffff"
        self.status_box.set_border(1, "#e5e7eb")
        
        self.status_label = Text(self.status_box, text="Status: Stopped", grid=[0,0], size=12, weight="bold")
        self.status_label.text_color = "#dc2626" # Red
        
        # Action button
        self.btn = PushButton(self.app, command=self.toggle_receiver, text="Start Listening", width=15)
        self.btn.bg = "#3b82f6"
        self.btn.text_color = "white"
        
        self.app.when_closed = self.on_close
        self.app.display()

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
            self.status_label.text_color = "#d97706" # Orange
            
            # Start background thread to handle network data without freezing GUI
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
            self.server_socket.settimeout(1.0) # Allows the loop to check if stopped
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    self.status_label.value = f"Status: Connected to Aid ({addr[0]})"
                    self.status_label.text_color = "#16a34a" # Green
                    
                    while self.running:
                        data = conn.recv(CHUNK * 4)
                        if not data:
                            break
                        if self.stream:
                            self.stream.write(data)
                    conn.close()
                except socket.timeout:
                    continue # Keep waiting for connection if timeout hits
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop_receiver()

    def stop_receiver(self):
        self.running = False
        self.btn.text = "Start Listening"
        self.btn.bg = "#3b82f6"
        self.status_label.value = "Status: Stopped"
        self.status_label.text_color = "#dc2626"
        
        if self.server_socket:
            self.server_socket.close()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def on_close(self):
        self.stop_receiver()
        self.p.terminate()
        self.app.destroy()

if __name__ == "__main__":
    MacAudioReceiver()
