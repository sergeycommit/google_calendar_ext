# Show HN: One-Click Meeting Join from the Browser Toolbar

*Hacker News post · August 8, 2027*

---

We added a feature to [Schedule Calendar](https://chromewebstore.google.com/detail/google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe) specifically for the "find and join meeting" workflow, and it's become the most-used feature by volume.

## The problem it solves

The standard pre-meeting workflow:
1. Notification fires
2. Open Google Calendar (switch tabs or find tab)
3. Find the event (scroll or click)
4. Expand event details
5. Find the video conferencing link (buried in description)
6. Click the link
7. Browser prompts "open in Zoom/Meet app?"
8. Click confirm

On average: 45-90 seconds, 6-8 clicks. Every meeting, every day.

The extension workflow:
1. Click toolbar icon
2. Upcoming events appear with "Join" buttons for calls that have video links
3. Click "Join"

Total: 2 clicks, 3-5 seconds.

## The technical implementation

The challenge is detecting and extracting video conferencing links from event descriptions. Event descriptions in Google Calendar are stored as HTML. Video conferencing links appear in several formats:
- Zoom: `zoom.us/j/[meeting-id]` or `zoom.us/wc/join/[id]`
- Google Meet: `meet.google.com/[code]`
- Teams: `teams.microsoft.com/l/meetup-join/...`
- Webex, Whereby, Around: their respective URL patterns

We maintain a list of known video conferencing URL patterns and scan event descriptions for them. When found, we surface a "Join" button in the popup adjacent to the event.

Edge cases: events with multiple video links (conference ID + browser join), events using Google Calendar's native Meet integration (these have a separate `conferenceData` field in the API response, which is cleaner to parse), links in the location field vs. description field.

## Usage patterns

In our telemetry: Join button is clicked on average 4.2x/day per active user. Users with more meetings use it more. The distribution suggests the time savings scale linearly with meeting frequency — which is the expected result.

Happy to answer questions about the link detection implementation or usage data.
