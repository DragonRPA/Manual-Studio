# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import imageio_ffmpeg
from .tts_generator import generate_scenario_audio
from .visual_renderer import VisualRenderer

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def render_scenario_to_video(scenario: dict, assets_dir: str, output_mp4_path: str, temp_dir: str, fps: int = 30):
    """
    Renders a scenario JSON to 1080x1920 MP4 video.
    """
    title = scenario.get("title", "Shorts Video")
    print(f"[1/4] Generating Neural TTS voice for: {title}...")
    master_wav, scene_timelines, total_duration = generate_scenario_audio(scenario, temp_dir)
    print(f"      TTS generated. Total duration: {total_duration:.2f}s across {len(scene_timelines)} scenes.")
    
    print("[2/4] Initializing visual renderer & assets...")
    renderer = VisualRenderer(assets_dir)
    
    total_frames = int(total_duration * fps)
    print(f"[3/4] Streaming {total_frames} frames ({fps} FPS, 1080x1920) directly to FFmpeg...")
    
    os.makedirs(os.path.dirname(output_mp4_path), exist_ok=True)
    
    # FFmpeg command for raw frame piping
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",               # Read video frames from stdin pipe
        "-i", master_wav,         # Read audio from WAV file
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        output_mp4_path
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Render frame by frame
    for frame_idx in range(total_frames):
        current_time = frame_idx / float(fps)
        
        # Find active scene
        active_scene = scene_timelines[-1]
        for s in scene_timelines:
            if s['start_time'] <= current_time < s['end_time']:
                active_scene = s
                break
                
        frame_img = renderer.render_frame(current_time, total_duration, active_scene, scenario)
        raw_bytes = frame_img.tobytes('raw', 'RGB')
        try:
            proc.stdin.write(raw_bytes)
        except BrokenPipeError:
            break
            
        if frame_idx % (fps * 3) == 0:
            progress_pct = (frame_idx / total_frames) * 100
            print(f"      Rendering progress: {progress_pct:.1f}% ({frame_idx}/{total_frames} frames)")
            
    proc.stdin.close()
    _, stderr = proc.communicate()
    
    if proc.returncode != 0:
        print(f"FFmpeg error:\n{stderr.decode('utf-8', errors='ignore')}")
        raise RuntimeError("FFmpeg encoding failed!")
        
    print(f"[4/4] Video rendered successfully -> {output_mp4_path}")
    return output_mp4_path
