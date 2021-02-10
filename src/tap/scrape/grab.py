from subprocess import call
from pathlib import Path
from ..data.store.channels import _dir_path as data_dir
from ..share.cal import cal_path, cal_shift, cal_date, parse_abs_from_rel_date
from .streams import Stream
from .link_file_handling import handle_link_file

__all__ = ["get_program_urls"]


def get_program_urls(
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
    *filename_prefix, last_file_num = last_filename.stem.rpartition("-")
    filename_prefix = "".join(filename_prefix)

    if filename_prefix == "":
        # rpartition gives two empty strings and the original string if separator not found
        raise ValueError("Failed to parse filename (did not contain '-' separator)")

    try:
        last_file_num_int = int(last_file_num)
    except ValueError as e:
        raise ValueError(f"{last_file_num} was non-numeric")

    def construct_url(int_i, url_prefix=url_prefix, filename_prefix=filename_prefix):
        return url_prefix + filename_prefix + str(int_i) + url_suffix

    urls = [construct_url(i) for i in range(1, last_file_num_int + 1)]
    # for i in range(1, last_file_num+1):
    #    url_i = construct_url(i)
    stream = Stream(channel, station, program, ymd, urls)
    return stream
