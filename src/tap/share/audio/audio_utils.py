import soundfile as sf

__all__ = ["get_track_length"]

def get_track_length(wav_file, unit="frames"):
    """
    Return the track length either in seconds (unit: "s") or frames (unit: "frames").
    Always returns both the track length and the sample rate (AKA frame rate).
    """
    track = sf.SoundFile(wav_file)
    sr = track.samplerate
    if unit == "frames":
        track_length = track.frames
    elif unit == "s":
        track_length = track.frames / sr
    else:
        raise ValueError(f"Unrecognised unit {unit} (expected 's' or 'frames')")
    return track_length, sr
