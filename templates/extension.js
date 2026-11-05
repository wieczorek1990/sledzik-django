window.Śledzik = (function () {
    const script = document.currentScript;
    const BASE = script && script.src
        ? new URL(script.src, window.location.href).origin
        : window.location.origin;
    let authToken = null;

    function setAuthToken(token) {
        authToken = token;
        try {
            if (token) {
                window.localStorage.setItem("authorization", token);
            } else {
                window.localStorage.removeItem("authorization");
            }
        } catch (error) {
            // Keep using the in-memory token when browser storage is unavailable.
        }
    }

    function getAuthToken() {
        if (!authToken) {
            try {
                authToken = window.localStorage.getItem("authorization");
            } catch (error) {
                // Browser storage may be disabled.
            }
        }
        return authToken;
    }

    function getUrl(actionId) {
        return BASE + "/api/actions/" + encodeURIComponent(actionId) + "/hit/";
    }

    async function hit(url, token, userAuthToken) {
        if (!token || (typeof token === "string" && !token.trim())) {
            throw new Error("Token cannot be empty");
        }

        const payload = JSON.stringify({ token: typeof token === "string" ? token.trim() : token });
        const headers = { "Content-Type": "application/json" };
        const auth = userAuthToken || getAuthToken();
        if (auth) {
            headers["Authorization"] = "Token " + auth;
        }

        return await fetch(url, {
            method: "POST",
            headers: headers,
            body: payload,
            keepalive: true
        });
    }

    return { hit: hit, getUrl: getUrl, setAuthToken: setAuthToken, getAuthToken: getAuthToken };
})();
