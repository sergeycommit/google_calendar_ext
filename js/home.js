// Homepage demo: lays the popup's timeline out around the visitor's own clock,
// then keeps the now-line, countdown chips and toolbar badge ticking.
(function () {
    var track = document.querySelector('[data-track]');
    if (!track) return;

    var PX_PER_MIN = 1.2;          // matches the 72px hour spacing in home.css
    var WINDOW_MIN = 260;          // ~4 hours of timeline (track is 312px)
    var MIN = 60000;

    var loaded = new Date();
    var start = new Date(loaded.getTime() - 70 * MIN);   // now sits 70 min into the window
    var roundUp = function (d, step) {
        var t = Math.ceil(d.getTime() / (step * MIN)) * step * MIN;
        return new Date(t);
    };
    var roundDown = function (d, step) {
        return new Date(Math.floor(d.getTime() / (step * MIN)) * step * MIN);
    };

    // The next meeting starts 10–25 min after page load, so the countdown is real.
    var nextStart = roundUp(new Date(loaded.getTime() + 10 * MIN), 15);
    var events = {
        past: { start: roundDown(new Date(loaded.getTime() - 55 * MIN), 5), dur: 25 },
        next: { start: nextStart, dur: 30 },
        later: { start: new Date(nextStart.getTime() + 90 * MIN), dur: 30 }
    };

    var clock = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' });
    var fmt = function (d) { return clock.format(d); };
    var hourLabel = new Intl.DateTimeFormat(undefined, { hour: 'numeric' });
    var y = function (d) { return ((d.getTime() - start.getTime()) / MIN) * PX_PER_MIN; };
    var until = function (d, now) {
        var mins = Math.round((d.getTime() - now.getTime()) / MIN);
        if (mins <= 0) return 'now';
        if (mins < 60) return 'in ' + mins + ' min';
        var h = Math.floor(mins / 60), m = mins % 60;
        return 'in ' + h + ' h' + (m ? ' ' + m + ' m' : '');
    };

    var today = document.querySelector('[data-today]');
    if (today) {
        today.textContent = loaded.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
    }

    // Hour lines: the first full hour inside the window, then every 60 min.
    var firstHour = roundUp(start, 60);
    track.querySelectorAll('.h-hour').forEach(function (el, i) {
        var at = new Date(firstHour.getTime() + i * 60 * MIN);
        el.style.top = y(at) + 'px';
        el.querySelector('span').textContent = hourLabel.format(at);
        el.hidden = y(at) > WINDOW_MIN * PX_PER_MIN;
    });

    Object.keys(events).forEach(function (key) {
        var ev = events[key];
        var el = track.querySelector('[data-event="' + key + '"]');
        if (!el) return;
        ev.el = el;
        el.style.top = y(ev.start) + 'px';
        el.querySelector('[data-time]').textContent =
            fmt(ev.start) + ' – ' + fmt(new Date(ev.start.getTime() + ev.dur * MIN));
    });

    var nowLine = track.querySelector('[data-now]');
    var badge = document.querySelector('[data-badge]');

    function tick() {
        var now = new Date();
        if (nowLine) nowLine.style.top = Math.min(y(now), WINDOW_MIN * PX_PER_MIN) + 'px';
        ['next', 'later'].forEach(function (key) {
            var chip = events[key].el && events[key].el.querySelector('[data-chip]');
            if (chip) chip.textContent = until(events[key].start, now);
        });
        if (badge) {
            var mins = Math.max(0, Math.round((events.next.start.getTime() - now.getTime()) / MIN));
            badge.textContent = mins ? mins + 'm' : 'now';
        }
    }

    tick();
    setInterval(tick, 15000);
})();
