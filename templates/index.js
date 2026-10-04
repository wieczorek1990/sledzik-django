window.Sledzik = (function () {
    const BASE = "https://śledzik.pl:8000";
    const TOKEN = "ed74e235-7a7f-4190-b3c9-6a04258ed899";

    function hit(actionId, callback) {
        const url = BASE + "/api/actions/" + encodeURIComponent(actionId) + "/hit/";
        const payload = JSON.stringify({ token: TOKEN });

        if (navigator.sendBeacon && !callback) {
            navigator.sendBeacon(url, new Blob([payload], {type: "application/json"}));
            return;
        }

        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload,
            keepalive: true
        })
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                if (callback) callback(null, data);
            })
            .catch(function (err) {
                if (callback) callback(err);
            });
    }

    return { hit: hit };
})();
