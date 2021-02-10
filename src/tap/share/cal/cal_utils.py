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
