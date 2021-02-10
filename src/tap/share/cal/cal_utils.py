from subprocess import run
from pathlib import Path
import datetime as DT
from datetime import date as cal_date  # , datetime as dt
from dateutil.relativedelta import relativedelta as rd

__all__ = [
    "cal_y", "cal_m", "cal_d",
    "cal_path",
    "y_shift", "m_shift", "d_shift",
    "cal_shift", "cal_date",
    "parse_abs_from_rel_date",
]

def cal_y(date=cal_date.today()):
    """
    Equivalent to `date +"%y"`
    """
    return date.strftime("%y")


def cal_m(date=cal_date.today()):
    """
    Equivalent to `date +"%m%b" | tr "A-Z" "a-z"`
    """
    return date.strftime("%m%b").lower()


def cal_d(date=cal_date.today()):
    """
    Equivalent to `date +"%d"`
    """
    return date.strftime("%d")


def cal_path(date=cal_date.today()):
    y, m, d = [f(date) for f in (cal_y, cal_m, cal_d)]
    return Path(y) / m / d


def y_shift(y=0, date=cal_date.today()):
    return date + rd(years=y) if y != 0 else date


def m_shift(m=0, date=cal_date.today()):
    return date + rd(years=m) if m != 0 else date


def d_shift(d=0, date=cal_date.today()):
    return date + rd(days=d) if d != 0 else date


def cal_shift(y=0, m=0, d=0, date=cal_date.today()):
    return date + rd(years=y, months=m, days=d) if any([y, m, d]) else date

def parse_abs_from_rel_date(ymd=None, ymd_ago=None):
    if ymd is ymd_ago is None:
        ymd = cal_date.today()
    else:
        # If ymd was supplied, do type conversion if passed as int tuple
        if isinstance(ymd, tuple):
            if all(map(lambda i: isinstance(i, int), ymd)):
                ymd = cal_date(*ymd)
            else:
                raise TypeError(f"{ymd=} is neither a datetime.date nor integer tuple")
        if all([ymd, ymd_ago]):
            # both ymd and ymd_ago are not None (i.e. are supplied) so shift accordingly
            ymd = cal_shift(*ymd_ago, date=ymd)
        elif ymd_ago:
            ymd = cal_shift(*ymd_ago)
        # else implies ymd was supplied
    # In each of the above cases `ymd` is now a `datetime.date` object
    return ymd
