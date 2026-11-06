# Integrating Śledzik

`extension.js` is the browser tracking client, exposed as `window.Śledzik`.
`sample.js` is a jQuery example that connects the client to a token input,
action chooser, Hit button, and Logout button.

The source files are Django templates. Load their rendered routes:

Opening `/extension/` in a browser tab shows an HTML source preview with the
site favicon. Script requests receive JavaScript as before; `/extension.js`
always returns raw JavaScript. Responses vary by `Sec-Fetch-Dest` so caches keep
the document preview separate from the script.

| Source | URL | Dependencies |
| --- | --- | --- |
| `templates/extension.js` | `/extension/` | Browser APIs; no jQuery |
| `templates/sample.js` | `/sample.js` | jQuery, `extension.js`, and the HTML below |

## Tokens and setup

Create a tenant, project, funnel, and actions through the admin or management API.
Copy the tenant's UUID token from the tenant record in the admin.

There are two different tokens:

| Token | Purpose | Where it goes |
| --- | --- | --- |
| Tenant token | Selects the tenant and authorizes hits for its actions | JSON `token` field; the sample's Token input |
| User auth token | Identifies the viewer submitting a hit | `Authorization: Token <value>` header |

Anonymous authorization creates a user with an unusable password and returns a
user auth token. It does not create a tenant or actions.

## Use the complete sample

Open `/sample/` for the existing integration. To build another page on the same
Śledzik origin, use this markup:

```html
<label for="token">Token:</label>
<input id="token" type="text" size="40">

<label for="action">Action:</label>
<select id="action" disabled>
    <option value="">Enter a token to load actions</option>
</select>

<button id="hit" type="button" disabled>Hit</button>
<button id="logout" type="button">Logout</button>
<div id="user-info"></div>
<div id="status" role="status"></div>

<script src="https://code.jquery.com/jquery-4.0.0.min.js"></script>
<script src="/extension/"></script>
<script src="/sample.js"></script>
```

Keep the element IDs and script order. In a Django template, the script URLs can
use `{% url 'extension' %}` and `{% url 'sample-js' %}` instead.

The sample:

1. Restores the tenant token and starts anonymous authorization if no user token exists.
2. Loads the tenant's actions and fills the chooser with their names and IDs.
3. Reloads actions 300 ms after the token changes, ignoring older responses.
4. Sends one hit for the selected action when Hit is clicked.
5. Clears the user auth token on Logout, keeping the tenant token and chooser.

Hit is disabled while actions load or when the token has no available actions.
After Logout, the next Hit creates a new anonymous identity. Reloading the page
also starts authorization if there is no saved user token.

## Use the extension in your own UI

Load `/extension/` before your code. The following example uses the browser's
`fetch` API; jQuery and `sample.js` are not required for a custom integration.

```javascript
async function trackAction(tenantToken, actionId) {
    const tracker = window.Śledzik;
    if (!tracker.getAuthToken()) {
        const response = await fetch('/api/register/anonymous/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: '{}'
        });
        if (!response.ok) throw new Error(`Authorization failed: ${response.status}`);
        const user = await response.json();
        tracker.setAuthToken(user.token);
    }

    const response = await tracker.hit(tracker.getUrl(actionId), tenantToken);
    if (!response.ok) throw new Error(`Hit failed: ${response.status}`);
    return response.json();
}

// Use a tenant token and an action ID returned by the actions endpoint.
// await trackAction(tenantToken, actionId);
```

For multiple simultaneous first hits, share one authorization promise, as
`sample.js` does, to avoid creating multiple anonymous users.

### Client methods

| Method | Behavior |
| --- | --- |
| `getUrl(actionId)` | Builds the action's hit URL on the origin that served `/extension/`. |
| `registerAnonymous()` | Creates an anonymous user session on the server, saves the returned token, and returns the registration JSON payload. |
| `setAuthToken(token)` | Sets the in-memory user token and saves it in localStorage. Pass `null` to clear it. |
| `getAuthToken()` | Returns the in-memory token, falling back to localStorage. |
| `hit(url, tenantToken, callback?, userAuthToken?)` | Posts a hit and returns a promise resolving to a Fetch `Response`. If no auth token is currently set, automatically registers anonymously first. |

`hit` chooses the explicit `userAuthToken` argument first, then the stored token.
The optional callback receives the response. An empty tenant token rejects the
promise and calls the callback with an error object. Network failures reject the
promise; HTTP failures such as 401 still resolve, so always check `response.ok`.
A successful hit returns `{"success":"ok"}`.

## Load actions by tenant token

`sample.js` uses jQuery AJAX to call this endpoint:

```javascript
const actions = await $.ajax({
    url: '/api/actions/for-token/',
    method: 'POST',
    contentType: 'application/json',
    dataType: 'json',
    data: JSON.stringify({ token: tenantToken })
});
// Example: [{ id: 42, name: 'ready', funnel: 7 }]
```

This endpoint requires the tenant token, without a user auth token. It returns
only that tenant's actions, an empty array for a tenant without actions, or HTTP
401 for a missing, malformed, or unknown token. Hitting an action additionally
requires a user auth token and a tenant token matching that action's tenant.

## Storage and identity

| localStorage key | Value |
| --- | --- |
| `authorization` | User auth token, managed by the extension |
| `śledzik.sample.tenantToken` | Tenant token, managed by the sample |

Storage belongs to the page's origin. If storage is unavailable, the extension
keeps the user token in memory and the sample uses the entered tenant token for
the current page. Logout clears the local user token; it does not revoke the
server-side token. The dashboard also uses `authorization` on the same origin.

Unique-viewer statistics count distinct user IDs per time window. Reusing the
saved user token preserves that identity; a new browser, cleared storage, or a
new anonymous session can count as another viewer.

## Hosting and troubleshooting

The sample's AJAX URLs resolve relative to the page's origin. The extension's
hit URLs use the origin of the loaded extension script. Serve the sample and API
on the same origin, or configure a same-origin reverse proxy that forwards both
the script routes and `/api/` routes. The project currently has no cross-origin
API configuration; loading the scripts from another host alone does not enable
cross-origin requests.

| Symptom | Check |
| --- | --- |
| `Śledzik` or `$` is undefined | Load jQuery, then `/extension/`, then `/sample.js`. |
| Unresolved Django tags in JavaScript | Load `/sample.js` through Django, rather than copying its template source to a static host. |
| Actions unavailable / HTTP 401 | Use the tenant UUID token in the Token input. |
| No actions for this token | Create actions under a funnel and project belonging to that tenant. |
| Hit returns HTTP 401 | Check both the user auth token and the action's tenant token. A stale user token can be cleared with Logout. |
| `Load failed` / network error | Check the script/API origins, HTTPS, reverse proxy, and browser Network panel. |
