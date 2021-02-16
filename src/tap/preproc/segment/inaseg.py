from pathlib import Path
import subprocess
import pandas as pd
import numpy as np
from glob import glob
from itertools import count
from functools import partial
from .segment_extract import read_audio_section, extract_as_clip
from ...share.audio import get_track_length
from ...share.multiproc import batch_multiprocess

__all__ = [
    "run_inaseg",
    "get_csv_path",
    "calculate_peaks",
    "read_csv_out",
    "get_segment_times",
    "update_wav_counter",
    "segment_intervals_from_ranges",
    "segment_at_breaks_and_spread",
]

DEFAULT_MIN_S = 5.0

def run_inaseg(input_wav, csv_out_dir):
    # TODO: switch out for Python library itself
    subprocess.call(["ina_speech_segmenter.py", "-i", input_wav, "-o", csv_out_dir])
    return get_csv_path(input_wav, csv_out_dir)


def get_csv_path(input_wav, csv_out_dir):
    csv_name = input_wav.stem + ".csv"
    csv_path = Path(csv_out_dir) / csv_name
    return csv_path


def calculate_peaks(segment_ranges, input_wav):
    peak_amps = []
    for start, stop in segment_ranges:
        audio_section, sr = read_audio_section(input_wav, start, stop)
        peak_amps.append(np.abs(audio_section).max())
    return peak_amps


def read_csv_out(input_wav, csv_out_dir, sep="\t", calculate_peaks=False):
    """
    Read an InaSeg output CSV file, optionally calculating the peak amplitudes
    for each segment (default: do not calculate), return a pandas DataFrame
    containing the segmentation time ranges.
    """
    output_csv = get_csv_path(input_wav, csv_out_dir)
    csv = pd.read_csv(output_csv, sep=sep)
    csv["time_start"] = pd.to_datetime(csv.start, unit="s").dt.time
    csv["time_stop"] = pd.to_datetime(csv.stop, unit="s").dt.time
    csv["duration"] = csv.stop - csv.start
    if calculate_peaks:
        ranges = zip(csv.start, csv.stop)
        csv["peak"] = calculate_peak_amplitudes(ranges, input_wav)
    return csv


def get_segment_times(csv_df, breaks=None, no_energy=False, music=False, noise=False):
    """
    Filter an InaSeg output CSV of segmented time ranges.

    The parameters `no_energy`, `music`, and `noise` are optional bools which
    filter for the "noEnergy", "music", "noise" labels in segmented time ranges.
    These are the 'breaks', i.e. the parts labelled as anything other than speech.
    The "noEnergy" label corresponds to 'gaps' or 'pauses' in the audio.

    If all three are False (default), they will all be flipped to True and included.

    If any one or two of the three is True, these will be the only break label
    included in the results.

    If `breaks` is None (default) then return all rows after filtering. If `breaks`
    is True, only return the non-speech rows, else if `breaks` is False, only return
    the speech rows (this last option is known as "speaker segmentation").
    """
    if not (no_energy | music | noise):
        no_energy = music = noise = True
    break_labels = []
    noe_str = "noEnergy" if no_energy else ""
    mus_str = "music" if music else ""
    noi_str = "noise" if noise else ""
    break_labels = " ".join([noe_str, mus_str, noi_str]).split()
    break_idx = csv_df.labels.isin(break_labels)
    if breaks is True:
        breaks = csv_df[break_idx]
        return breaks
    elif breaks is False:
        speech = csv_df[~break_idx]
        return speech
    elif breaks is None:
        return csv_df
    else:
        raise ValueError(f"{breaks=} is invalid: only True, False, or None are allowed")


def update_wav_counter(clip_counter, zfill_len, out_dir, wav_stem, wav_suff):
    clip_count = next(clip_counter)
    zf_count = str(clip_count).zfill(zfill_len)
    output_wav = out_dir / f"{wav_stem}_{zf_count}{wav_suff}"
    return output_wav


def segment_intervals_from_ranges(
    input_wav, segment_range_df, segmented_out_dir, min_s=DEFAULT_MIN_S
):
    """
    Segmentation of files from input file. The algorithm proceeds row by row through the
    DataFrame `segment_range_df` and creates clips from the row start to the row end,
    except when the duration indicated on the row is below `min_s`, in which case the
    row's duration is instead accumulated as the `clip_duration`.
    """
    prev_end_pt = 0.0
    since_prev_end_pt = 0.0
    clip_counter = count()  # uninitialised: becomes 0 on first `next` call
    zfill_len = len(str(len(segment_range_df)))  # number of digits of row count
    get_next_wav_name = partial(
        update_wav_counter,
        zfill_len=zfill_len,
        out_dir=segmented_out_dir,
        wav_stem=input_wav.stem,
        wav_suff=input_wav.suffix,
    )
    extraction_params = []  # presumed parameter: `input_wav`
    clip_unit = "s"
    for row_idx, row in segment_range_df.iterrows():
        since_prev_end_pt = row.stop - prev_end_pt
        if since_prev_end_pt > min_s:
            output_wav = get_next_wav_name(clip_counter)
            clip_params = (input_wav, output_wav, prev_end_pt, row.stop, clip_unit)
            extraction_params.append(clip_params)  # Postpone extraction (multiprocess)
            prev_end_pt = row.stop
    total_frames, sr = get_track_length(input_wav, unit="frames")
    final_params = extraction_params[-1]
    fin_in, fin_out, fin_start, fin_end, fin_unit = final_params
    fin_unit = "frames"  # rather than "s"
    if (total_frames / sr) - fin_end > min_s:
        # If remaining time span is greater than `min_s`, make it a new clip
        prev_end_pt = int(fin_end * sr)
        output_wav = get_next_wav_name(clip_counter)
        new_final_params = (fin_in, output_wav, prev_end_pt, total_frames, fin_unit)
        extraction_params.append(new_final_params)
    else:
        # Modify final extraction_params entry so final clip extends to the final frame
        new_fin_start = int(
            fin_start * sr
        )  # scale start of last clip from seconds to frames
        final_params = (fin_in, fin_out, new_fin_start, total_frames, fin_unit)
        extraction_params[-1] = final_params  # reassign the final entry
    func_list = [
        partial(extract_as_clip, *arg_tuple) for arg_tuple in extraction_params
    ]
    batch_multiprocess(func_list)


def segment_at_breaks_and_spread(
    input_wav, csv_out_dir=None, segmented_out_dir=None, min_s=DEFAULT_MIN_S
):
    if csv_out_dir is None:
        csv_out_dir = input_wav.parent
    if segmented_out_dir is None:
        segmented_out_dir = csv_out_dir / "segmented"
        if segmented_out_dir.exists() and glob(str(segmented_out_dir / "*.wav")):
            raise ValueError(f"Segmented files already exist in {segmented_out_dir}")
        else:
            segmented_out_dir.mkdir(exist_ok=True)
    if not get_csv_path(input_wav, csv_out_dir).exists():
        csv_out = run_inaseg(input_wav, csv_out_dir) # verbose/slow step
    csv_df = read_csv_out(input_wav, csv_out_dir)
    pause_segments = get_segment_times(csv_df, breaks=True, no_energy=True)
    # Create segmented output WAV files using all cores
    segment_intervals_from_ranges(
        input_wav, pause_segments, segmented_out_dir, min_s=min_s
    )


# max_break = breaks[breaks.duration.eq(breaks.duration.max())]
