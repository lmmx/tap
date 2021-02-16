from pathlib import Path
import subprocess
import pandas as pd
import numpy as np
from glob import glob
from .segment_extract import read_audio_section, extract_as_clip

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

# TODO
def segment_audio_at_breaks(input_wav, csv_out_dir=None, segmented_out_dir=None):
    if csv_out_dir is None:
        csv_out_dir = input_wav.parent
    if segmented_out_dir is None:
        segmented_out_dir = csv_out_dir / "segmented"
        if segmented_out_dir.exists() and glob(segmented_out_dir / "*.wav"):
            raise ValueError(f"Segmented files already exist in {segmented_out_dir}")
        else:
            segmented_out_dir.mkdir(exist_ok=True)
    csv_out = run_inaseg(input_wav, csv_out_dir)
    csv_df = read_csv_out(input_wav, csv_out_dir)
    pause_segments = get_segment_times(csv_df, breaks=True, no_energy=True)
    # TODO: segmentation I/O based on `pause_segments`
    #segment_from_df_ranges(pause_segments)

# max_break = breaks[breaks.duration.eq(breaks.duration.max())]
