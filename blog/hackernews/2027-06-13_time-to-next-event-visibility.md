# Show HN: Persistent "Time to Next Event" in the Browser Toolbar

*Hacker News post · June 13, 2027*

---

One of the features in [Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — our Google Calendar Chrome extension — is a small "in X min" display in the browser toolbar that shows continuously updated time until your next event.

We added this as a minor feature. It turned out to be the most commented-on thing in our reviews.

## The behavioral effect

The ambient display changes task selection decisions at transitions.

Without time visibility: you finish one task and start whatever seems reasonable, often underestimating how close the next meeting is. You start a substantial piece of work with 15 minutes available, get interrupted 12 minutes in, and leave it in a broken state.

With time visibility: "in 17 min" is always visible. You choose a bounded task for 17 minutes rather than an open-ended one. You prepare for the meeting 2 minutes out rather than scrambling when the notification fires.

## The psychology

This is similar to the effect of having a visible countdown timer on tasks (time boxing). External visibility of a deadline changes behavior even when the person knows the deadline abstractly. Seeing "in 17 min" produces a different response than knowing your next meeting is at 2:30.

## The implementation

Background service worker polling Google Calendar API every minute (or on event changes). Extension badge text updated with minutes until next event. Display format: "12m" (abbreviated), transitions to event title display when imminent.

Edge cases that required thought: multiple simultaneous events (all-day events vs. time-specific events), events with no defined end time, events that have been modified since last sync, timezone display for events in non-local zones.

## Performance considerations

The background polling is the obvious concern. We settled on: on-demand fetch when the popup opens, plus a background worker that wakes every 60 seconds to update the badge text. CPU usage is negligible; the periodic Calendar API call is the cost.

Happy to discuss the implementation details or behavioral patterns we've observed.
