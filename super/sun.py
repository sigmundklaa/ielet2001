
from datetime import datetime, date, timedelta
from astral import LocationInfo
from astral.sun import sun as ASun

SR_MARGIN_HR = timedelta(hours=1)
SS_MARGIN_HR = timedelta(hours=- 1)

CITY = LocationInfo('Melhus', 'Norway', 'Europe/Oslo')


def sun() -> ASun:
    return ASun(CITY.observer, date=date(2009, 4, 22))


def is_daytime(t: datetime = datetime.now(),
               srise_margin_hr: timedelta = SR_MARGIN_HR,
               sset_margin_hr: timedelta = SS_MARGIN_HR,
               ) -> bool:
    """Checks whether we are in daytime by comparing the time to the times
    of sunset and sunrise.

    :param t: Time to compare against 
    :param sset_margin_hr: Margin (in hours) from sunset.
    :param srise_margin_hr: Margin (in hours) from sunrise.
    """
    s = sun()
    srise = s['sunrise'] + srise_margin_hr
    sset = s['sunset'] + sset_margin_hr

    return srise < t.replace(tzinfo=srise.tzinfo) < sset
