from subprocess import call
from pathlib import Path
from ..data.store.channels import _dir_path as data_dir
from ..share.cal import cal_path, cal_shift, cal_date, parse_abs_from_rel_date
from .streams import Stream
from .link_file_handling import handle_link_file
from .stream_url_handling import construct_urlset

__all__ = ["load_stream"]


def load_stream(
    channel="bbc", station="r4", program="today", ymd=None, ymd_ago=None
):
    ymd = parse_abs_from_rel_date(ymd, ymd_ago)
    cal_subpath = cal_path(ymd)

    prog_date_dir = data_dir / channel / station / program / cal_subpath

    link_file = handle_link_file(data_dir, channel, station, program, cal_subpath)
    with open(link_file, "r") as f:
        last_link_url = f.read().strip()

    last_filename = Path(Path(last_link_url).name)
    url_prefix = last_link_url[: -len(last_filename.name)]
    url_suffix = last_filename.suffix
    fname_prefix, fname_sep, last_file_num = last_filename.stem.rpartition("-")

    if fname_prefix == fname_sep == "":
        # rpartition gives two empty strings and the original string if separator not found
        raise ValueError("Failed to parse filename (did not contain '-' separator)")

    try:
        last_file_num_i = int(last_file_num)
    except ValueError as e:
        raise ValueError(f"{last_file_num} was non-numeric")

    # This should use StreamUrlSet
    urlset = construct_urlset(last_file_num_i, url_prefix, fname_prefix, fname_sep, url_suffix)
    # for i in range(1, last_file_num+1):
    #    url_i = construct_url(i)
    stream = Stream(channel, station, program, ymd, urlset)
    return stream
