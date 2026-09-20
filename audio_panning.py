import sys
import subprocess
import numpy as np
import wave

def analyze_audio(video_path):
    # Extract audio to wav
    wav_path = "temp.wav"
    subprocess.run(f"ffmpeg -y -i {video_path} -vn -acodec pcm_s16le -ac 2 -ar 44100 {wav_path}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    wf = wave.open(wav_path, 'rb')
    nframes = wf.getnframes()
    audio = np.frombuffer(wf.readframes(nframes), dtype=np.int16)
    audio = audio.reshape(-1, 2) # Left and Right channels
    
    fps = 30
    samples_per_frame = 44100 // fps
    
    results = []
    for i in range(0, len(audio), samples_per_frame):
        chunk = audio[i:i+samples_per_frame]
        if len(chunk) == 0: break
        
        chunk = chunk.astype(np.float32)
        rms_L = np.sqrt(np.mean(chunk[:, 0]**2))
        rms_R = np.sqrt(np.mean(chunk[:, 1]**2))
        
        diff = rms_L - rms_R
        results.append(diff)
        
    for i, diff in enumerate(results[:30]): # print first second
        print(f"Frame {i}: L-R = {diff:.2f}")

if __name__ == "__main__":
    analyze_audio(sys.argv[1])
