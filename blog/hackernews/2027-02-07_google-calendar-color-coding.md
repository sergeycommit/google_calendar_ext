# Google Calendar Color Coding: Building a Visual System That Scales

*Hacker News post · February 7, 2027*

---

Color coding in Google Calendar is one of those features that's trivially easy to set up and disproportionately valuable in daily use. The cognitive difference between "read each event title to understand what it is" and "parse the color to understand what it is" is larger than it sounds.

## The design constraint

Human short-term memory can reliably distinguish 4-6 distinct categories. Beyond 7, colors become hard to differentiate and the system creates cognitive load rather than reducing it.

A 6-category maximum:
- Deep work / focus blocks
- Meetings / calls
- Shallow work / admin batches
- Deadlines / deliverables
- Personal / health / life
- Tentative / low-priority holds

That covers ~95% of what knowledge workers do. More categories are self-defeating.

## Applying colors in Google Calendar

**Existing events:** Click the event → click the colored dot next to the event title in the details panel → choose a new color. This applies to the specific occurrence; you can choose to apply to all events in a recurring series.

**New events:** During event creation, there's a colored circle next to the event title field. Click it to choose the category.

**Calendar-level colors:** Under the Calendars sidebar, you can assign a color to an entire calendar (e.g., "Personal" is green, "Work" is blue). Individual events inherit the calendar color unless overridden.

## The consistency requirement

The system only delivers its value if colors are applied consistently. The decision about which color to apply should be automatic, not deliberate. 3-4 days of deliberate application typically builds the habit.

## What consistent color coding enables

**Visual parsing:** You can read the shape of a week — meeting-heavy, focus-heavy, balanced — in 2-3 seconds without reading any event titles.

**Diagnostic utility:** A week with no green (focus) and all blue (meetings) is visually alarming in a way that's useful. You see the imbalance before the week feels bad.

**Shared calendar legibility:** When a colleague looks at your calendar, color provides structural context without requiring them to read every event title.

---

[Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) — free Chrome extension. Happy to discuss color system design.
