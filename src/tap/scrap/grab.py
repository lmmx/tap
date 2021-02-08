from subprocess import call
from pathlib import Path

__all__ = ["all_urls"]

out_dir = Path.home() / "dev" / "tap" / "bbc" / "r4" / "today" / "2021" / "02feb" / "21/02feb/08"

with open("last-link.txt", "r") as f:
    last_link_url = f.read().strip()

last_filename = Path(Path(last_link_url).name)
url_prefix = last_link_url[:-len(last_filename.name)]
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

all_urls = [construct_url(i) for i in range(1, last_file_num+1)]
#for i in range(1, last_file_num+1):
#    url_i = construct_url(i)
