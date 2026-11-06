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

    async function registerAnonymous() {
        const response = await fetch(BASE + "/api/register/anonymous/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: "{}"
        });
        if (!response.ok) {
            throw new Error("Anonymous registration failed with HTTP " + response.status);
        }
        const data = await response.json();
        if (data && data.token) {
            setAuthToken(data.token);
        }
        return data;
    }

    async function hit(url, token, userAuthToken) {
        if (!token) {
            throw new Error("Token cannot be empty");
        }
        if (typeof token === "object" && token !== null && typeof token.token === "string") {
            token = token.token;
        }
        if (typeof token === "string" && !token.trim()) {
            throw new Error("Token cannot be empty");
        }

        const payload = JSON.stringify({ token: typeof token === "string" ? token.trim() : token });
        const headers = { "Content-Type": "application/json" };
        let auth = userAuthToken || getAuthToken();
        if (!auth) {
            try {
                const regData = await registerAnonymous();
                auth = regData.token;
            } catch (error) {
                // Fall back if anonymous registration fails
            }
        }
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

    return {
        hit: hit,
        getUrl: getUrl,
        setAuthToken: setAuthToken,
        getAuthToken: getAuthToken,
        registerAnonymous: registerAnonymous
    };
})();
