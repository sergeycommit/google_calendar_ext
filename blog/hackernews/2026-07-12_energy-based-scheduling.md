# Energy-Based Scheduling: Matching Task Demands to Cognitive State

*Hacker News post · July 12, 2026*

---

Standard scheduling optimization treats available time slots as interchangeable. "I have 2 hours on Tuesday — I'll put the difficult work there." But 2 hours at 9am Tuesday is not the same resource as 2 hours at 3pm Tuesday. Cognitive performance varies significantly across the day, and scheduling as if it doesn't leaves performance on the table.

## The cognitive performance pattern

The research on this is fairly consistent (Breus, Pink, and others): most people have a performance pattern with a morning peak, a post-lunch trough, and a smaller secondary peak in the late afternoon. The exact timing varies by chronotype, but the pattern is consistent across chronotypes — just shifted in time.

Performance differences across this cycle are not trivial. Studies measuring attention, working memory, and decision quality show 20-40% performance differences between peak and trough periods for tasks that require these capacities.

## Task-energy matching

**High-demand tasks** (complex problem solving, architectural decisions, writing, analysis) → peak period only.

**Medium-demand tasks** (meetings, code reviews, collaborative work, editing) → shoulder periods (early morning before peak or late morning after, early afternoon).

**Low-demand tasks** (email, Slack, admin, data entry, repetitive coding tasks) → trough period. These don't require peak capacity, so there's no performance cost to placing them in the lowest-energy window.

## Implementation in Google Calendar

The calendar cannot enforce this automatically. It requires:
1. Knowing your own peak period (1 week of self-observation is enough)
2. Blocking peak periods for high-demand work before meetings claim them
3. Deliberately placing shallow work batches in trough windows

## The performance ROI

The math is simple: if your peak produces 40% more output per hour than your trough, and you currently put low-demand tasks in your peak and high-demand tasks in your trough, you're significantly under-leveraging your own cognitive capacity.

---

[Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — free Chrome extension. Happy to discuss the scheduling model.
