# Śledzik

Anonymous registration: `POST /api/register/anonymous/` with an empty JSON body
(`{}`). Returns HTTP 201 with `token`, `username`, and `id`. The generated user
has no usable password. Use the token in the `Authorization: Token <token>` header.

The sample loads its action chooser with `POST /api/actions/for-token/`, sending
`{"token": "<tenant token>"}`. The endpoint returns only that tenant's actions.

`GET /api/funnels/<id>/statistics/` returns time-series entries with `created`,
`action`, and `count`. By default, hits are grouped by minute and action, with
`created` set to the bucket's start as an ISO timestamp. Use `?granularity=hour`,
`day`, `month`, or `year` for grouped counts, or `?granularity=created` for exact
stored timestamps (Django's standard microsecond precision). The chart consumes `created`; browser chart
rendering may round submillisecond timestamps.
The chart's Time window selector offers Year, Month, Day, Hour,
30 minutes, 15 minutes, 5 minutes, 1 minute (the default), and 12 seconds. Short API window
values are `30min`, `15min`, `5min`, `1min`, and `12sec`. Windows align to the
clock and include their start but exclude their end.

The Unique Viewers Over Time chart uses the statistics response's `unique_viewers`
series (`created`, `count`). It counts distinct user IDs per window across all
actions in the selected funnel. Repeated hits count once; a returning user counts
again in each window where they act. Anonymous identity follows the saved token,
so clearing storage, changing browsers, or logging out can create a new viewer.

Hosts append (`/etc/hosts`):

```
127.0.0.1 sledzik.soiree.tech
```

Serious pages:

```
http://sledzik.soiree.tech:8000/admin/
http://sledzik.soiree.tech:8000/sample/
http://sledzik.soiree.tech:8000/extension/
http://sledzik.soiree.tech:8000/
```
