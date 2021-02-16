import subprocess
from glob import glob

__all__ = []

def gather_m4s_to_mp4(dash_file, m4s_files, output_mp4):
    """
    Concatenate `.dash` and `.m4s` files using the system `cat` facility.
    Files can be passed either as explicit list of filenames or globbed with
    a Kleene-star string (note: Python `glob.glob` is unsorted, do not use).
    """
    if output_mp4.exists():
        raise ValueError(f"{output_mp4=} already exists: risk of doubled output")
    cmd_list = [
        *"for x in".split(),
        f'{dash_file}',
        f'{m4s_files}',
        *"; do cat $x >>".split(),
        f'{output_mp4}',
        *"; done".split(),
    ]
    subprocess.call(cmd_list)
    # TODO: rewrite as glob, this doesn't work

def gather_pulled_downloads(input_dir, output_dir):
    """
    Gather MPEG stream files from input_dir into a single MP4 file in output_dir
    """
    dash_globstr = f"{input_dir.absolute() / '*.dash'}"
    dash_glob = glob(dash_globstr)
    if len(dash_glob) < 1:
        raise ValueError(f"No dash file found in {input_dir}")
    elif len(dash_glob) > 1:
        raise ValueError(f"Multiple dash files found in {input_dir}")
    m4s_globstr = f"{input_dir.absolute() / '*.m4s'}"
    output_mp4 = output_dir.absolute() / "output.mp4"
    gather_m4s_to_mp4(dash_globstr, m4s_globstr, output_mp4)
    return output_mp4
