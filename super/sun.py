
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun as ASun

SR_MARGIN = timedelta(hours=1)
SS_MARGIN = timedelta(hours=- 1)

CITY = LocationInfo('Trondheim', 'Norway', 'Europe/Oslo')


def sun(d: datetime) -> ASun:
    return ASun(CITY.observer, date=d, tzinfo=CITY.timezone)


def is_daytime(t: datetime = datetime.now(),
               srise_margin: timedelta = SR_MARGIN,
               sset_margin: timedelta = SS_MARGIN,
               ) -> bool:
    """Checks whether we are in daytime by comparing the time to the times
    of sunset and sunrise.

    :param t: Time to compare against 
    :param srise_margin: Margin from sunrise.
    :param sset_margin: Margin from sunset.
    """
    s = sun(t)
    srise = s['sunrise'] + srise_margin
    sset = s['sunset'] + sset_margin

    return srise < t.replace(tzinfo=srise.tzinfo) < sset
