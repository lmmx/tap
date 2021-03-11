from sys import stderr
from .bbc_sounds_api import final_m4s_link_from_pid

__all__ = ["handle_link_file"]

_link_filename = "last-link.txt"

def handle_link_file(link_dir_path, channel, station, program, cal_subpath, link_filename=_link_filename):
    link_file = link_dir_path / channel / station / program / cal_subpath / link_filename
    if not link_file.exists():
        recording_id = " ⠶ ".join([channel, station, program])
        cal_datestr = " ".join(map(lambda p: p[-3:].title(), cal_subpath.parts[::-1]))
        if not link_dir_path.exists():
            raise ValueError(f"No records for {recording_id} on {cal_datestr}")
        else:
            # TODO: automatically scrape the PID for this if available
            # TODO: automatically obtain the link file given the PID
            # pid = scrape_ep_pid_from_parent_pid(parent_pid, ymd)
            # link = final_m4s_link_from_pid(episode_pid)
            msg = f"No link file for {recording_id} on {cal_datestr}"
            #raise ValueError(msg)
            print(msg, file=stderr)
            try:
                input_prompt = f"Enter the PID for the stream episode: "
                episode_pid = input(input_prompt)
                link = final_m4s_link_from_pid(episode_pid)
            except KeyboardInterrupt as e:
                raise ValueError(msg)
            else:
                link_file.parent.mkdir(parents=True, exist_ok=True)
                with open(link_file, "w") as f:
                    print(link, file=f)
    return link_file
