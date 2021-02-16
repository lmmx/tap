import soundfile as sf

def read_audio_section(filename, start_time, stop_time):
    track = sf.SoundFile(filename)
    if not track.seekable:
        raise ValueError("Not compatible with seeking")
    sr = track.samplerate
    start_frame = int(sr * start_time)
    frames_to_read = int(sr * (stop_time - start_time))
    track.seek(start_frame) 
    audio_section = track.read(frames_to_read)
    return audio_section, sr

def extract_as_clip(input_filename, output_filename, start_time, stop_time):
    audio_extract, sr = read_audio_section(input_filename, start_time, stop_time)
    sf.write(output_filename, audio_extract, sr)
    return
