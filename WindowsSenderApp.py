import socket
import pyaudiowpatch as pyaudio
import threading
from guizero import App, Text, TextBox, PushButton, Box

CHUNK = 1024

class WindowsAudioSender:
    def __init__(self):
        self.running = False
        self.client_socket = None
        self.stream = None
        self.p = pyaudio.PyAudio()
        
        # Build GUI
        self.app = App(title="Wireless Audio Sender", width=400, height=280)
        self.app.bg = "#f3f4f6"
        
        Text(self.app, text="Windows Audio Sender", size=18, weight="bold", color="#111827")
        Text(self.app, text="Streams speech engine audio to Mac", size=10, color="#6b7280")
        
        # IP Input Section
        input_box = Box(self.app, width=350, height=50)
        Text(input_box, text="Enter Mac's IP Address:", size=11, align="left")
        self.ip_input = TextBox(input_box, text="192.168.1.X", width=15, align="right")
        
        # Status Box
        self.status_box = Box(self.app, width=350, height=60)
        self.status_box.bg = "#ffffff"
        self.status_box.set_border(1, "#e5e7eb")
        self.status_label = Text(self.status_box, text="Status: Disconnected", size=12, weight="bold")
        self.status_label.text_color = "#dc2626"
        
        # Button
        self.btn = PushButton(self.app, command=self.toggle_sender, text="Connect to Mac", width=15)
        self.btn.bg = "#3b82f6"
        self.btn.text_color = "white"
        
        self.app.when_closed = self.on_close
        self.app.display()

    def get_loopback_device(self):
        wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackCapable"]:
            for dev_index in range(self.p.get_device_count()):
                dev_info = self.p.get_device_info_by_index(dev_index)
                if dev_info["hostApi"] == wasapi_info["index"] and dev_info["isLoopbackCapable"]:
                    return dev_info
        return default_speakers

    def toggle_sender(self):
        if not self.running:
            self.running = True
            self.btn.text = "Disconnect"
            self.btn.bg = "#ef4444"
            self.status_label.value = "Status: Connecting..."
            self.status_label.text_color = "#d97706"
            
            # Start background thread to run audio loop
            self.thread = threading.Thread(target=self.audio_worker, daemon=True)
            self.thread.start()
        else:
            self.stop_sender()

    def audio_worker(self):
        target_ip = self.ip_input.value
        try:
            device_info = self.get_loopback_device()
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=device_info["maxInputChannels"],
                rate=int(device_info["defaultSampleRate"]),
                input=True,
                input_device_index=device_info["index"],
                frames_per_buffer=CHUNK
            )
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(4.0) # Fails quickly if Mac isn't listening
            self.client_socket.connect((target_ip, 50005))
            self.client_socket.settimeout(None) # Clear timeout for streaming
            
            self.status_label.value = "Status: Connected & Streaming!"
            self.status_label.text_color = "#16a34a"
            
            while self.running:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.client_socket.sendall(data)
                
        except Exception as e:
            print(f"Error: {e}")
            self.app.after(0, self.show_error_status)
        finally:
            self.stop_sender()

    def show_error_status(self):
        self.status_label.value = "Status: Connection Failed"
        self.status_label.text_color = "#dc2626"

    def stop_sender(self):
        self.running = False
        self.btn.text = "Connect to Mac"
        self.btn.bg = "#3b82f6"
        if self.status_label.value != "Status: Connection Failed":
            self.status_label.value = "Status: Disconnected"
            self.status_label.text_color = "#dc2626"
            
        if self.client_socket:
            self.client_socket.close()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def on_close(self):
        self.stop_sender()
        self.p.terminate()
        self.app.destroy()

if __name__ == "__main__":
    WindowsAudioSender()
