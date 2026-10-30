# Śledzik

Anonymous registration: `POST /api/register/anonymous/` with an empty JSON body
(`{}`). Returns HTTP 201 with `token`, `username`, and `id`. The generated user
has no usable password. Use the token in the `Authorization: Token <token>` header.

`GET /api/funnels/<id>/statistics/` returns time-series entries with `created`,
`action`, and `count`. By default, hits are grouped by minute and action, with
`created` set to the bucket's start as an ISO timestamp. Use `?granularity=hour`,
`day`, `month`, or `year` for grouped counts, or `?granularity=created` for exact
nanosecond timestamps. The chart consumes `created`; browser chart
rendering may round submillisecond timestamps.
The chart's Time window selector offers Year, Month, Day, Hour,
30 minutes, 15 minutes, 5 minutes, 1 minute (the default), and 12 seconds. Short API window
values are `30min`, `15min`, `5min`, `1min`, and `12sec`. Windows align to the
clock and include their start but exclude their end.

Hosts append (`/etc/hosts`):

```
127.0.0.1 sledzik.soiree.tech
```

Serious pages:

```
http://sledzik.soiree.tech:8000/admin/
http://sledzik.soiree.tech:8000/sample/
http://sledzik.soiree.tech:8000/
```
