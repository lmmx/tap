__all__ = ["ensure_stream_dir"]

def ensure_stream_dir(link_dir_path, broadcaster, station, programme_pid, cal_subpath):
    "The function of this is to create a directory"
    if not link_dir_path.exists():
        raise FileNotFoundError(f"{link_dir_path} not found")
    link_file_dir = link_dir_path / broadcaster / station / programme_pid / cal_subpath
    link_file_dir.mkdir(parents=True, exist_ok=True)
