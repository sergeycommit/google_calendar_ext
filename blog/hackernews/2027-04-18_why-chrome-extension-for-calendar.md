# Show HN: Built a Chrome Extension for One-Click Google Calendar Access

*Hacker News post · April 18, 2027*

---

**The problem:** I was switching to the Google Calendar tab ~30-40 times per day for quick checks: what time is my next meeting, how long until the next event, where's the join link. Each check took 20-40 seconds including tab switching, page load, and returning to context. Multiplied across the day, that's 10-20 minutes of overhead for a task that should take seconds.

**What we built:** [Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — a Chrome extension that puts your Google Calendar in a browser toolbar popup.

## How it works

Click the toolbar icon → calendar appears in a popup showing today's events. Join links for video calls are surfaced directly. The popup closes when you click away. You never leave your current tab.

The toolbar icon also shows "Next event: in X min" so you can check your schedule without even clicking — ambient awareness without any action.

## The design decisions

**No event creation in the popup.** Creating events is a deliberate action that belongs in the full calendar interface. We specifically excluded it to keep the popup fast and focused.

**No configuration required.** The extension connects to whatever Google account is signed into Chrome. No OAuth dance, no settings, no onboarding. It works immediately after installation.

**Free, no subscription.** We make money on the paid tiers of adjacent products. The extension itself is a distribution mechanism, not a revenue source.

## The tech

Chrome extension using the Google Calendar API. OAuth via Chrome's identity API. The popup is a React SPA that renders against the Calendar API data. Load time from click to visible events: <200ms on a good connection.

## What we've learned

The most used feature, by far, is the next-event countdown in the toolbar. People don't click the popup most of the time — they glance at the number in the toolbar and move on. The ambient display is more valuable than we initially expected.

Second most used: the one-click join button for video calls. The reduction from "find the tab → find the event → find the link → click" to "click popup → click Join" is significant enough that several users cited it specifically in reviews.

Happy to answer questions about the technical implementation or the design decisions.
