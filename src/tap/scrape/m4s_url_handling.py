from sys import stderr
from ..data.store import channels
from beeb.api import final_m4s_link_from_episode_pid, final_m4s_link_from_programme_pid
from functools import reduce

__all__ = ["get_last_m4s_url"]


# TODO the real function of this is to create a directory, make this explicit
def get_last_m4s_url(link_dir_path, channel, station, program, cal_subpath):
    link_file_dir = (
        link_dir_path / channel / station / program / cal_subpath
    )
    # TODO This should be object oriented
    recording_id = " ⠶ ".join([channel, station, program])
    cal_datestr = " ".join(map(lambda p: p[-3:].title(), cal_subpath.parts[::-1]))
    # TODO: directories should not be being handled in this function...
    if not link_dir_path.exists():
        raise ValueError(f"No records for {recording_id} on {cal_datestr}")
    try:
        ymd_parts = [*map(lambda p: int(p[:2]), cal_subpath.parts)]
        # Convert internal date to explicit Y, can't assume BBC date is post-Y2K
        ymd_parts[0] = 2000 + ymd_parts[0]
        programme_pid = reduce(
            getattr, [channel, station, program], channels
        ).pid
        link = final_m4s_link_from_programme_pid(programme_pid, ymd=tuple(ymd_parts))
    except Exception as e:
        raise e
    else:
        link_file_dir.mkdir(parents=True, exist_ok=True)
    return link
