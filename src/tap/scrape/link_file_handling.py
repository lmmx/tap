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
            raise ValueError(f"No link file for {recording_id} on {cal_datestr}")
    return link_file
