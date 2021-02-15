from pathlib import Path
import subprocess
import pandas as pd
import numpy as np
from .segment_extract import read_audio_section

def run_inaseg(input_wav, csv_out_dir):
    # TODO: switch out for Python library itself
    subprocess.call(["ina_speech_segmenter.py", "-i", input_wav, "-o", csv_out_dir])

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

def read_csv_out(input_wav, csv_out_dir, sep="\t", calculate_peaks=True):
    output_csv = get_csv_path(input_wav, csv_out_dir)
    csv = pd.read_csv(output_csv, sep=sep)
    csv["time_start"] = pd.to_datetime(csv.start, unit="s").dt.time
    csv["time_stop"] = pd.to_datetime(csv.stop, unit="s").dt.time
    csv["duration"] = csv.stop - csv.start
    if calculate_peaks:
        ranges = zip(csv.start, csv.stop)
        csv["peak"] = calculate_peak_amplitudes(ranges, input_wav)
    return csv

def get_speech_segment_times(csv):
    break_labels = ["noEnergy", "music", "noise"]
    break_idx = csv.labels.isin(break_labels)
    #breaks = csv[break_idx]
    speech = csv[~break_idx]
    return speech

# max_break = breaks[breaks.duration.eq(breaks.duration.max())]
