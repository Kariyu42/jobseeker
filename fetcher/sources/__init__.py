"""Each source module exposes `fetch(http) -> list[dict]` built with normalize.job()."""
from . import arbeitnow, himalayas, hn, jobicy, remoteok, remotive, weworkremotely, workingnomads

ALL = {
    "remoteok": remoteok.fetch,
    "remotive": remotive.fetch,
    "arbeitnow": arbeitnow.fetch,
    "himalayas": himalayas.fetch,
    "jobicy": jobicy.fetch,
    "weworkremotely": weworkremotely.fetch,
    "workingnomads": workingnomads.fetch,
    "hackernews": hn.fetch,
}
