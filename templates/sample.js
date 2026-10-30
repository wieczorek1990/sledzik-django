$(function () {
    const tracker = window.Śledzik;
    const $tokenInput = $("#token");
    const $actionInput = $("#action");
    const $hitButton = $("#hit");
    const $userInfo = $("#user-info");
    const $status = $("#status");
    const tokenStorageKey = "śledzik.sample.tenantToken";
    let authorizationPromise = null;
    let session = 0;
    let actionsRequest = 0;
    let actionsTimer;

    async function postJSON(url, data = {}) {
        try {
            return await $.ajax({
                url,
                method: "POST",
                contentType: "application/json",
                dataType: "json",
                data: JSON.stringify(data)
            });
        } catch (request) {
            throw new Error(request.status ? `Request failed (HTTP ${request.status}).` : "Could not reach the server.");
        }
    }

    async function loadActions() {
        const requestId = ++actionsRequest;
        const token = rememberToken();
        const previousAction = $actionInput.val();
        $actionInput.prop("disabled", true);
        $hitButton.prop("disabled", true);
        $actionInput.empty().append(new Option(token ? "Loading actions..." : "Enter a token to load actions", ""));
        if (!token) return;
        try {
            const actions = await postJSON("{% url 'token-actions' %}", { token });

            if (requestId !== actionsRequest) return;
            $actionInput.empty().append(...actions.map(action =>
                new Option(`${action.name} (#${action.id})`, String(action.id))
            ));
            if (actions.some(action => String(action.id) === previousAction)) $actionInput.val(previousAction);
            if (!actions.length) $actionInput.empty().append(new Option("No actions for this token", ""));
            $actionInput.prop("disabled", !actions.length);
            $hitButton.prop("disabled", !actions.length);
            $status.text("");
        } catch (error) {
            if (requestId !== actionsRequest) return;
            $actionInput.empty().append(new Option("Actions unavailable", ""));
            $status.text(error.message);
        }
    }

    try {
        $tokenInput.val(window.localStorage.getItem(tokenStorageKey) || "");
    } catch (error) {
        // The sample still works when browser storage is disabled.
    }

    function rememberToken() {
        const token = $tokenInput.val().trim();
        try {
            if (token) window.localStorage.setItem(tokenStorageKey, token);
            else window.localStorage.removeItem(tokenStorageKey);
        } catch (error) {
            // Keep using the input when browser storage is disabled.
        }
        return token;
    }

    async function authorize() {
        const savedToken = tracker.getAuthToken();
        if (savedToken) {
            $userInfo.text("Authorized with saved anonymous token.");
            return savedToken;
        }
        if (!authorizationPromise) {
            const currentSession = session;
            authorizationPromise = (async () => {
                const data = await postJSON("{% url 'api-register-anonymous' %}");
                if (currentSession !== session) return null;
                tracker.setAuthToken(data.token);
                $userInfo.text("Authorized as: " + data.username);
                return data.token;
            })().finally(() => {
                if (currentSession === session) authorizationPromise = null;
            });
        }
        return authorizationPromise;
    }

    function tokenChanged() {
        rememberToken();
        actionsRequest++;
        $actionInput.prop("disabled", true);
        $hitButton.prop("disabled", true);
        clearTimeout(actionsTimer);
        actionsTimer = setTimeout(loadActions, 300);
    }
    $tokenInput.on("input change", tokenChanged);
    $("#logout").on("click", () => {
        session++;
        authorizationPromise = null;
        tracker.setAuthToken(null);
        $userInfo.text("Logged out.");
        $status.text("");
        $hitButton.prop("disabled", $actionInput.prop("disabled"));
    });
    $hitButton.on("click", async () => {
        const currentSession = session;
        const token = rememberToken();
        const actionId = $actionInput.val();
        if (!token || $actionInput.prop("disabled") || !actionId) {
            $status.text("Enter a valid token and choose an action.");
            return;
        }
        $hitButton.prop("disabled", true);
        const currentActionsRequest = actionsRequest;
        $status.text("Sending hit...");
        try {
            const authToken = await authorize();
            if (currentSession !== session || currentActionsRequest !== actionsRequest) return;
            const response = await tracker.hit(tracker.getUrl(actionId), token, null, authToken);
            if (currentSession !== session || currentActionsRequest !== actionsRequest) return;
            $status.text(response.ok
                ? "Hit sent successfully!"
                : "Hit failed (e.g. invalid or rejected token).");
        } catch (error) {
            if (currentSession === session && currentActionsRequest === actionsRequest) $status.text("Error sending hit: " + error.message);
        } finally {
            if (currentSession === session && currentActionsRequest === actionsRequest) $hitButton.prop("disabled", $actionInput.prop("disabled"));
        }
    });

    loadActions();
    authorize().catch(error => {
        if (session === 0) $status.text("Authorization error: " + error.message);
    });
});
