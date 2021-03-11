from sys import stderr
from ..data.store import channels
from .bbc_api import final_m4s_link_from_episode_pid, final_m4s_link_from_series_pid
from functools import reduce

__all__ = ["handle_link_file"]

_link_filename = "last-link.txt"


def handle_link_file(
    link_dir_path, channel, station, program, cal_subpath, link_filename=_link_filename
):
    link_file = (
        link_dir_path / channel / station / program / cal_subpath / link_filename
    )
    if not link_file.exists():
        recording_id = " ⠶ ".join([channel, station, program])
        cal_datestr = " ".join(map(lambda p: p[-3:].title(), cal_subpath.parts[::-1]))
        if not link_dir_path.exists():
            raise ValueError(f"No records for {recording_id} on {cal_datestr}")
        else:
            try:
                ymd_parts = [*map(lambda p: int(p[:2]), cal_subpath.parts)]
                # Convert internal date to explicit Y, can't assume BBC date is post-Y2K
                ymd_parts[0] = 2000 + ymd_parts[0]
                program_pid = reduce(
                    getattr, [channel, station, program], channels
                ).pid
                link = final_m4s_link_from_series_pid(program_pid, ymd=tuple(ymd_parts))
            except Exception as e:
                raise e
                print(e, file=stderr)
                msg = f"No link file for {recording_id} on {cal_datestr}"
                print(msg, file=stderr)
                try:
                    input_prompt = f"Enter the PID for the stream episode: "
                    episode_pid = input(input_prompt)
                    link = final_m4s_link_from_episode_pid(episode_pid)
                except KeyboardInterrupt as e:
                    raise ValueError(msg)
                else:
                    link_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(link_file, "w") as f:
                        print(link, file=f)
            else:
                link_file.parent.mkdir(parents=True, exist_ok=True)
                with open(link_file, "w") as f:
                    print(link, file=f)
    return link_file
