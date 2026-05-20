# BridgeVoice 🎙️💻

BridgeVoice is a lightweight, wireless audio link designed specifically to route system audio from a Windows-based communication aid (AAC device) over a local Wi-Fi network directly into a Mac, registering it as a native system microphone/audio input device.

This lets you use your speech-generating device directly inside Mac applications like Zoom, Microsoft Teams, FaceTime, or audio recording software without messy, tangled physical cables.

---

## 🛠️ Prerequisites & Requirements

Before using the applications, ensure both devices are connected to the same local Wi-Fi network and have Python installed.

### 1. Mac Virtual Audio Driver (Required for Mac Input)
To make your Mac register the incoming audio stream as an actual microphone device, you need to install a virtual audio loopback driver. 
* Download and install **BlackHole 2ch** (Free/Open-Source) or **VB-Cable** (Free/Donationware).

### 2. Python Dependencies
Open your respective command line tools on both machines and install the following packages:

* **On the Mac (Terminal):**
  ```bash
  pip install pyaudio guizero
  ```
 * **On the Windows Communication Aid (Command Prompt):**

  ```
pip install pyaudiowpatch guizero
```
*(Note: `pyaudiowpatch` is specifically required on Windows to safely copy and loop back the system's output volume layer).*

---

## 🚀 How to Use BridgeVoice

Always launch and start the Mac receiver software **before** triggering the Windows sender software.

### Step 1: Start the Mac Receiver
1. Run `MacReceiverApp.py` on your Mac.
2. Click the **Start Listening** button. The status window will turn orange and display `Listening on port 50005...`.

### Step 2: Connect the Windows Communication Aid
1. Find your Mac's current Wi-Fi IP address (Hold `Option` and click the Wi-Fi icon on your Mac taskbar).
2. Run `WindowsSenderApp.py` on your Windows device.
3. Type your Mac's IP address into the input field.
4. Click **Connect to Mac**. 

Both application window status bars will turn **Green** indicating a successful, active wireless audio link!

### Step 3: Route Audio on your Mac
To use the voice stream inside third-party apps:
1. Open **System Settings > Sound** on your Mac.
2. Select the **Input** tab.
3. Choose **BlackHole 2ch** or **VB-Cable** as your system microphone.
4. (Optional) Open Zoom or Teams and change your microphone setting to match the virtual audio cable.

---

## 🔧 Architecture Overview

BridgeVoice operates via a standard multi-threaded client-server model:
* **The Server (Mac):** Opens a persistent TCP network socket listening on port `50005`, capturing streaming PCM chunks and pushing them down into the Core Audio system framework via PyAudio.
* **The Client (Windows):** Hooks directly into the WASAPI system audio driver loopback layer, capturing low-latency raw `Int16` dual-channel audio packets at a clean 44.1kHz sample rate, instantly piping them across the socket network pipeline.
* **Threading:** Network and audio processing loops run entirely inside isolated background daemon threads, keeping the `guizero` UI mainloop fully active, responsive, and stutter-free.

---

## 📝 License
This project is open-source and free to use, modify, or adapt for personal accessibility requirements.

