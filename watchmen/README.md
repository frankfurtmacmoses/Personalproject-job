# Watchmen
The watchmen project currently monitors several feeds and processes. This project was
created because of silent failures leading to missing data leaving questions about what
happened. This project serves to catch these errors and explain what issues occurred.

## Project Info
### Reaper Feeds
This project currently monitors several feeds that submit straight to Reaper. These feeds
are broken up into 3 categories:
**hourly feeds**, **daily feeds**, **weekly feeds**.

NOTE:\
Current method for monitor feed is querying the Reaper metrics table!

Each class contains a dictionary called **FEEDS_TO_CHECK** which contains all the feeds
being monitored. They are structured like this:
```
FEEDS_TO_CHECK_<TYPE> = {'feed_name': {'metric_name': <NAME> min': <NUM>, 'max': <NUM>}}
```
For each feed a minimum value and a maximum value is set and an alarm will be raised
if the metric name returns an associated number outside of this range. If no min or max
is needed simply place 0 for min and sys.maxint for max.

Hourly:
```
FEEDS_TO_CHECK_HOURLY = {'feed_name': {'metric_name': <NAME> min': <NUM>, 'max': <NUM>}}
```
Fields are the same as above.\
For the list below you will have to add the actual name that displays in the
logs at the beginning.\
For example if you see:
```
zeus-tracker-scraper/zeus-tracker-scraper-prod/ffe50104-5272-4832-bf83-5ae02c6f85f6
```
Then zeus-tracker-scraper is what you would insert into the list. Nothing
else should be added after the first slash.\
**IMPORTANT NOTE**: Even if the name is identical still add it otherwise it will not work.
You will also notice some feeds have very different names from what's listed in the logs,
please keep this in mind when adding to this list. 
```
FEEDS_HOURLY_NAMES = [
                      'bambenek-ip-scraper', 'cox-feed', 'cybercrime-scraper', 'ecrimex-scraper',
                      'g01-dga', 'tracker-h3x-eu-scraper', 'vxvault-scraper', 'ransomware-tracker-scraper',
                      'zeus-tracker-scraper'
]
```


Daily:

Same as hourly must be added as well for all daily feeds.
```

FEEDS_DAILY_NAMES = [
                     'feodo-scraper', 'ff-goz-dga', 'locky-dga-scraper', 'malc0de-scraper',
                     'tor-exit-node-scraper'
]
```
```
FEEDS_TO_CHECK_DAILY = {'feed_name': {'metric_name': <NAME> min': <NUM>, 'max': <NUM>, 'hour_submitted': <HOUR>}}
```
The hour submitted requires a specific hour in which the metric was submitted. For
example if a feed submits daily at 09:00 (UTC) then you must place the hour submitted as
'09'.\
 **Important to remember the 0 at the front**.
 
Weekly:\
Same as daily and hourly as well.
```
FEEDS_WEEKLY_NAMES = [
                      'ponmocup-scraper'
]
```

```
FEEDS_TO_CHECK_WEEKLY = {'feed_name': {'metric_name': <NAME> min': <NUM>, 'max': <NUM>, 'hour_submitted': <HOUR>, 'days_to_subtract': <NUM>}}
```
Since the weekly feed Watchmen runs once a week on Friday. In order to get the current date we have to set the date
a integer value. Currently it goes as following:
```
Saturday: 6
Sunday: 5
Monday: 4
Tuesday: 3
Wednesday: 2
Thursday: 1
Friday: 0
```
Along with that is the hour it was submitted on that day.

To run any of these watchmen individually you will need to add:
```
main({'type':<Hourly, Daily, Weekly>', None)
```
Choose one of the three above.\
At the bottom of the script to ensure the added feed does not cause issues.
## Getting Started: Dev Setup
Running a dev-setup script to install the project and libraries
```
make clean dev-setup
```
IMPORTANT NOTE:\
You must have configurations for the Pypi server. This means you must
have a .pip configuration file and .pydistutils file in order to get the cyberint python 
packages.

## Testing
After running the previous command now you can start running unit tests on the current
code. To run all tests:

```
make test-all
```
or to start a clean test (you should do this before adding changes)
```
make clean test-all
```

After tests are completed you should see the results in the following format:

```
---------- coverage: platform linux2, python 2.7.12-final-0 ----------
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
watchmen/__init__.py                       0      0   100%
watchmen/main.py                          11      0   100%
watchmen/manhattan_daily.py               31      0   100%
watchmen/manhattan_hourly.py              31      0   100%
watchmen/manhattan_weekly.py              31      0   100%
watchmen/moloch.py                        51      0   100%
watchmen/silhouette.py                    39      0   100%
watchmen/utils/__init__.py                 0      0   100%
watchmen/utils/universal_watchmen.py      74      0   100%
----------------------------------------------------------
TOTAL                                    268      0   100%
Coverage HTML written to dir htmlcov
```


To view individual test coverage go to
```
cyberint-watchmen/htmlcov/<YOUR_FILE> 
```
to view testing coverage.

## Deployment
The deployment may vary depending on what is added to the cloud formation template.
Once the changes are added to the master branch in Infoblox-CTO then Jenkins will
automatically run against there environment.
If completed then Jenkins has a build called:
 
**cyberint-watchmen-deploy**

That needs to be manually ran at the moment. In other cases you can deploy to 
production with:
```
make deploy-cf-prod
```