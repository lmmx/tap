import warnings
from matplotlib import MatplotlibDeprecationWarning
from pathlib import Path
import pandas as pd
import numpy as np
from glob import glob
from itertools import count
from functools import partial
from .segment_extract import read_audio_section, extract_as_clip
from .naiveseg import pause_estimator#, estimate_pauses
from ...share.audio import get_track_length
from ...share.pandas import insert_replacement_rows
from ...share.multiproc import batch_multiprocess, batch_multiprocess_with_dict_updates

__all__ = [
    "run_inaseg",
    "get_csv_path",
    "calculate_peaks",
    "read_csv_out",
    "get_segment_times",
    "update_wav_counter",
    "segment_intervals_from_ranges",
    "segment_pauses_and_spread",
]


def run_inaseg(input_wav, csv_out_dir):
    # load neural network into memory, may last few seconds
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=MatplotlibDeprecationWarning)
        from inaSpeechSegmenter import Segmenter
    seg = Segmenter(vad_engine="smn", detect_gender=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stem = input_wav.stem
        input_files = [str(input_wav)]
        output_files = [str(csv_out_dir / f"{stem}.csv")]
        seg.batch_process(input_files, output_files, verbose=True)
    #subprocess.run(["ina_speech_segmenter.py", "-i", input_wav, "-o", csv_out_dir])
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
    input_wav, segment_range_df, segmented_out_dir, min_s, max_s, dry_run=False,
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
    # Just revert the final row's unit to seconds rather than handling in pandas
    final_params = extraction_params[-1]
    if final_params[-1] == "frames":
        s_fin_params = (*final_params[:2], final_params[2]/sr, final_params[3]/sr, "s")
        extraction_params[-1] = s_fin_params
    # Now switch to pandas and handle the naive segmentation pass to reduce to `max_s`
    segment_time_df = pd.DataFrame(
        dict(zip("input output start stop unit".split(), zip(*extraction_params)))
    )
    surplus_duration = (segment_time_df.stop - segment_time_df.start).gt(max_s)
    if surplus_duration.any():
        # Estimate a finer segmentation by estimating pauses based on amplitude minima
        surplus_duration_intervals = segment_time_df[surplus_duration]
        sdi = surplus_duration.copy()
        pause_estimator_funcs = []
        # Wrap returned value as a dict to update `segment_interval_replacements` with
        #pause_estimator = lambda i, *args: {i: estimate_pauses(*args)}
        for row_idx, row in surplus_duration_intervals.iterrows():
            assert row.unit == "s" # All frame units must be replaced by now
            estim_params = row.input, row.output, row.start, row.stop, min_s, max_s
            f = partial(pause_estimator, row_idx, *estim_params)
            pause_estimator_funcs.append(f)
        # Multiprocess on all cores, updating `segment_interval_replacements` dict with
        # each returned dict entry of `{row_idx: estimate_pauses(...)}`
        segment_interval_replacements = batch_multiprocess_with_dict_updates(
            function_list=pause_estimator_funcs,
            tqdm_desc=f"Segmenting audio into clips between {min_s}s and {max_s}s",
        )
        # Reorder by time, rename output wav with zfilled count, convert to intervals
        reorder_rename_segment_replacements_as_intervals(segment_interval_replacements)
        # Calculate interval ranges that correspond to the new segmentation ranges
        segment_time_df = insert_replacement_rows(
            segment_time_df, segment_interval_replacements
        )
    # Re-assign extraction params with modifications indicating further segmentations
    extraction_params = [*map(tuple, segment_time_df.itertuples(index=False))]
    func_list = [
        partial(extract_as_clip, *arg_tuple) for arg_tuple in extraction_params
    ]
    if not dry_run:
        batch_multiprocess(func_list, tqdm_desc="Saving segment interval WAVs")
    return segment_time_df


def reorder_rename_segment_replacements_as_intervals(replacements_dict):
    """
    Update the input dictionary in-place: reorder the replacement
    values by the start time (the third entry) and 
    """
    zf = len(str(max(map(len, replacements_dict.values()))))
    unnecessary_replacements_idx = []
    for row_idx, replacement_rows in replacements_dict.items():
        # A single replacement row doesn't need reordering, since initial and
        # final intervals (NB: not segment ranges) already added, a single
        # replacement row will have length 3
        if len(replacement_rows) > 3: # initial and final intervals already added
            # Sort replacement rows in chronological order
            replacement_rows = sorted(replacement_rows, key=get_start_time)
        else:
            unnecessary_replacements_idx.append(row_idx)
            continue
        # The `replacement_rows` are capped by init/final intervals, which must
        # be merged with the (2nd and penultimate) contiguous segment ranges
        # All replacement rows between first and last are made into intervals
        n_replacement_rows = len(replacement_rows)
        for row_j, row in enumerate(replacement_rows):
            replacement_rows = list(map(list, replacement_rows))
            if row_j == 0:
                # Pop the first interval and only keep its start time
                # thus merging its interval range with the first segment
                replacement_rows[0][2] = replacement_rows.pop(0)[2]
            elif row_j == n_replacement_rows - 2:
                # Pop the final interval and only keep its stop time
                # thus merging its interval range with the last segment
                replacement_rows[-1][3] = replacement_rows.pop()[3]
                break # Avoid IndexError from pre-indexed iterator
            else:
                # The current segment interval starts where the previous stopped
                replacement_rows[row_j][2] = replacement_rows[row_j-1][3]
        # Lastly, rename the output filenames to reflect the sorted order
        replacements_dict[row_idx] = rename_by_order(replacement_rows, zf)

##### Helper functions for reorder_rename_segment_replacements_as_intervals #####

def get_start_time(replacement_row):
    return replacement_row[2] # becomes the 'start' column of the DataFrame

def rename_by_order(rows, zfill_len):
    """
    Modify the 2nd item in each `row` tuple, given `rows` (a list of tuples).
    """
    for i, row_tuple in enumerate(rows):
        # Renumber the files incrementing by 1 so the initial segment can be zero
        new_filename = renumber_filename(row_tuple[1], i+1, zfill_len)
        rows[i] = tuple(x if j != 1 else new_filename for j,x in enumerate(row_tuple))
    return rows # Note: it's modified in-place too

def renumber_filename(filename, i, zfill_len):
    """
    Discard the numbered part of the filename and renumber according to its
    new position in the list of replacement rows to be inserted (passed as `i`).
    E.g. from ".../segmented/output_035_6.wav" to ".../segmented/output_035_012.wav"
    when `i` = 12 and `zfill` = 3.
    """
    filename_prefix = filename.stem.rpartition("_")[0]
    new_number = str(i).zfill(zfill_len)
    new_filename = f"{filename_prefix}_{new_number}{filename.suffix}"
    #print(f"Renaming {filename.name} as {new_filename} ({i}:{zfill_len} -> {new_number})")
    return filename.parent / new_filename

####################################################################################

def segment_pauses_and_spread(
    input_wav, csv_out_dir=None, segmented_out_dir=None, min_s=5., max_s=50.
):
    """
    Calculate the audio segmentation of the `input_wav` file by calling
    `inaSpeechSegementer` (unfortunately this uses threads for batch processing
    and so does not use all cores at maximal efficiency), producing a TSV in
    `csv_out_dir` (by default this will be the parent directory of `input_wav`).

    Once the segmentation is computed, go on to calculate the intervals inclusive of
    the gaps between these segments (from the start of the audio to the end of the
    first pause, then from the end of the first pause to the start of the second pause,
    and so on, until the final pause which is merged up to the end of the track).

    If there are already files in a segmented directory, assume already computed
    (delete the directory or the wav files in it if this is not the case, e.g.
    if the computation was interrupted).

    Return the segment intervals (note: these are the start- and end-inclusive
    intervals as opposed to the segmentation ranges provided by `inaSpeechSegmenter`
    which only cover the 'pauses', the segment intervals cover the entire audio).
    """
    if csv_out_dir is None:
        csv_out_dir = input_wav.parent
    if segmented_out_dir is None:
        segmented_out_dir = csv_out_dir / "segmented"
    dry_run = segmented_out_dir.exists() and glob(str(segmented_out_dir / "*.wav"))
    segmented_out_dir.mkdir(exist_ok=True)
    if not get_csv_path(input_wav, csv_out_dir).exists():
        csv_out = run_inaseg(input_wav, csv_out_dir)  # verbose/slow step
    csv_df = read_csv_out(input_wav, csv_out_dir)
    pause_segments = get_segment_times(csv_df, breaks=True, no_energy=True)
    # Create segmented output WAV files using all cores
    segment_intervals = segment_intervals_from_ranges(
        input_wav, pause_segments, segmented_out_dir, min_s=min_s, max_s=max_s, dry_run=dry_run,
    )
    return segment_intervals, segmented_out_dir


# max_break = breaks[breaks.duration.eq(breaks.duration.max())]
