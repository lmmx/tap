import ffmpeg


def mp4_to_wav(input_mp4, sr="16k", output_wav=None):
    """
    Convert an MP4 file to a WAV file at sampling rate `sr` (default 16 kHz).
    If output_dir is None (default), place it in `input_mp4`'s parent
    """
    if output_wav is None:
        output_wav_name = input_mp4.stem + ".wav"
        output_wav = input_mp4.parent / output_wav_name
    ffmpeg.input(filename=input_mp4).output(
        filename=output_wav, ac=2, ar=sr, format="wav"
    ).run(quiet=True)
    return output_wav
