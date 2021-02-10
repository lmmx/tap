from subprocess import call
from pathlib import Path
from ..data.store.channels import _dir_path as data_dir
from ..share.cal import cal_path, cal_shift, cal_date

__all__ = ["get_program_urls"]

_link_filename = "last-link.txt"


def get_program_urls(
    channel="bbc", station="r4", program="today", ymd=None, ymd_ago=None
):
    if ymd is ymd_ago is None:
        cal_subpath = cal_path()  # defaults to today
    elif ymd_ago:
        offset_date = cal_shift(*ymd_ago)
        cal_subpath = cal_path(offset_date)
    # Now know that ymd was supplied, so do type conversion if passed as int tuple
    if isinstance(ymd, tuple):
        if all(map(lambda i: isinstance(i, int), ymd)):
            ymd = cal_date(*ymd)
        else:
            raise TypeError(f"{ymd=} is neither a datetime.date nor integer tuple")
    if all([ymd, ymd_ago]):
        # both ymd and ymd_ago are not None (i.e. are supplied) so calculate date
        offset_date = cal_shift(*ymd_ago, date=ymd)
        cal_subpath = cal_path(offset_date)
    else:  # implies date was supplied
        cal_subpath = cal_path(ymd)

    prog_date_dir = data_dir / channel / station / program / cal_subpath

    link_file = prog_date_dir / _link_filename
    if not link_file.exists():
        recording_id = f"{channel}⠶{station}⠶{program}"
        cal_datestr = " ".join(map(lambda p: p[-3:].title(), cal_subpath.parts[::-1]))
        if not prog_date_dir.exists():
            raise ValueError(f"No records for {recording_id} on {cal_datestr}")
        else:
            raise ValueError(f"No link file for {recording_id} on {cal_datestr}")
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

    all_urls = [construct_url(i) for i in range(1, last_file_num_int + 1)]
    # for i in range(1, last_file_num+1):
    #    url_i = construct_url(i)
    return all_urls
