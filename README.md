# Śledzik

Tenants have multiple owners. The admin provides an owners selector, and the
tenant API accepts an `owners` list of user IDs. Creation always includes the
requesting user; existing owners can update the list, which cannot be empty.
All owners share access to the tenant's projects, funnels, actions, and statistics.

Actions have an `order` field within each funnel. Lower values appear first;
ties use the action ID. Existing actions default to 0, preserving their ID order.
Edit the sequence in the funnel admin's action rows, the action list, or the
action API (`PATCH /api/actions/<id>/` with `{"order": 10}`). The sample chooser
and funnel chart follow this sequence. Statistics include an `action_order`
array so clients can preserve ordering even for action names containing numbers.

The dashboard's Total visits counter sums recorded action hits across all tenants
owned by the signed-in user. It refreshes every 30 seconds while the page is
visible. `GET /api/visits/` returns `{"visits": 123}` and requires a user auth token.
This measures action hits, including repeat hits, rather than separate page loads.

See the [browser integration guide](docs/integration.md) for setup with
`extension.js` and `sample.js`, client methods, token handling, and troubleshooting.

Anonymous registration: `POST /api/register/anonymous/` with an empty JSON body
(`{}`). Returns HTTP 201 with `token`, `username`, and `id`. The generated user
has no usable password. Use the token in the `Authorization: Token <token>` header.

The sample loads its action chooser with `POST /api/actions/for-token/`, sending
`{"token": "<tenant token>"}`. The endpoint returns only that tenant's actions.
Its behavior lives in `templates/sample.js`, served at `/sample.js`, and uses
`window.Śledzik` from `extension.js` to authorize, send hits, and log out.

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

On `/etc/hosts` changed.
```
http://sledzik.soiree.tech/admin/
http://sledzik.soiree.tech/sample/
http://sledzik.soiree.tech/extension/
http://sledzik.soiree.tech/
```

On `ngrok` domains configured:
```
https://proud-amazingly-filly.ngrok-free.app/admin/
https://proud-amazingly-filly.ngrok-free.app/sample/
https://proud-amazingly-filly.ngrok-free.app/extension/
https://proud-amazingly-filly.ngrok-free.app/
```
