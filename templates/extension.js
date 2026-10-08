window.Śledzik = (function () {
    const BASE = "http://śledzik.pl:8000";

    function getUrl(actionId) {
        return BASE + "/api/actions/" + encodeURIComponent(actionId) + "/hit/";
    }

    function hit(url, token) {
        const payload = JSON.stringify({ token: token });

        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload,
            keepalive: true
        });
    }

    return { hit: hit, getUrl: getUrl };
})();
