import soundfile as sf
import numpy as np
from .segment_extract import read_audio_section

def moving_average(values, window_size):
    """
    Calculate the unweighted moving average over `window_size` items
    from `values` at a time. The index of an entry in the resulting
    moving averages vector corresponds to the interval `[i, i + w]`
    where `w` is specified as the argument `window_size` (meaning
    there are `len(values) - window_size` moving averages in total).
    """
    ret = np.cumsum(values, dtype=float)
    ret[window_size:] = ret[window_size:] - ret[:-window_size]
    return ret[window_size - 1:] / window_size

def estimate_pauses(audio_file, output_wav, start_time, stop_time, min_s=5., max_s=60., window_s=0.4):
    """
    In the absence of an intelligent segmentation from `inaSpeechSegmenter`,
    estimate where the pauses could reasonably be in the audio, returning
    a sequence of segmentations that would split the track to constituent
    segments each between `min_s` and `max_s` in duration.

    Suggested: `min_s` no smaller than `2.0`, for reasonable spaced segments,
    either `5.0` (default) or `10.0`.

    Calculate the mean amplitude of each `window_s`-width bin, and select those
    at least `min_s` apart, until the maximum interval between the selected
    minima is less than `max_s`.
    """
    if min_s < 2 * window_s:
        raise ValueError(f"{window_s=} must not be greater than or equal to {0.5 * min_s=}")
    segment_frames = []
    track = sf.SoundFile(audio_file)
    audio_input, sr = read_audio_section(audio_file, start_time, stop_time)
    min_sf = min_s * sr # Convert unit of `min_s` from seconds to frames
    total_frames = len(audio_input)
    bin_frame_width = int(window_s * sr)
    # Make as many bins as needed to slide the `window_s` across the entire audio track
    n_bins = total_frames - bin_frame_width
    abs_mono_audio = np.abs(audio_input).mean(axis=1)
    max_amp = abs_mono_audio.max()
    # Create bins for the range of amplitudes
    bins = np.linspace(0, max_amp, n_bins)
    # Exclude `window_s` at either end, by pretending they have uniform max. amplitude
    abs_mono_audio[:bin_frame_width] = abs_mono_audio[-bin_frame_width:] = max_amp
    max_segment_len = total_frames
    n_new_segments = 0
    while max_segment_len > (max_s * sr):
        digitised = np.digitize(abs_mono_audio, bins)
        rolling_avgs = moving_average(digitised, bin_frame_width)
        min_idx = rolling_avgs.argmin() # get index of lowest mean amplitude bin
        new_seg_start = min_idx / sr
        new_seg_stop = new_seg_start + window_s
        new_seg_stop_frame = new_seg_stop * sr
        # The moving average at index `i` corresponds to the interval `[i, i+w]`
        #min_idx_centre = min_idx + bin_frame_width // 2 # interval centre: `i + (w/2)`
        new_output_filename = f"{output_wav.stem}_{n_new_segments}{output_wav.suffix}"
        new_output_wav = output_wav.parent / new_output_filename 
        new_segment = (
            audio_file, new_output_wav, new_seg_start, new_seg_stop, "s", window_s
        )
        segment_frames.append(new_segment)
        # Exclude half a `window_s` either side of the end of the new segment interval
        seg_avoid_on = int(new_seg_stop_frame - min_sf // 2)
        seg_avoid_off = int(new_seg_stop_frame + min_sf // 2)
        # Mark the excluded interval as max. amplitude so it has a high mean and repeat
        abs_mono_audio[seg_avoid_on:seg_avoid_off+1] = max_amp
        segment_stops = sorted([(s[3] * sr) for s in segment_frames])
        segment_lengths = np.diff([0, *segment_stops, total_frames])
        print(f" {segment_stops=}")
        print(f" {segment_lengths=}")
        max_segment_len = segment_lengths.max() # convert max. from frames to s
        print(f" - Identified {min_idx=} "
              f"({new_seg_start} seconds of {total_frames / sr})"
              f" - new {max_segment_len=}")
    print(f"Successfully estimated a segmentation of {len(segment_frames)} splits,"
          f" max. segment length {max_segment_len / sr} seconds")
    breakpoint()
    return segment_frames
