from sys import stderr

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
            msg = f"No link file for {recording_id} on {cal_datestr}"
            #raise ValueError(msg)
            print(msg, file=stderr)
            try:
                input_prompt = f"Enter the URL of the final M4S file for the stream: "
                link = input(input_prompt)
            except KeyboardInterrupt as e:
                raise ValueError(msg)
            else:
                link_file.parent.mkdir(parents=True, exist_ok=True)
                with open(link_file, "w") as f:
                    print(link, file=f)
    return link_file
