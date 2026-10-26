window.Śledzik = (function () {
    const BASE = "http://sledzik.soiree.tech:8000";
    let authToken = null;

    function setAuthToken(token) {
        authToken = token;
    }

    function getUrl(actionId) {
        return BASE + "/api/actions/" + encodeURIComponent(actionId) + "/hit/";
    }

    function hit(url, token, callback, userAuthToken) {
        if (!token || (typeof token === "string" && !token.trim())) {
            const error = new Error("Token cannot be empty");
            if (typeof callback === "function") {
                callback({ ok: false, status: 400, statusText: "Bad Request", error: error });
            }
            return Promise.reject(error);
        }

        const payload = JSON.stringify({ token: typeof token === "string" ? token.trim() : token });
        const headers = { "Content-Type": "application/json" };
        const auth = userAuthToken || authToken || window.localStorage.getItem("authorization");
        if (auth) {
            headers["Authorization"] = "Token " + auth;
        }

        return fetch(url, {
            method: "POST",
            headers: headers,
            body: payload,
            keepalive: true
        }).then(function (response) {
            if (typeof callback === "function") {
                callback(response);
            }
            return response;
        });
    }

    return { hit: hit, getUrl: getUrl, setAuthToken: setAuthToken };
})();
