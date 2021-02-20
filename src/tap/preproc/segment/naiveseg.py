import soundfile as sf
import numpy as np
from .segment_extract import read_audio_section
from tqdm import tqdm
from sys import stderr

__all__ = ["moving_average", "pause_estimator", "estimate_pauses"]


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
    return ret[window_size - 1 :] / window_size


def pause_estimator(row_idx, *args):
    d = {row_idx: estimate_pauses(*args)}
    return d


def estimate_pauses(
    audio_file,
    output_wav,
    start_time,
    stop_time,
    min_s=5.0,
    max_s=60.0,
    window_s=0.4,
    verbose=False,
    show_progress=False,
):
    """
    In the absence of an intelligent segmentation from `inaSpeechSegmenter`,
    estimate where the pauses could reasonably be in the audio, returning
    a sequence of segmentations that would split the track to constituent
    segments each between `min_s` and `max_s` in duration.

    Suggested: `min_s` no smaller than `2.0`, for reasonable spaced segments,
    either `5.0` (default) or `10.0`. Since `min_s` is the gap to be left
    between segments, `window_s` must be less than half the size of `min_s`.
    [Note that `window_s` can be interpreted as the expected length of a pause,
    and matches those observed in INA Speech Segmenter output.]

    Calculate the mean amplitude of each `window_s`-width bin, and select those
    at least `min_s` apart, until the maximum interval between the selected
    minima is less than `max_s`.
    """
    if min_s < 2 * window_s:
        raise ValueError(
            f"{window_s=} must not be greater than or equal to {0.5 * min_s=}"
        )
    segment_frames = []
    track = sf.SoundFile(audio_file)
    audio_input, sr = read_audio_section(audio_file, start_time, stop_time)
    min_sf = min_s * sr  # Convert unit of `min_s` from seconds to frames
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
    segment_stops = []
    pbar_goal = total_frames - min_sf  # Track progress to reducing max. seg. to `min_s`
    if show_progress:
        pbar = tqdm(
            desc=f"Estimating naive segmentation for {output_wav.name}", total=pbar_goal
        )
    last_max_segment_len = max_segment_len  # for tqdm updates
    # if output_wav.name == "output_263.wav":
    #    verbose = True
    while max_segment_len > (max_s * sr):
        # Assign each frame of audio to a mean amplitude bin
        digitised = np.digitize(abs_mono_audio, bins)
        rolling_avgs = moving_average(digitised, bin_frame_width)
        min_idx = rolling_avgs.argmin()  # get index of lowest mean amplitude bin
        # if min_idx == 26718:
        #    breakpoint()
        if verbose:
            print(f"Trying new seg {min_idx}", file=stderr)
        # min_idx is both an index of rolling avg window and segment start frame
        new_seg_start = min_idx / sr  # convert segment start unit from frame to s
        new_seg_stop = new_seg_start + window_s
        new_seg_stop_frame = int(new_seg_stop * sr)
        # Ensure no existing segment plus/minus `min_sf` gets segmented
        seg_dists_from_existing = np.abs(np.subtract(segment_stops, new_seg_stop_frame))
        new_seg_is_too_near_existing_seg = np.any(seg_dists_from_existing < min_sf)
        do_not_add_new_seg = new_seg_is_too_near_existing_seg  # or new_seg_too_small
        if not do_not_add_new_seg:
            # No need to zfill the `n_new_segments` count as it's rewritten afterwards
            # Increment `n_new_segments` by 1 so the initial segment can be the zero
            new_output_filename = (
                f"{output_wav.stem}_{n_new_segments+1}{output_wav.suffix}"
            )
            new_output_wav = output_wav.parent / new_output_filename
            new_segment = [
                audio_file,
                new_output_wav,
                new_seg_start,
                new_seg_stop,
                "s",
                window_s,
            ]
            # redundant as audio_file|unit|window_s are repeated, new_output_wav
            # is temporary, new_seg_start can be calculated from new_seg_stop
            segment_frames.append(new_segment)
            n_new_segments += 1
        # Exclude half a `window_s` either side of the end of the new segment interval.
        # `seg_avoid_on` precedes min_idx since `min_s < 2 * window_s` has been ensured
        half_min_sf = min_sf // 2
        # Clip to 0 after subtraction rather than checking if new stop > half_min_sf
        seg_avoid_on = int(np.clip(new_seg_stop_frame - half_min_sf, 0, None))
        seg_avoid_off = int(new_seg_stop_frame + half_min_sf)
        # Mark the excluded interval as max. amplitude so it has a high mean and repeat
        abs_mono_audio[seg_avoid_on : seg_avoid_off + 1] = max_amp
        if not do_not_add_new_seg:
            segment_stops = sorted([(s[3] * sr) for s in segment_frames])
            # Note: the first and last segment are presumed (will be added afterward)
            segment_lengths = np.diff([0, *segment_stops, total_frames])
            if verbose:
                print(f" {segment_stops=}", file=stderr)
                print(f" {segment_lengths=}", file=stderr)
            reduction_since_last_seg = np.clip(
                last_max_segment_len - max_segment_len, 0, None
            )
            # update_by = reduction_since_last_seg
            if show_progress:
                pbar.update(reduction_since_last_seg)
            last_max_segment_len = max_segment_len
            max_segment_len = segment_lengths.max()  # convert max. from frames to s
            if verbose:
                print(
                    f" - Identified {min_idx=} "
                    f"({new_seg_start:.2f} seconds of {total_frames / sr:.2f})"
                    f" - new {max_segment_len=} ({max_segment_len/sr:.2f} seconds)",
                    file=stderr,
                )
    if show_progress:
        pbar.update(pbar.total - pbar.n)  # Finish
    if verbose:
        print(
            f"Successfully estimated a segmentation of {len(segment_frames)} splits,"
            f" max. segment length {max_segment_len / sr:.2f} seconds",
            file=stderr,
        )
    for seg_i, segment in enumerate(segment_frames):
        # Offset each time by start_time to go from relative to absolute count
        for j in range(2, 4): # positions 2 and 3 correspond to the
            segment[j] += start_time
        segment_frames[seg_i] = tuple(segment) # Finally change to immutable tuple
    # Lastly, add the start and end (simple!)
    if not do_not_add_new_seg:
        # No need to zfill the `n_new_segments` count as it's rewritten afterwards
        init_fname, final_fname = (
            f"{output_wav.stem}_{n}{output_wav.suffix}"
            for n in (0, n_new_segments+1)
        )
        extrema_outputs = (
            output_wav.parent / fname
            for fname in [init_fname, final_fname]
        )
        min_new_start = min(x[2] for x in segment_frames)
        max_new_stop = max(x[3] for x in segment_frames)
        extrema_times = (start_time, min_new_start), (max_new_stop, stop_time)
        init_segment, final_segment = (
            [
                audio_file,
                out_name,
                t_start,
                t_stop,
                "s",
                window_s,
            ]
            for out_name, (t_start, t_stop) in zip(extrema_outputs, extrema_times)
        )
        # redundant as audio_file|unit|window_s are repeated, new_output_wav
        # is temporary, new_seg_start can be calculated from new_seg_stop
        segment_frames.insert(0, init_segment)
        segment_frames.append(final_segment)
    return segment_frames
