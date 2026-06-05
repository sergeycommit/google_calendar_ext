# Combining Pomodoro and Calendar Blocking: Complementary Mechanisms

*Hacker News post · December 26, 2027*

---

Pomodoro and time blocking are often presented as alternatives. They're actually orthogonal: they operate at different levels of the scheduling hierarchy and solve different problems. Using both together produces effects that neither achieves alone.

## The level analysis

**Time blocking operates at the scheduling level:** When will I work on this? It claims calendar time, protects it from meetings, makes work visible alongside commitments.

**Pomodoro operates at the execution level:** How will I stay focused during the time I've scheduled? It structures the work session itself — 25-minute sprints, 5-minute breaks, recurring cycles.

Neither answers the other's question. A calendar block doesn't help you stay focused during the block. Pomodoro doesn't help you protect time for the block to exist.

## The combination

**Calendar block** → claims and protects a 90-120 minute window.

**Pomodoro within the block** → structures how that window is used: 25-min sprint → 5-min break → 25-min sprint → 5-min break → 25-min sprint → 5-min break.

Three full Pomodoros fit in a 90-minute block with ~5 minutes of buffer.

The break timing matters. Pomodoro breaks are not optional recovery padding — they're the mechanism that enables the next sprint to start at equivalent cognitive capacity. Skipping breaks produces diminishing returns in later sprints.

## Implementation notes

**Don't block individual Pomodoros on the calendar.** The block is the unit of calendar planning; Pomodoros are the unit of execution within it. Attempting to schedule 25-minute increments on the calendar adds overhead without value.

**Update the block description at the end.** "Stopped at: [where you left off]." This is the inverse of context ramp-up: a 2-minute note at the end of each session amortizes the ramp-up cost of the next session.

**Track which Pomodoros completed.** Not for performance management — for data on how long specific task types actually take. Most people systematically under-estimate. The data corrects this.

## When Pomodoro doesn't fit

Tasks with natural longer rhythms (deep design sessions, extended debugging) sometimes resist the 25-minute interrupt. In these cases, extend the sprint to 45-50 minutes and the break to 10. The principle (sprint + break + sprint) matters more than the specific durations.

---

[Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — free Chrome extension. Happy to discuss the Pomodoro/blocking combination.
