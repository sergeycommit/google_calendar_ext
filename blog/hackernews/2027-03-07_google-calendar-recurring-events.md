# Google Calendar Recurring Events: Infrastructure Patterns for Weekly Structure

*Hacker News post · March 7, 2027*

---

Recurring events are the calendar's infrastructure layer. Unlike one-off events that require a creation decision each time they appear, recurring events run automatically once configured. The design principle: decisions made once should not require re-making every week.

## The three categories of recurring events worth investing in

**Work infrastructure:**
- Daily deep work block (8:30–10:00 or equivalent peak window, Busy, task-specific name updated weekly)
- Shallow work batches (two windows daily, 30–45 min each)
- Weekly planning review (Friday or Sunday, 20–25 min)
- End-of-day shutdown (5 min, serves as workday endpoint signal)

**Team coordination:**
- Standups, syncs, 1-on-1s — these already exist as recurring events for most teams
- Team planning sessions, retrospectives

**Personal maintenance:**
- Exercise, lunch, health appointments
- Whatever needs to be protected from work encroachment

## The configuration details that matter

**Busy vs. Free status:** Work blocks should be Busy. Meetings should be Busy. Personal holds that shouldn't be displaced by work: Busy. Only truly flexible holds should be Free.

**Event naming:** Recurring blocks need specific task names updated weekly. A recurring "Deep work" block with no task name is a recurring reminder that you have time set aside, not a commitment to use it for anything specific. Update the event title as part of the weekly planning review.

**End conditions:** Recurring events created "forever" accumulate. For project-specific recurring events, set an end date. For infrastructure events (morning deep work, shutdown routine), indefinite is fine.

## The quarterly audit

The risk of recurring events is that they outlive their purpose. A quarterly pass — "does this still serve its function?" — prevents calendar debt accumulation. Remove or reduce anything whose removal wouldn't produce a specific, named problem.

---

[Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — free Chrome extension. Happy to discuss recurring event design.
