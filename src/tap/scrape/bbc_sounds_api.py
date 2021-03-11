from xml.etree import ElementTree as ET
from json import loads
import requests
from .isotime import total_seconds_in_isoduration
from math import ceil

__all__ = ["scrape_ep_pid_from_parent_pid", "final_m4s_link_from_pid"]

def scrape_ep_pid_from_parent_pid(series_pid, ymd):
    ...

def final_m4s_link_from_pid(episode_pid):
    """
    Scrape the DASH manifest (MPD file) to determine the URL of the final M4S file
    (MPEG stream), using the episode's duration divided by the... sampling rate?
    """
    verpid = episode_pid
    pid_json_url = f"https://www.bbc.co.uk/programmes/{episode_pid}/playlist.json"
    pid_json_resp = requests.get(pid_json_url)
    pid_json_resp.raise_for_status()
    pid_json = loads(pid_json_resp.content.decode())
    verpid = pid_json["defaultAvailableVersion"]["pid"]
    mediaset_v = 6
    mediaset_url = (
        f"https://open.live.bbc.co.uk/mediaselector/{mediaset_v}/"
        f"select/version/2.0/mediaset/pc/vpid/{verpid}"
    )
    mediaset_resp = requests.get(mediaset_url)
    mediaset_resp.raise_for_status()
    mediaset_json = loads(mediaset_resp.content.decode())
    if mediaset_json.get("result") == "selectionunavailable":
        raise ValueError(f"Bad mediaset response from {episode_pid}")
    # `sorted()[0]` with the key 'priority' gives 'top' choice of 3 suppliers
    mpd_url = sorted(
        [
            x for x in mediaset_json["media"][0]["connection"]
            if x["transferFormat"] == "dash"
            if x["protocol"] == "https"
        ],
        key=lambda e: int(e["priority"])
    )[0]["href"]
    mpd_resp = requests.get(mpd_url)
    mpd_resp.raise_for_status()
    mpd_resp_xml = ET.fromstring(mpd_resp.content.decode())
    duration_string = mpd_resp_xml.get("mediaPresentationDuration")
    sec_duration = total_seconds_in_isoduration(duration_string)
    # Choose the highest bitrate option (there are 2 AdaptationSet options)
    xsd_namespace = mpd_resp_xml.items()[0][1].split()[0]
    ns_xpath = f"{{{xsd_namespace}}}"
    # Assume a single period duration (so use `find` not `findall`)
    period_xpath = f"{ns_xpath}Period"
    bitrate_opt_xpath = f"{ns_xpath}AdaptationSet"
    repr_xpath = f"{ns_xpath}Representation"
    max_bitrate_opt = sorted(
        mpd_resp_xml.find(period_xpath).findall(bitrate_opt_xpath),
        key=lambda t: int(t.find(repr_xpath).get("bandwidth"))
    )[-1] # take the maximum value, the last in the sorted list
    seg_templ_xpath = f"{ns_xpath}SegmentTemplate"
    segment_frames = int(max_bitrate_opt.find(seg_templ_xpath).get("duration"))
    sample_rate = int(max_bitrate_opt.get("audioSamplingRate"))
    n_m4s_parts = ceil(sec_duration * sample_rate / segment_frames)
    base_url_xpath = f"{ns_xpath}BaseURL"
    mpd_base_url = mpd_resp_xml.find(period_xpath).find(base_url_xpath).text
    segment_frames = int(max_bitrate_opt.find(seg_templ_xpath).get("duration"))
    repr_id = max_bitrate_opt.find(repr_xpath).get("id")
    media_url_suff = max_bitrate_opt.find(seg_templ_xpath).get("media")
    media_suff_parts = media_url_suff.split("$")
    media_suff_parts[1::2] = repr_id, str(n_m4s_parts)
    m4s_link_prefix = mpd_url[:mpd_url.rfind("/") + 1]
    last_m4s_suffix = "".join(media_suff_parts)
    last_m4s_link = m4s_link_prefix + mpd_base_url + last_m4s_suffix
    return last_m4s_link
