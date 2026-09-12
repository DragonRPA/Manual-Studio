# -*- coding: utf-8 -*-
import os
import asyncio
import wave
import subprocess
import imageio_ffmpeg
import edge_tts

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

async def _synthesize_edge_tts(text: str, voice: str, rate: str, output_mp3: str):
    """Synthesizes speech using Edge-TTS."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_mp3)

def convert_mp3_to_wav(mp3_path: str, wav_path: str):
    """Converts MP3 to 16-bit 44.1kHz WAV for exact duration and mixing."""
    cmd = [
        FFMPEG_EXE, "-y", "-i", mp3_path,
        "-ar", "44100", "-ac", "2", "-f", "wav", wav_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def get_wav_duration(wav_path: str) -> float:
    """Returns duration of WAV in seconds."""
    with wave.open(wav_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)

def create_silence_wav(duration_sec: float, output_wav: str):
    """Generates a silent WAV file of given duration."""
    cmd = [
        FFMPEG_EXE, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(duration_sec), "-f", "wav", output_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def concatenate_wav_files(wav_files: list, output_master_wav: str):
    """Concatenates multiple WAV files into a single master audio file."""
    concat_list_txt = output_master_wav + ".list.txt"
    with open(concat_list_txt, "w", encoding="utf-8") as f:
        for w in wav_files:
            clean_path = os.path.abspath(w).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
    
    cmd = [
        FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_txt, "-c", "copy", output_master_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if os.path.exists(concat_list_txt):
        os.remove(concat_list_txt)

def generate_scenario_audio(scenario: dict, temp_dir: str):
    """
    Generates all TTS voice files for the scenario scenes,
    calculates precise scene timelines, and creates master audio track.
    
    Returns:
        (master_audio_wav_path, scene_timelines, total_duration)
    """
    voice = scenario.get("voice", "ko-KR-SunHiNeural")
    rate = scenario.get("rate", "+12%")
    scenes = scenario.get("scenes", [])
    
    scene_timelines = []
    wav_files = []
    current_time = 0.0
    
    # Initial silence 0.3s
    init_silence = os.path.join(temp_dir, "init_silence.wav")
    create_silence_wav(0.3, init_silence)
    wav_files.append(init_silence)
    current_time += 0.3
    
    for idx, scene in enumerate(scenes):
        narration = scene.get("narration", "").strip()
        mp3_path = os.path.join(temp_dir, f"scene_{idx}.mp3")
        wav_path = os.path.join(temp_dir, f"scene_{idx}.wav")
        
        # 1. Synthesize TTS
        asyncio.run(_synthesize_edge_tts(narration, voice, rate, mp3_path))
        
        # 2. Convert to WAV & get duration
        convert_mp3_to_wav(mp3_path, wav_path)
        speech_duration = get_wav_duration(wav_path)
        
        # 3. Add pause
        pause_wav = os.path.join(temp_dir, f"pause_{idx}.wav")
        pause_duration = 0.35 if idx < len(scenes) - 1 else 0.8
        create_silence_wav(pause_duration, pause_wav)
        
        scene_total_duration = speech_duration + pause_duration
        scene_start = current_time
        scene_end = scene_start + scene_total_duration
        
        wav_files.append(wav_path)
        wav_files.append(pause_wav)
        
        timeline_entry = {
            "scene_index": idx,
            "scene_id": scene.get("id", f"scene_{idx}"),
            "visual_type": scene.get("visual_type", "ui_demo"),
            "badge": scene.get("badge", ""),
            "title_main": scene.get("title_main", ""),
            "subtitle_lines": scene.get("subtitle_lines", []),
            "highlight_words": scene.get("highlight_words", []),
            "image_asset": scene.get("image_asset"),
            "motion": scene.get("motion", "zoom_in"),
            "start_time": scene_start,
            "end_time": scene_end,
            "duration": scene_total_duration,
            "speech_duration": speech_duration
        }
        scene_timelines.append(timeline_entry)
        current_time = scene_end
        
    master_wav = os.path.join(temp_dir, "master_narration.wav")
    concatenate_wav_files(wav_files, master_wav)
    total_duration = get_wav_duration(master_wav)
    
    return master_wav, scene_timelines, total_duration
