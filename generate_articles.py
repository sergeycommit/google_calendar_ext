#!/usr/bin/env python3
"""
Blog article generator for calendar-extension.site.

Reads the ARTICLES content plan (100 topics in 9 semantic clusters),
calls Claude API to generate each article, and writes:
  - blog/<slug>.html   — full HTML article with FAQ + internal links
  - blog/medium/<slug>.md — abbreviated Medium version (~500 words)
  - blog/devto/<slug>.md  — dev.to version with YAML frontmatter (~400 words)

Also rewrites blog/index.html to list all published articles.

Usage:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...

  python generate_articles.py               # all 100 articles
  python generate_articles.py --id 1        # single article by plan ID
  python generate_articles.py --cluster 1   # one cluster
  python generate_articles.py --dry-run     # print plan, write nothing
"""

import anthropic
import argparse
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

SITE_URL       = "https://calendar-extension.site"
STORE_URL      = ("https://chromewebstore.google.com/detail/"
                  "google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe")
AUTHOR         = "Schedule Calendar Team"
BLOG_DIR       = Path(__file__).parent / "blog"
MEDIUM_DIR     = BLOG_DIR / "medium"
DEVTO_DIR      = BLOG_DIR / "devto"
START_DATE     = date(2026, 4, 1)   # first new article date
DAYS_GAP       = 3                  # days between articles (≈100 articles over ~10 months)

# ─── Competitor content fetcher ──────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Minimal HTML→text: keeps headings and paragraph text, strips tags."""
    def __init__(self):
        super().__init__()
        self._capture = False
        self._tag = ""
        self.chunks: list[str] = []
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("h1","h2","h3","h4","p","li"):
            self._capture = True
            self._tag = tag
            self._buf = ""

    def handle_endtag(self, tag):
        if tag in ("h1","h2","h3","h4","p","li") and self._capture:
            text = self._buf.strip()
            if text and len(text) > 15:
                prefix = "## " if tag in ("h2","h3") else "### " if tag == "h4" else ""
                self.chunks.append(prefix + text)
            self._capture = False
            self._buf = ""

    def handle_data(self, data):
        if self._capture:
            self._buf += data


def fetch_competitor_content(url: str, max_chars: int = 6000) -> str:
    """Fetch a competitor URL and return extracted headings + body text (plain)."""
    if not url:
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SEO-research-bot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, Exception) as e:
        print(f"\n    [fetch warn] {url}: {e}", end="")
        return ""

    parser = _TextExtractor()
    parser.feed(raw)
    text = "\n".join(parser.chunks)
    # Truncate so it fits in the prompt without blowing token budget
    return text[:max_chars]


# ─── Content plan ────────────────────────────────────────────────────────────
# 100 articles across 9 semantic clusters.
# competitor_ref is an optional URL used as editorial reference only (never copied).

ARTICLES = [
    # ── Cluster 1: Time Blocking (11) ───────────────────────────────────────
    {"id": 1,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-guide-google-calendar",
     "title": "How to Set Up Time Blocking in Google Calendar",
     "seo_title": "Time Blocking in Google Calendar: A Practical Setup Guide",
     "category": "Time blocking",
     "primary_keyword": "time blocking Google Calendar",
     "secondary_keywords": ["calendar time blocks", "focus scheduling", "time block template"],
     "competitor_ref": "https://reclaim.ai/blog/time-blocking-guide"},

    {"id": 2,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "deep-work-time-blocks",
     "title": "How to Schedule Deep Work Blocks That Actually Stick",
     "seo_title": "Deep Work Scheduling: Protecting Your Best Hours on the Calendar",
     "category": "Time blocking",
     "primary_keyword": "deep work time blocks",
     "secondary_keywords": ["schedule deep work", "focus blocks calendar", "uninterrupted work time"],
     "competitor_ref": "https://fellow.ai/blog/calendar-organization-ideas-for-better-time-management/"},

    {"id": 3,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-vs-todo-list",
     "title": "Time Blocking vs. To-Do Lists: Which Works Better?",
     "seo_title": "Time Blocking vs. To-Do Lists: What the Difference Means for Your Day",
     "category": "Time blocking",
     "primary_keyword": "time blocking vs to-do list",
     "secondary_keywords": ["calendar vs task list", "time blocking productivity", "daily planning method"],
     "competitor_ref": "https://pumble.com/blog/google-calendar-extensions/"},

    {"id": 4,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-for-meetings",
     "title": "Time Blocking When Your Day Is Full of Meetings",
     "seo_title": "How to Time Block Around a Meeting-Heavy Schedule",
     "category": "Time blocking",
     "primary_keyword": "time blocking meetings",
     "secondary_keywords": ["meeting schedule planning", "block time between meetings", "busy calendar management"],
     "competitor_ref": "https://reclaim.ai/blog/smart-meetings-report"},

    {"id": 5,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "morning-focus-blocks",
     "title": "How to Protect Morning Focus Time With Calendar Blocks",
     "seo_title": "Morning Focus Blocks: Protecting Peak Hours Before Meetings Start",
     "category": "Time blocking",
     "primary_keyword": "morning focus blocks calendar",
     "secondary_keywords": ["protect morning hours", "focus time morning", "calendar morning routine"],
     "competitor_ref": "https://reclaim.ai/blog/what-is-focus-time"},

    {"id": 6,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-mistakes",
     "title": "5 Time Blocking Mistakes That Kill Productivity",
     "seo_title": "Common Time Blocking Mistakes (and How to Fix Them)",
     "category": "Time blocking",
     "primary_keyword": "time blocking mistakes",
     "secondary_keywords": ["time blocking problems", "why time blocking fails", "better time blocking"],
     "competitor_ref": "https://reclaim.ai/blog/time-blocking-guide"},

    {"id": 7,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-templates",
     "title": "Time Blocking Templates for Different Work Styles",
     "seo_title": "Free Time Blocking Templates for Google Calendar",
     "category": "Time blocking",
     "primary_keyword": "time blocking templates",
     "secondary_keywords": ["calendar template time blocking", "daily schedule template", "weekly time block template"],
     "competitor_ref": "https://savvycal.com/articles/time-blocking-templates/"},

    {"id": 8,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "energy-based-scheduling",
     "title": "Energy-Based Scheduling: Align Your Calendar to Peak Hours",
     "seo_title": "Energy-Based Scheduling: Match Your Calendar to How You Actually Work",
     "category": "Time blocking",
     "primary_keyword": "energy-based scheduling",
     "secondary_keywords": ["peak hours productivity", "chronotype scheduling", "ultradian rhythm calendar"],
     "competitor_ref": "https://savvycal.com/articles/context-switching/"},

    {"id": 9,  "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-boxing-vs-time-blocking",
     "title": "Time Boxing vs. Time Blocking: Key Differences Explained",
     "seo_title": "Time Boxing vs. Time Blocking: Which Method Fits Your Work?",
     "category": "Time blocking",
     "primary_keyword": "time boxing vs time blocking",
     "secondary_keywords": ["timeboxing method", "time blocking difference", "productivity scheduling methods"],
     "competitor_ref": "https://reclaim.ai/blog/time-blocking-guide"},

    {"id": 10, "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "shallow-work-batching",
     "title": "How to Batch Shallow Work on Your Calendar",
     "seo_title": "Batching Shallow Work: The Calendar Move That Frees Up Deep Focus",
     "category": "Time blocking",
     "primary_keyword": "batch shallow work calendar",
     "secondary_keywords": ["task batching", "admin batching", "shallow work scheduling"],
     "competitor_ref": "https://reclaim.ai/blog/deep-work-vs-shallow-work"},

    {"id": 11, "cluster": 1, "cluster_name": "Time Blocking",
     "slug": "time-blocking-remote-work",
     "title": "Time Blocking Strategies for Remote Workers",
     "seo_title": "Time Blocking for Remote Workers: Keeping Structure Without an Office",
     "category": "Time blocking",
     "primary_keyword": "time blocking remote work",
     "secondary_keywords": ["remote work scheduling", "work from home calendar structure", "remote focus time"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    # ── Cluster 2: Meeting Management (11) ──────────────────────────────────
    {"id": 12, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "meeting-hygiene-best-practices",
     "title": "Meeting Hygiene: 8 Habits That Make Meetings Worth Attending",
     "seo_title": "Meeting Hygiene Best Practices That Save Everyone's Time",
     "category": "Meeting management",
     "primary_keyword": "meeting hygiene",
     "secondary_keywords": ["better meetings", "meeting habits", "effective meeting practices"],
     "competitor_ref": "https://fellow.ai/blog/calendar-organization-ideas-for-better-time-management/"},

    {"id": 13, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "reduce-meeting-overload",
     "title": "How to Reduce Meeting Overload Without Saying No to Everything",
     "seo_title": "Reducing Meeting Overload: Practical Tactics That Don't Burn Bridges",
     "category": "Meeting management",
     "primary_keyword": "reduce meeting overload",
     "secondary_keywords": ["too many meetings", "meeting calendar", "fewer meetings productivity"],
     "competitor_ref": "https://reclaim.ai/blog/smart-meetings-report"},

    {"id": 14, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "back-to-back-meetings-recovery",
     "title": "How to Recover From Back-to-Back Meeting Days",
     "seo_title": "Back-to-Back Meetings: How to Recover and Protect Future Days",
     "category": "Meeting management",
     "primary_keyword": "back-to-back meetings",
     "secondary_keywords": ["consecutive meetings recovery", "meeting fatigue", "calendar buffer time"],
     "competitor_ref": "https://fellow.ai/blog/calendar-organization-ideas-for-better-time-management/"},

    {"id": 15, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "meeting-free-day-setup",
     "title": "How to Set Up a Meeting-Free Day (and Keep It)",
     "seo_title": "Meeting-Free Day: How to Set One Up and Actually Protect It",
     "category": "Meeting management",
     "primary_keyword": "meeting-free day",
     "secondary_keywords": ["no meeting day", "focus day calendar", "deep work day"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    {"id": 16, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "async-vs-sync-meetings",
     "title": "Async vs. Sync: Which Meetings Should Stay on the Calendar?",
     "seo_title": "Async vs. Sync Meetings: How to Decide Which Meetings Are Worth Scheduling",
     "category": "Meeting management",
     "primary_keyword": "async vs sync meetings",
     "secondary_keywords": ["asynchronous meetings", "when to have meetings", "synchronous communication"],
     "competitor_ref": "https://savvycal.com/articles/asynchronous-communication/"},

    {"id": 17, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "meeting-preparation-checklist",
     "title": "A Simple Meeting Preparation Checklist for Recurring Calls",
     "seo_title": "Meeting Preparation Checklist: What to Do Before Every Recurring Call",
     "category": "Meeting management",
     "primary_keyword": "meeting preparation checklist",
     "secondary_keywords": ["prepare for meetings", "meeting agenda checklist", "pre-meeting routine"],
     "competitor_ref": "https://savvycal.com/articles/team-meeting-agenda/"},

    {"id": 18, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "decline-meetings-politely",
     "title": "How to Decline Calendar Invites Without Damaging Relationships",
     "seo_title": "Declining Meeting Invites Gracefully: Scripts and Strategies",
     "category": "Meeting management",
     "primary_keyword": "decline meeting invites",
     "secondary_keywords": ["how to say no to meetings", "meeting decline message", "calendar boundaries"],
     "competitor_ref": "https://savvycal.com/articles/scheduling-conflicts/"},

    {"id": 19, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "15-minute-meeting-format",
     "title": "Why 15-Minute Meetings Work Better Than 30",
     "seo_title": "15-Minute Meetings: Why Shorter Beats Longer (and How to Make Them Work)",
     "category": "Meeting management",
     "primary_keyword": "15-minute meeting",
     "secondary_keywords": ["shorter meetings", "meeting length", "efficient meetings"],
     "competitor_ref": "https://reclaim.ai/blog/smart-meetings-report"},

    {"id": 20, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "meeting-scheduling-best-practices",
     "title": "6 Rules for Smarter Meeting Scheduling",
     "seo_title": "Smarter Meeting Scheduling: 6 Rules That Reduce Calendar Chaos",
     "category": "Meeting management",
     "primary_keyword": "meeting scheduling best practices",
     "secondary_keywords": ["how to schedule meetings", "better meeting scheduling", "calendar scheduling rules"],
     "competitor_ref": "https://savvycal.com/articles/scheduling-conflicts/"},

    {"id": 21, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "recurring-meeting-audit",
     "title": "When to Kill a Recurring Meeting (and How)",
     "seo_title": "Recurring Meeting Audit: How to Identify and Kill the Ones That Don't Pay Off",
     "category": "Meeting management",
     "primary_keyword": "recurring meeting audit",
     "secondary_keywords": ["cancel recurring meetings", "meeting audit", "standing meetings review"],
     "competitor_ref": "https://reclaim.ai/blog/productivity-report-one-on-one-meetings"},

    {"id": 22, "cluster": 2, "cluster_name": "Meeting Management",
     "slug": "buffer-time-between-meetings",
     "title": "Why Buffer Time Between Meetings Is Not Optional",
     "seo_title": "Meeting Buffer Time: Why Every Calendar Needs It and How to Add It",
     "category": "Meeting management",
     "primary_keyword": "buffer time between meetings",
     "secondary_keywords": ["meeting buffer", "transition time meetings", "calendar breaks"],
     "competitor_ref": "https://fellow.ai/blog/calendar-organization-ideas-for-better-time-management/"},

    # ── Cluster 3: Google Calendar Features (12) ────────────────────────────
    {"id": 23, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-color-coding",
     "title": "How to Build a Color-Coding System in Google Calendar",
     "seo_title": "Google Calendar Color Coding: A System That Actually Makes Sense",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar color coding",
     "secondary_keywords": ["calendar color system", "color code events", "calendar visual organization"],
     "competitor_ref": "https://fellow.ai/blog/calendar-categories-ideas/"},

    {"id": 24, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-keyboard-shortcuts",
     "title": "Google Calendar Keyboard Shortcuts That Save Real Time",
     "seo_title": "Google Calendar Keyboard Shortcuts: The Complete List Worth Learning",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar keyboard shortcuts",
     "secondary_keywords": ["calendar shortcuts", "Google Calendar hotkeys", "navigate calendar keyboard"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-hacks/"},

    {"id": 25, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-recurring-events",
     "title": "Recurring Events in Google Calendar: Tips Most Users Miss",
     "seo_title": "Google Calendar Recurring Events: Advanced Tips and Settings",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar recurring events",
     "secondary_keywords": ["repeating events calendar", "recurring meeting setup", "calendar repeat options"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 26, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-notifications",
     "title": "How to Set Smarter Notifications in Google Calendar",
     "seo_title": "Google Calendar Notifications: How to Stop Getting the Wrong Alerts",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar notifications",
     "secondary_keywords": ["calendar alerts", "event reminders Google Calendar", "notification settings"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 27, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-sharing",
     "title": "Google Calendar Sharing and Permissions Explained",
     "seo_title": "Google Calendar Sharing: How Permissions Work and What to Share",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar sharing",
     "secondary_keywords": ["share Google Calendar", "calendar permissions", "Google Calendar access levels"],
     "competitor_ref": "https://savvycal.com/articles/how-to-share-google-calendar/"},

    {"id": 28, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-goals",
     "title": "Using Google Calendar Goals Without Them Taking Over",
     "seo_title": "Google Calendar Goals: How to Use Them Without Overcrowding Your Week",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar goals",
     "secondary_keywords": ["goals in calendar", "calendar goal setting", "Google Calendar habit tracking"],
     "competitor_ref": "https://reclaim.ai/blog/setting-work-priorities-report"},

    {"id": 29, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-search-tips",
     "title": "How to Find Anything in Google Calendar Quickly",
     "seo_title": "Google Calendar Search: How to Find Past Events and People Fast",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar search",
     "secondary_keywords": ["search events Google Calendar", "find calendar events", "calendar search filters"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-hacks/"},

    {"id": 30, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-workspace-settings",
     "title": "Google Calendar for Google Workspace Teams: Key Settings",
     "seo_title": "Google Calendar Workspace Settings Your Team Should Configure",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar Workspace settings",
     "secondary_keywords": ["Google Workspace calendar", "team calendar settings", "calendar admin settings"],
     "competitor_ref": "https://reclaim.ai/blog/google-calendar-add-ons"},

    {"id": 31, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-integrations",
     "title": "Best Google Calendar Integrations for Focused Work",
     "seo_title": "Google Calendar Integrations That Actually Help You Focus",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar integrations",
     "secondary_keywords": ["calendar app integrations", "Google Calendar connect", "best calendar add-ons"],
     "competitor_ref": "https://reclaim.ai/blog/google-calendar-add-ons"},

    {"id": 32, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-view-modes",
     "title": "Google Calendar Day vs. Week vs. Month View: When to Use Each",
     "seo_title": "Google Calendar Views Explained: Day, Week, Month, and Agenda",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar views",
     "secondary_keywords": ["calendar day view", "Google Calendar month view", "best calendar view"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 33, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-out-of-office",
     "title": "Setting Up Out-of-Office and Focus Time in Google Calendar",
     "seo_title": "Google Calendar Out of Office and Focus Time: Setup Guide",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar out of office",
     "secondary_keywords": ["focus time Google Calendar", "out of office calendar", "calendar focus mode"],
     "competitor_ref": "https://reclaim.ai/blog/what-is-focus-time"},

    {"id": 34, "cluster": 3, "cluster_name": "Google Calendar Features",
     "slug": "google-calendar-mobile-tips",
     "title": "Google Calendar Mobile Tips for Checking Without Getting Stuck",
     "seo_title": "Google Calendar on Mobile: Tips for Quick Checks That Don't Derail You",
     "category": "Google Calendar features",
     "primary_keyword": "Google Calendar mobile tips",
     "secondary_keywords": ["Google Calendar phone", "mobile calendar tips", "calendar app mobile"],
     "competitor_ref": "https://savvycal.com/articles/how-to-plan-your-day/"},

    # ── Cluster 4: Calendar Productivity System (11) ─────────────────────────
    {"id": 35, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "weekly-planning-ritual",
     "title": "Building a Weekly Planning Ritual That Takes Under 20 Minutes",
     "seo_title": "Weekly Planning Ritual: A 20-Minute System for a Calmer Week",
     "category": "Planning system",
     "primary_keyword": "weekly planning ritual",
     "secondary_keywords": ["weekly review calendar", "weekly planning routine", "calendar weekly reset"],
     "competitor_ref": "https://savvycal.com/articles/how-to-plan-your-day/"},

    {"id": 36, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "daily-calendar-check-habits",
     "title": "3 Daily Calendar Check Habits That Keep the Day on Track",
     "seo_title": "Daily Calendar Check Habits: Three Moments That Keep the Day Readable",
     "category": "Planning system",
     "primary_keyword": "daily calendar check",
     "secondary_keywords": ["calendar daily habits", "checking calendar routine", "morning calendar review"],
     "competitor_ref": "https://savvycal.com/articles/best-daily-plan/"},

    {"id": 37, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "calendar-audit-guide",
     "title": "How to Run a Calendar Audit and Reclaim Your Week",
     "seo_title": "Calendar Audit: How to Find and Fix What's Stealing Your Time",
     "category": "Planning system",
     "primary_keyword": "calendar audit",
     "secondary_keywords": ["review calendar schedule", "calendar cleanup", "time audit calendar"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 38, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "pomodoro-google-calendar",
     "title": "How to Use the Pomodoro Technique With Google Calendar",
     "seo_title": "Pomodoro and Google Calendar: Making Focus Sessions Visible",
     "category": "Planning system",
     "primary_keyword": "Pomodoro Google Calendar",
     "secondary_keywords": ["pomodoro technique calendar", "pomodoro blocks", "25 minute work blocks"],
     "competitor_ref": "https://savvycal.com/articles/context-switching/"},

    {"id": 39, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "calendar-for-project-management",
     "title": "Using Your Calendar as a Light Project Management Tool",
     "seo_title": "Calendar as Project Management: When Your Schedule Replaces a Task App",
     "category": "Planning system",
     "primary_keyword": "calendar project management",
     "secondary_keywords": ["project planning calendar", "calendar tasks projects", "schedule project management"],
     "competitor_ref": "https://reclaim.ai/blog/task-management-trends-report"},

    {"id": 40, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "personal-vs-work-calendar",
     "title": "How to Manage Personal and Work Calendars Without Overlap",
     "seo_title": "Personal vs. Work Calendar: Keeping Boundaries Without the Chaos",
     "category": "Planning system",
     "primary_keyword": "personal vs work calendar",
     "secondary_keywords": ["separate work personal calendar", "multiple calendar management", "calendar boundaries"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 41, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "calendar-goal-setting",
     "title": "Setting Weekly Goals That Show Up on Your Calendar",
     "seo_title": "Calendar Goal Setting: Making Your Weekly Priorities Visible",
     "category": "Planning system",
     "primary_keyword": "calendar goal setting",
     "secondary_keywords": ["weekly goals calendar", "set goals calendar", "priority planning calendar"],
     "competitor_ref": "https://reclaim.ai/blog/setting-work-priorities-report"},

    {"id": 42, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "focus-time-protection",
     "title": "How to Protect Focus Time Before Meetings Claim It",
     "seo_title": "Protecting Focus Time on Your Calendar: Tactics That Actually Work",
     "category": "Planning system",
     "primary_keyword": "protect focus time calendar",
     "secondary_keywords": ["focus block protection", "calendar focus time", "defend deep work"],
     "competitor_ref": "https://reclaim.ai/blog/what-is-focus-time"},

    {"id": 43, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "end-of-day-calendar-review",
     "title": "The 5-Minute End-of-Day Calendar Review",
     "seo_title": "End-of-Day Calendar Review: A 5-Minute Routine Worth Keeping",
     "category": "Planning system",
     "primary_keyword": "end of day calendar review",
     "secondary_keywords": ["daily calendar review", "EOD planning routine", "evening calendar check"],
     "competitor_ref": "https://savvycal.com/articles/best-daily-plan/"},

    {"id": 44, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "calendar-system-simplification",
     "title": "Signs Your Calendar System Is Too Complicated",
     "seo_title": "Is Your Calendar System Too Complex? Signs and How to Simplify",
     "category": "Planning system",
     "primary_keyword": "simplify calendar system",
     "secondary_keywords": ["calendar overcomplicated", "simpler schedule", "minimal calendar setup"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 45, "cluster": 4, "cluster_name": "Calendar Productivity System",
     "slug": "sunday-planning-routine",
     "title": "A Sunday Calendar Planning Routine for a Calmer Monday",
     "seo_title": "Sunday Planning Routine: Prepare Your Calendar for a Calmer Week",
     "category": "Planning system",
     "primary_keyword": "Sunday planning routine calendar",
     "secondary_keywords": ["weekend planning calendar", "Sunday review", "Monday prep calendar"],
     "competitor_ref": "https://savvycal.com/articles/how-to-plan-your-day/"},

    # ── Cluster 5: Chrome Extension & Browser Workflow (10) ──────────────────
    {"id": 46, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "why-chrome-extension-for-calendar",
     "title": "Why a Chrome Extension Beats Switching to a Full Calendar Tab",
     "seo_title": "Chrome Calendar Extension vs. Full Tab: Why Lightweight Wins",
     "category": "Chrome extension",
     "primary_keyword": "Chrome extension Google Calendar",
     "secondary_keywords": ["calendar browser extension", "calendar popup chrome", "google calendar extension"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-extension/"},

    {"id": 47, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "popup-calendar-workflow",
     "title": "How a Popup Calendar Changes Your Daily Workflow",
     "seo_title": "Popup Calendar Workflow: How Inline Access Changes How You Plan",
     "category": "Chrome extension",
     "primary_keyword": "popup calendar workflow",
     "secondary_keywords": ["calendar popup browser", "inline calendar workflow", "quick calendar access"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-extension/"},

    {"id": 48, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "browser-calendar-tools-2026",
     "title": "Browser-First Calendar Tools: What to Look for in 2026",
     "seo_title": "Best Browser-First Calendar Tools in 2026: What to Evaluate",
     "category": "Chrome extension",
     "primary_keyword": "browser calendar tools 2026",
     "secondary_keywords": ["calendar browser extension 2026", "best calendar chrome tools", "browser productivity calendar"],
     "competitor_ref": "https://timehopperapp.com/blog/best-google-calendar-extensions-2026.html"},

    {"id": 49, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "calendar-extension-features-to-look-for",
     "title": "The Features That Make a Google Calendar Extension Worth Installing",
     "seo_title": "Google Calendar Extension Features: What Separates Good from Great",
     "category": "Chrome extension",
     "primary_keyword": "Google Calendar extension features",
     "secondary_keywords": ["best calendar extension features", "what to look for calendar extension", "calendar extension review"],
     "competitor_ref": "https://fellow.ai/blog/google-calendar-extensions-to-boost-productivity/"},

    {"id": 50, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "time-to-next-event-visibility",
     "title": "Why Knowing Time-to-Next-Event Changes How You Work",
     "seo_title": "Time to Next Event: The One Number That Changes Your Workday",
     "category": "Chrome extension",
     "primary_keyword": "time to next event",
     "secondary_keywords": ["next event countdown", "meeting timer extension", "time until meeting"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 51, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "reducing-tab-switching-calendar",
     "title": "How to Stop Switching Tabs to Check Your Calendar",
     "seo_title": "Stop Tab Switching for Calendar: How to Keep Context Without Leaving Your Work",
     "category": "Chrome extension",
     "primary_keyword": "stop switching tabs calendar",
     "secondary_keywords": ["reduce tab switching", "calendar tab distraction", "browser calendar access"],
     "competitor_ref": "https://savvycal.com/articles/defensive-calendaring/"},

    {"id": 52, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "quick-calendar-check-workflow",
     "title": "The Quick Calendar Check: A Workflow for Staying on Track",
     "seo_title": "Quick Calendar Check Workflow: How to Orient Without Losing Focus",
     "category": "Chrome extension",
     "primary_keyword": "quick calendar check",
     "secondary_keywords": ["fast calendar review", "calendar check habit", "glance at calendar"],
     "competitor_ref": "https://savvycal.com/articles/best-daily-plan/"},

    {"id": 53, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "calendar-extension-vs-full-app",
     "title": "Chrome Extension vs. Standalone Calendar App: What Works for Most People",
     "seo_title": "Calendar Extension vs. App: Which One You Actually Need",
     "category": "Chrome extension",
     "primary_keyword": "calendar extension vs app",
     "secondary_keywords": ["chrome extension vs standalone app", "calendar app comparison", "lightweight calendar tool"],
     "competitor_ref": "https://clickup.com/blog/google-calendar-extensions/"},

    {"id": 54, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "join-meetings-faster-toolbar",
     "title": "How to Join Meetings Faster With a Toolbar Calendar",
     "seo_title": "Joining Meetings Faster: How Toolbar Calendar Access Reduces Friction",
     "category": "Chrome extension",
     "primary_keyword": "join meetings faster toolbar",
     "secondary_keywords": ["one-click meeting join", "meeting link toolbar", "quick join calendar"],
     "competitor_ref": "https://meetingnotes.com/blog/google-calendar-extensions"},

    {"id": 55, "cluster": 5, "cluster_name": "Chrome Extension Workflow",
     "slug": "lightweight-calendar-tools",
     "title": "Why Lighter Calendar Tools Work Better for Most People",
     "seo_title": "Lightweight Calendar Tools: Why Less Is More for Most Workflows",
     "category": "Chrome extension",
     "primary_keyword": "lightweight calendar tools",
     "secondary_keywords": ["simple calendar extension", "minimal calendar app", "light calendar workflow"],
     "competitor_ref": "https://www.attendancebot.com/blog/google-calendar-extensions/"},

    # ── Cluster 6: Remote & Hybrid Work (10) ─────────────────────────────────
    {"id": 56, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "remote-team-calendar-etiquette",
     "title": "Calendar Etiquette for Remote Teams",
     "seo_title": "Remote Team Calendar Etiquette: Norms That Keep Everyone Sane",
     "category": "Remote work",
     "primary_keyword": "remote team calendar etiquette",
     "secondary_keywords": ["distributed team calendar", "remote calendar norms", "team scheduling etiquette"],
     "competitor_ref": "https://savvycal.com/articles/virtual-meeting-etiquette/"},

    {"id": 57, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "timezone-management-google-calendar",
     "title": "Managing Time Zones in Google Calendar for Distributed Teams",
     "seo_title": "Time Zone Management in Google Calendar: A Guide for Distributed Teams",
     "category": "Remote work",
     "primary_keyword": "time zones Google Calendar",
     "secondary_keywords": ["Google Calendar time zones", "multiple time zones calendar", "distributed team scheduling"],
     "competitor_ref": "https://savvycal.com/articles/remote-board-meetings/"},

    {"id": 58, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "async-team-scheduling",
     "title": "Scheduling for Async Teams: Less Calendar, Better Output",
     "seo_title": "Async Team Scheduling: How to Reduce Meetings Without Losing Coordination",
     "category": "Remote work",
     "primary_keyword": "async team scheduling",
     "secondary_keywords": ["asynchronous team calendar", "async scheduling", "fewer meetings remote team"],
     "competitor_ref": "https://savvycal.com/articles/asynchronous-communication/"},

    {"id": 59, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "hybrid-work-calendar-setup",
     "title": "How to Set Up Your Calendar for a Hybrid Work Schedule",
     "seo_title": "Hybrid Work Calendar Setup: Balancing Office and Remote Days",
     "category": "Remote work",
     "primary_keyword": "hybrid work calendar",
     "secondary_keywords": ["hybrid schedule calendar", "office days calendar", "hybrid remote calendar setup"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    {"id": 60, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "work-from-home-calendar-boundaries",
     "title": "Using Your Calendar to Set Work-From-Home Boundaries",
     "seo_title": "Work-From-Home Calendar Boundaries: How to Signal When You're Off",
     "category": "Remote work",
     "primary_keyword": "work from home calendar boundaries",
     "secondary_keywords": ["WFH calendar setup", "remote work boundaries", "home office calendar"],
     "competitor_ref": "https://savvycal.com/articles/work-from-home-setup/"},

    {"id": 61, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "cross-timezone-meeting-scheduling",
     "title": "How to Schedule Across Time Zones Without the Chaos",
     "seo_title": "Cross-Timezone Meeting Scheduling: Finding Times That Work for Everyone",
     "category": "Remote work",
     "primary_keyword": "cross-timezone meeting scheduling",
     "secondary_keywords": ["schedule across timezones", "international meeting scheduling", "global team meetings"],
     "competitor_ref": "https://savvycal.com/articles/remote-board-meetings/"},

    {"id": 62, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "remote-standup-calendar-setup",
     "title": "Setting Up a Lightweight Remote Standup on the Calendar",
     "seo_title": "Remote Standup Setup: A Calendar-First Approach to Daily Syncs",
     "category": "Remote work",
     "primary_keyword": "remote standup calendar",
     "secondary_keywords": ["daily standup schedule", "remote standup meeting", "async standup calendar"],
     "competitor_ref": "https://savvycal.com/articles/virtual-meeting-etiquette/"},

    {"id": 63, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "calendar-transparency-remote-teams",
     "title": "When to Share Your Calendar With Remote Teammates (and When Not To)",
     "seo_title": "Calendar Transparency for Remote Teams: How Much to Share and With Whom",
     "category": "Remote work",
     "primary_keyword": "calendar transparency remote teams",
     "secondary_keywords": ["share calendar team", "calendar visibility remote", "team calendar access"],
     "competitor_ref": "https://savvycal.com/articles/remote-work-culture/"},

    {"id": 64, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "flexible-schedule-calendar",
     "title": "How to Structure a Flexible Work Schedule on Your Calendar",
     "seo_title": "Flexible Work Schedule on Calendar: Structuring Freedom Without Chaos",
     "category": "Remote work",
     "primary_keyword": "flexible work schedule calendar",
     "secondary_keywords": ["flexible schedule setup", "non-traditional work hours calendar", "flex time calendar"],
     "competitor_ref": "https://savvycal.com/articles/work-schedule-apps/"},

    {"id": 65, "cluster": 6, "cluster_name": "Remote & Hybrid Work",
     "slug": "distributed-team-focus-time",
     "title": "Protecting Focus Time on Distributed Teams",
     "seo_title": "Focus Time on Distributed Teams: How to Defend Deep Work Across Time Zones",
     "category": "Remote work",
     "primary_keyword": "distributed team focus time",
     "secondary_keywords": ["remote team deep work", "protect focus distributed", "global team focus hours"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    # ── Cluster 7: Role-Specific Tips (11) ───────────────────────────────────
    {"id": 66, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-managers",
     "title": "Google Calendar for Managers: Staying Available Without Losing Focus",
     "seo_title": "Google Calendar for Managers: Balancing Availability and Deep Work",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for managers",
     "secondary_keywords": ["manager calendar tips", "manager schedule", "leadership calendar management"],
     "competitor_ref": "https://reclaim.ai/blog/productivity-report-one-on-one-meetings"},

    {"id": 67, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-engineers",
     "title": "Calendar Habits for Engineers Who Need Long Focus Windows",
     "seo_title": "Google Calendar for Software Engineers: Protecting Flow State",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for engineers",
     "secondary_keywords": ["developer calendar habits", "software engineer schedule", "engineering focus time"],
     "competitor_ref": "https://reclaim.ai/blog/deep-work"},

    {"id": 68, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-freelancers",
     "title": "Google Calendar for Freelancers: Billing Time and Client Calls",
     "seo_title": "Google Calendar for Freelancers: Managing Clients, Billing, and Boundaries",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for freelancers",
     "secondary_keywords": ["freelance calendar setup", "client scheduling calendar", "freelancer time management"],
     "competitor_ref": "https://savvycal.com/articles/work-schedule-apps/"},

    {"id": 69, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-product-managers",
     "title": "Calendar System for Product Managers: Planning Without Overplanning",
     "seo_title": "Google Calendar for Product Managers: A Lightweight System That Works",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for product managers",
     "secondary_keywords": ["PM calendar tips", "product manager schedule", "product planning calendar"],
     "competitor_ref": "https://reclaim.ai/blog/task-management-trends-report"},

    {"id": 70, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-founders",
     "title": "Founder Calendar Management: Keeping Strategy Visible",
     "seo_title": "Google Calendar for Founders: How to Keep Strategic Work From Disappearing",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for founders",
     "secondary_keywords": ["startup founder calendar", "CEO calendar management", "founder time management"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 71, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-sales",
     "title": "Google Calendar for Sales: Managing Pipelines and Calls",
     "seo_title": "Google Calendar for Sales Teams: Scheduling Outreach and Follow-Ups",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for sales",
     "secondary_keywords": ["sales calendar tips", "CRM and calendar", "sales call scheduling"],
     "competitor_ref": "https://savvycal.com/articles/one-on-one-meetings/"},

    {"id": 72, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-designers",
     "title": "Calendar Setup for Designers Who Need Creative Flow",
     "seo_title": "Google Calendar for Designers: Building Space for Creative Work",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for designers",
     "secondary_keywords": ["designer calendar habits", "creative work scheduling", "design flow time blocking"],
     "competitor_ref": "https://reclaim.ai/blog/deep-work"},

    {"id": 73, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-customer-success",
     "title": "Calendar Management for Customer Success Teams",
     "seo_title": "Google Calendar for Customer Success: Managing Check-ins and Renewals",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar customer success",
     "secondary_keywords": ["CS team calendar", "customer success scheduling", "client success calendar"],
     "competitor_ref": "https://savvycal.com/articles/one-on-one-meetings/"},

    {"id": 74, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-students",
     "title": "Google Calendar for Students: Semester Planning in a Browser",
     "seo_title": "Google Calendar for Students: How to Manage Classes, Deadlines, and Study Time",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for students",
     "secondary_keywords": ["student calendar tips", "college schedule calendar", "study time blocking"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 75, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "google-calendar-for-hr",
     "title": "HR Calendar Management: Onboarding, Reviews, and Recruiting",
     "seo_title": "Google Calendar for HR Teams: Managing Recruiting and Reviews",
     "category": "Role-specific",
     "primary_keyword": "Google Calendar for HR",
     "secondary_keywords": ["HR team calendar", "recruiting scheduling", "onboarding calendar"],
     "competitor_ref": "https://savvycal.com/articles/team-meeting-agenda/"},

    {"id": 76, "cluster": 7, "cluster_name": "Role-Specific Calendar",
     "slug": "executive-calendar-management",
     "title": "Executive Calendar Management: Tips for EAs and Chiefs of Staff",
     "seo_title": "Executive Calendar Management: How EAs Keep Leaders Organized",
     "category": "Role-specific",
     "primary_keyword": "executive calendar management",
     "secondary_keywords": ["EA calendar management", "executive assistant scheduling", "chief of staff calendar"],
     "competitor_ref": "https://reclaim.ai/blog/productivity-report-one-on-one-meetings"},

    # ── Cluster 8: Calendar Health & Habits (11) ─────────────────────────────
    {"id": 77, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "calendar-burnout-signs",
     "title": "7 Signs Your Calendar Is Causing Burnout",
     "seo_title": "Calendar Burnout: 7 Warning Signs and How to Respond",
     "category": "Calendar health",
     "primary_keyword": "calendar burnout",
     "secondary_keywords": ["schedule burnout", "overbooked calendar burnout", "meeting exhaustion"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 78, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "no-meeting-day-implementation",
     "title": "How to Implement a No-Meeting Day Your Team Will Respect",
     "seo_title": "No-Meeting Day: How to Set It Up and Keep It Sacred",
     "category": "Calendar health",
     "primary_keyword": "no-meeting day implementation",
     "secondary_keywords": ["no meeting day policy", "meeting-free day team", "focus day implementation"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    {"id": 79, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "calendar-detox-guide",
     "title": "Calendar Detox: How to Reset a Broken Schedule",
     "seo_title": "Calendar Detox: A Step-by-Step Guide to Resetting an Overloaded Schedule",
     "category": "Calendar health",
     "primary_keyword": "calendar detox",
     "secondary_keywords": ["schedule reset", "calendar cleanse", "calendar rebuild"],
     "competitor_ref": "https://savvycal.com/articles/scheduling-conflicts/"},

    {"id": 80, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "work-life-balance-calendar",
     "title": "Using Your Calendar to Protect Work-Life Balance",
     "seo_title": "Work-Life Balance Through Calendar: How to Make Boundaries Visible",
     "category": "Calendar health",
     "primary_keyword": "work-life balance calendar",
     "secondary_keywords": ["calendar work life balance", "protect personal time", "schedule boundaries"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 81, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "calendar-anxiety-reduction",
     "title": "Calendar Anxiety: How to Stop Dreading Your Own Schedule",
     "seo_title": "Reducing Calendar Anxiety: Why Your Schedule Feels Overwhelming and What to Do",
     "category": "Calendar health",
     "primary_keyword": "calendar anxiety",
     "secondary_keywords": ["schedule anxiety", "overwhelmed by calendar", "meeting dread"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 82, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "sustainable-scheduling-habits",
     "title": "5 Scheduling Habits That Make the Workweek Feel Sustainable",
     "seo_title": "Sustainable Scheduling: 5 Habits That Stop the Week From Feeling Brutal",
     "category": "Calendar health",
     "primary_keyword": "sustainable scheduling habits",
     "secondary_keywords": ["sustainable work schedule", "healthy scheduling", "long-term scheduling habits"],
     "competitor_ref": "https://reclaim.ai/blog/remote-work-best-practices"},

    {"id": 83, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "calendar-boundaries-coworkers",
     "title": "Setting Calendar Boundaries With Coworkers",
     "seo_title": "Calendar Boundaries With Coworkers: How to Say No Without Saying No",
     "category": "Calendar health",
     "primary_keyword": "calendar boundaries coworkers",
     "secondary_keywords": ["coworker meeting boundaries", "protect calendar colleagues", "say no meetings"],
     "competitor_ref": "https://savvycal.com/articles/defensive-calendaring/"},

    {"id": 84, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "overbooked-week-recovery",
     "title": "How to Recover From an Overbooked Week",
     "seo_title": "Overbooked Week Recovery: How to Rebalance When Your Calendar Goes Off the Rails",
     "category": "Calendar health",
     "primary_keyword": "overbooked week recovery",
     "secondary_keywords": ["too many commitments", "calendar recovery", "overcommitted schedule"],
     "competitor_ref": "https://reclaim.ai/blog/burnout-trends-report"},

    {"id": 85, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "stop-overplanning-calendar",
     "title": "How to Stop Overplanning Your Calendar",
     "seo_title": "Overplanning Your Calendar: Signs You're Doing It and How to Stop",
     "category": "Calendar health",
     "primary_keyword": "stop overplanning calendar",
     "secondary_keywords": ["overplanning schedule", "calendar perfectionism", "over-scheduling"],
     "competitor_ref": "https://savvycal.com/articles/scheduling-conflicts/"},

    {"id": 86, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "simpler-calendar-less-stress",
     "title": "How a Simpler Calendar Reduces Daily Stress",
     "seo_title": "Simpler Calendar, Less Stress: Why Reduction Is a Productivity Strategy",
     "category": "Calendar health",
     "primary_keyword": "simpler calendar stress reduction",
     "secondary_keywords": ["minimal calendar stress", "reduce schedule complexity", "calendar simplicity"],
     "competitor_ref": "https://savvycal.com/articles/calendar-optimization/"},

    {"id": 87, "cluster": 8, "cluster_name": "Calendar Health",
     "slug": "meeting-exhaustion-recovery",
     "title": "Recovering From Meeting Exhaustion: A Calendar Reset Plan",
     "seo_title": "Meeting Exhaustion Recovery: How to Rebalance a Meeting-Heavy Schedule",
     "category": "Calendar health",
     "primary_keyword": "meeting exhaustion recovery",
     "secondary_keywords": ["meeting fatigue recovery", "video call fatigue", "zoom fatigue calendar"],
     "competitor_ref": "https://reclaim.ai/blog/smart-meetings-report"},

    # ── Cluster 9: Comparisons & Context (12) ────────────────────────────────
    {"id": 88, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "google-calendar-vs-outlook",
     "title": "Google Calendar vs. Outlook Calendar: Key Differences for Individuals",
     "seo_title": "Google Calendar vs. Outlook Calendar: Which Should You Use in 2026?",
     "category": "Comparison",
     "primary_keyword": "Google Calendar vs Outlook",
     "secondary_keywords": ["Outlook vs Google Calendar", "calendar comparison", "which calendar app"],
     "competitor_ref": "https://savvycal.com/articles/best-calendar-apps/"},

    {"id": 89, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "google-calendar-vs-apple-calendar",
     "title": "Google Calendar vs. Apple Calendar: Which Fits Your Workflow?",
     "seo_title": "Google Calendar vs. Apple Calendar: An Honest Comparison for 2026",
     "category": "Comparison",
     "primary_keyword": "Google Calendar vs Apple Calendar",
     "secondary_keywords": ["Apple Calendar vs Google Calendar", "iCal vs Google Calendar", "best calendar app Mac"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-vs-apple-calendar/"},

    {"id": 90, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "google-calendar-vs-notion-calendar",
     "title": "Google Calendar vs. Notion Calendar: When Each Makes Sense",
     "seo_title": "Google Calendar vs. Notion Calendar: Two Different Tools for Two Different Needs",
     "category": "Comparison",
     "primary_keyword": "Google Calendar vs Notion Calendar",
     "secondary_keywords": ["Notion calendar features", "Notion vs Google Calendar", "calendar and notes integration"],
     "competitor_ref": "https://savvycal.com/articles/best-calendar-apps/"},

    {"id": 91, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "best-google-calendar-extensions-2026",
     "title": "Best Google Calendar Extensions in 2026 (Honest Comparison)",
     "seo_title": "Best Google Calendar Chrome Extensions in 2026: A No-Fluff Comparison",
     "category": "Comparison",
     "primary_keyword": "best Google Calendar extensions 2026",
     "secondary_keywords": ["top calendar extensions Chrome", "Google Calendar chrome extension list", "calendar extension comparison"],
     "competitor_ref": "https://fellow.ai/blog/google-calendar-extensions-to-boost-productivity/"},

    {"id": 92, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "free-vs-paid-calendar-tools",
     "title": "Free vs. Paid Calendar Tools: What You Actually Need",
     "seo_title": "Free vs. Paid Calendar Tools: When to Pay and When the Free Tier Is Enough",
     "category": "Comparison",
     "primary_keyword": "free vs paid calendar tools",
     "secondary_keywords": ["free calendar app", "paid calendar subscription", "calendar tool cost"],
     "competitor_ref": "https://savvycal.com/articles/best-calendar-apps/"},

    {"id": 93, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "calendar-tools-small-teams",
     "title": "Calendar Tools for Small Teams That Don't Want Complexity",
     "seo_title": "Best Calendar Tools for Small Teams in 2026: Simple Over Sophisticated",
     "category": "Comparison",
     "primary_keyword": "calendar tools small teams",
     "secondary_keywords": ["small team scheduling", "simple team calendar", "startup calendar tools"],
     "competitor_ref": "https://savvycal.com/articles/team-productivity-apps-tools/"},

    {"id": 94, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "minimalist-calendar-setup",
     "title": "The Minimalist Calendar Setup: Less Noise, More Signal",
     "seo_title": "Minimalist Calendar Setup: How Removing Features Improves Your Week",
     "category": "Comparison",
     "primary_keyword": "minimalist calendar setup",
     "secondary_keywords": ["minimal calendar system", "simple calendar setup", "less calendar noise"],
     "competitor_ref": "https://savvycal.com/articles/defensive-calendaring/"},

    {"id": 95, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "ai-calendar-tools-overview",
     "title": "AI Calendar Tools in 2026: What They Do (and What They Don't)",
     "seo_title": "AI Calendar Tools in 2026: An Honest Look at What They Actually Deliver",
     "category": "Comparison",
     "primary_keyword": "AI calendar tools 2026",
     "secondary_keywords": ["AI scheduling tools", "AI calendar assistant", "automated calendar AI"],
     "competitor_ref": "https://reclaim.ai/blog/google-calendar-add-ons"},

    {"id": 96, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "best-calendar-apps-mac",
     "title": "Best Calendar Apps for Mac Users in 2026",
     "seo_title": "Best Calendar Apps for Mac in 2026: Options Worth Using",
     "category": "Comparison",
     "primary_keyword": "best calendar apps Mac 2026",
     "secondary_keywords": ["Mac calendar app", "calendar for macOS", "best Mac scheduling app"],
     "competitor_ref": "https://savvycal.com/articles/best-calendar-apps/"},

    {"id": 97, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "google-calendar-for-chrome-users",
     "title": "Getting More From Google Calendar If You Live in Chrome",
     "seo_title": "Google Calendar for Chrome Power Users: Features and Extensions Worth Knowing",
     "category": "Comparison",
     "primary_keyword": "Google Calendar Chrome users",
     "secondary_keywords": ["Google Calendar Chrome tips", "power user calendar", "Chrome calendar workflow"],
     "competitor_ref": "https://savvycal.com/articles/best-productivity-chrome-extensions/"},

    {"id": 98, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "calendar-productivity-data",
     "title": "What the Data Says About Calendar Habits and Productivity",
     "seo_title": "Calendar and Productivity: What Research and Surveys Actually Show",
     "category": "Comparison",
     "primary_keyword": "calendar productivity research",
     "secondary_keywords": ["calendar habits data", "productivity statistics calendar", "meeting overload statistics"],
     "competitor_ref": "https://reclaim.ai/blog/smart-meetings-report"},

    {"id": 99, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "google-calendar-power-user-tips",
     "title": "Google Calendar Tips Most Power Users Never Discover",
     "seo_title": "Advanced Google Calendar Tips: What Power Users Know That You Might Not",
     "category": "Comparison",
     "primary_keyword": "Google Calendar power user tips",
     "secondary_keywords": ["advanced Google Calendar", "hidden calendar features", "Google Calendar tricks"],
     "competitor_ref": "https://savvycal.com/articles/google-calendar-hacks/"},

    {"id": 100, "cluster": 9, "cluster_name": "Comparisons & Context",
     "slug": "future-of-calendar-productivity",
     "title": "The Future of Calendar Productivity: Trends Worth Watching",
     "seo_title": "Future of Calendar Productivity: Where Scheduling Is Heading",
     "category": "Comparison",
     "primary_keyword": "future calendar productivity",
     "secondary_keywords": ["calendar trends 2026", "future of scheduling", "calendar productivity future"],
     "competitor_ref": "https://reclaim.ai/blog/setting-work-priorities-report"},
]

# ─── Internal linking map ─────────────────────────────────────────────────────
# Pre-compute: for each article, pick 2 related articles from the same cluster.
# Falls back to closest-cluster neighbors if cluster is small.

def build_link_map(articles: list[dict]) -> dict[int, list[int]]:
    """Return {article_id: [related_id_1, related_id_2]}."""
    by_cluster: dict[int, list[int]] = {}
    for a in articles:
        by_cluster.setdefault(a["cluster"], []).append(a["id"])

    link_map: dict[int, list[int]] = {}
    for a in articles:
        cluster_peers = [i for i in by_cluster[a["cluster"]] if i != a["id"]]
        # take first 2 peers; if cluster has only 1 member borrow from adjacent cluster
        peers = cluster_peers[:2]
        if len(peers) < 2:
            adj_cluster = (a["cluster"] % 9) + 1
            extra = [i for i in by_cluster.get(adj_cluster, []) if i != a["id"]]
            peers += extra[: 2 - len(peers)]
        link_map[a["id"]] = peers[:2]
    return link_map

LINK_MAP = build_link_map(ARTICLES)
ID_TO_ARTICLE = {a["id"]: a for a in ARTICLES}

# ─── Date assignment ──────────────────────────────────────────────────────────

def article_date(idx: int) -> date:
    """Spread 100 articles starting from START_DATE, DAYS_GAP apart."""
    return START_DATE + timedelta(days=idx * DAYS_GAP)

# ─── HTML template ────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_description}">
    <title>{seo_title} | Schedule Calendar</title>
    <link rel="canonical" href="{site_url}/blog/{slug}.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:image" content="{site_url}/images/screenshot1.png">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{pub_date}">
    <meta property="article:author" content="Schedule Calendar Team">
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../css/site-refresh.css?v=20260326">
    <link rel="icon" type="image/png" href="../images/logo.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{title}",
        "description": "{meta_description}",
        "author": {{"@type": "Organization", "name": "Schedule Calendar Team"}},
        "publisher": {{
            "@type": "Organization",
            "name": "Schedule Calendar",
            "logo": {{"@type": "ImageObject", "url": "{site_url}/images/logo.png"}}
        }},
        "datePublished": "{pub_date}",
        "dateModified": "{pub_date}",
        "mainEntityOfPage": "{site_url}/blog/{slug}.html",
        "image": "{site_url}/images/screenshot1.png"
    }}
    </script>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{faq_schema}]
    }}
    </script>
</head>

<body class="schedule-article">
    <div class="scroll-progress"></div>

    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand">
                    <img src="../images/logo.png" alt="Schedule Calendar logo" class="logo" width="42" height="42">
                    <span class="brand-name">Schedule Calendar</span>
                </div>
                <ul class="nav-menu">
                    <li><a href="../index.html">Home</a></li>
                    <li><a href="../index.html#features">Features</a></li>
                    <li><a href="./">Blog</a></li>
                    <li><a href="../support.html">Support</a></li>
                    <li>
                        <a href="{store_url}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">
                            Add to Chrome
                        </a>
                    </li>
                </ul>
                <button class="hamburger" aria-label="Toggle navigation menu" aria-expanded="false" tabindex="0">
                    <span aria-hidden="true"></span>
                    <span aria-hidden="true"></span>
                    <span aria-hidden="true"></span>
                </button>
            </div>
        </nav>
    </header>

    <div class="nav-overlay"></div>

    <main class="blog-main">
        <div class="container">
            <section class="article-hero">
                <div class="article-breadcrumbs">
                    <a href="./" class="text-link">Blog</a>
                    <span>/</span>
                    <span>{category}</span>
                </div>
                <div class="eyebrow">Published {pub_date_human}</div>
                <h1 class="article-title">{title}</h1>
                <p class="article-intro">{intro}</p>
                <p class="article-meta">{read_time} min read · Written by the Schedule Calendar Team</p>
            </section>

            <section class="article-layout">
                <article class="article-body-card">
                    <img src="../images/screenshot1.png"
                        alt="Schedule Calendar Chrome extension showing upcoming events"
                        class="article-cover" width="1365" height="768">

                    {body_html}

                    <section class="article-faq" aria-label="Frequently asked questions">
                        <h2>Frequently asked questions</h2>
                        {faq_html}
                    </section>
                </article>

                <aside class="article-sidebar">
                    <h3>Key takeaways</h3>
                    <ul>
                        {sidebar_takeaways}
                    </ul>

                    <h3>Try next</h3>
                    <p>{sidebar_cta_text}</p>
                    <a href="{store_url}" class="btn btn-primary" target="_blank" rel="noopener">Add to Chrome</a>
                </aside>
            </section>

            <section class="section">
                <div class="section-header">
                    <span class="section-kicker">Related reading</span>
                    <h2 class="section-title">{related_title}</h2>
                </div>

                <div class="related-grid">
                    {related_cards}
                </div>
            </section>
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-card">
                    <div class="nav-brand">
                        <img src="../images/logo.png" alt="Schedule Calendar logo" class="footer-logo" width="42" height="42">
                        <span class="footer-brand-name">Schedule Calendar</span>
                    </div>
                    <p class="footer-description">Workflow notes for people who want their calendar to support the day, not dominate it.</p>
                </div>

                <div class="footer-card">
                    <h4>Read next</h4>
                    <ul class="footer-links">
                        {footer_links}
                    </ul>
                </div>

                <div class="footer-card">
                    <h4>Explore</h4>
                    <ul class="footer-links">
                        <li><a href="../index.html">Home</a></li>
                        <li><a href="../support.html">Support</a></li>
                        <li><a href="../privacy-policy.html">Privacy Policy</a></li>
                    </ul>
                </div>
            </div>

            <div class="footer-bottom">
                <p>&copy; 2026 Schedule Calendar. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <button class="back-to-top" aria-label="Back to top">
        <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z" />
        </svg>
    </button>

    <script src="../js/script.js?v=20260326"></script>
</body>

</html>
"""

MEDIUM_TEMPLATE = """\
# {title}

*Originally published on [Schedule Calendar Blog]({site_url}/blog/{slug}.html)*

---

{medium_body}

---

**Want the full guide?** Read the complete article on the [Schedule Calendar blog]({site_url}/blog/{slug}.html) — including step-by-step tips, a FAQ section, and how a lightweight Chrome extension can help you put these habits into practice without adding more friction to your day.

[Add Schedule Calendar to Chrome]({store_url}) — free, no account required.
"""

DEVTO_TEMPLATE = """\
---
title: "{title}"
published: false
description: "{meta_description}"
tags: {tags}
canonical_url: {site_url}/blog/{slug}.html
---

{devto_body}

---

*[Schedule Calendar]({store_url}) — free Chrome extension. Your Google Calendar in one click from the toolbar.*
"""

# ─── Claude prompt ────────────────────────────────────────────────────────────

def build_prompt(article: dict, related: list[dict], competitor_text: str = "") -> str:
    related_context = "\n".join(
        f'  - "{r["title"]}" → {r["slug"]}.html' for r in related
    )
    secondary = ", ".join(article["secondary_keywords"])
    competitor_block = ""
    if competitor_text:
        competitor_block = f"""
COMPETITOR REFERENCE (read and understand — do NOT copy, translate, or closely rephrase):
---
{competitor_text}
---
Use the above only to understand what angles and subtopics the competitor covers.
Your article must take a DIFFERENT angle, use different examples, and add value the competitor doesn't provide.
Specifically: center the narrative on lightweight, browser-first calendar habits — not on AI tools or enterprise software.
"""
    return f"""You are a senior content strategist writing for Schedule Calendar (calendar-extension.site).
Schedule Calendar is a lightweight Google Calendar Chrome extension that shows events in a browser popup — no extra tab needed.
The brand voice is: calm, practical, direct. No hype. No buzzwords. Like a thoughtful colleague explaining something useful.

Write a complete semantic SEO article. This is NOT a translation or copy of any competitor article.
It is an ORIGINAL piece that covers the topic from our angle: lightweight, browser-first calendar workflow.
{competitor_block}
ARTICLE TOPIC: {article["title"]}
PRIMARY KEYWORD: {article["primary_keyword"]}
SECONDARY KEYWORDS: {secondary}
CLUSTER: {article["cluster_name"]}

RELATED ARTICLES IN SAME CLUSTER (for internal links, use these slugs):
{related_context}

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:

{{
  "meta_description": "string, 140-155 chars, includes primary keyword",
  "intro": "string, 2-3 sentences, hooks the reader on the specific problem",
  "read_time": number (integer, estimated minutes based on word count),
  "body_sections": [
    {{
      "type": "h2|h2_h3|note|cta|product|ul|ol",
      "heading": "string or null",
      "subheadings": ["string"] or null,
      "content": "string (plain text paragraphs, use \\n\\n to separate)",
      "bullets": ["string"] or null
    }}
  ],
  "sidebar_takeaways": ["string (max 12 words each)", ...],
  "sidebar_cta_text": "string, 1-2 sentences, why try Schedule Calendar",
  "related_title": "string, 6-10 words, thematic bridge sentence",
  "faq": [
    {{"question": "string", "answer": "string, 2-4 sentences, direct answer for GEO"}}
  ],
  "medium_body": "string, 400-550 words, adapted version for Medium. Covers 3-4 key insights from the article. Uses \\n\\n between paragraphs. Naturally references scheduling and calendar workflow. Does NOT copy the blog article verbatim.",
  "devto_body": "string, 350-450 words, adapted for dev.to audience (developers, engineers). Practical, code-adjacent tone. Uses markdown headers (##) and bullet lists. Naturally mentions the scheduling/calendar workflow. Does NOT copy medium_body verbatim.",
  "devto_tags": "string, exactly 4 comma-separated tags for dev.to, lowercase, no spaces (e.g. productivity,googlecalendar,chrome,timemanagement)"
}}

REQUIREMENTS:
- body_sections: 5-7 sections total. Use type "note" for callout boxes, "cta" for action-oriented callouts, "product" for the 'How Schedule Calendar helps' section.
- At least one internal link to a related article must appear naturally in body content as: <a href="./SLUG.html" class="text-link">anchor text</a>
- faq: exactly 6 items. Questions must be natural language questions a user would type or speak. Answers must be direct, complete, and GEO-optimized (could stand alone as a featured snippet).
- No keyword stuffing. Semantic coverage over exact-match repetition.
- Do not mention competitors by name.
- Word count target: 750-950 words for blog body (not counting FAQ).
- medium_body: must feel like a standalone read, not a teaser. Gives real value.
- devto_body: written for developers. Use ## headers, short paragraphs, bullet lists. Practical, low-fluff tone.
- devto_tags: must be exactly 4 tags, lowercase, no spaces (e.g. productivity,googlecalendar,chrome,timemanagement).
"""

# ─── Article builder ──────────────────────────────────────────────────────────

def sections_to_html(sections: list[dict]) -> str:
    parts = []
    for s in sections:
        t = s.get("type", "h2")
        heading = s.get("heading")
        content = s.get("content", "")
        bullets = s.get("bullets") or []
        subheadings = s.get("subheadings") or []

        if t == "note":
            inner = content.replace("\n\n", "</p>\n<p>")
            parts.append(f'<div class="article-note">\n<p>{inner}</p>\n</div>')
        elif t == "cta":
            inner = content.replace("\n\n", "</p>\n<p>")
            parts.append(f'<div class="article-cta">\n<p>{inner}</p>\n</div>')
        elif t == "ul":
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            items = "".join(f"<li>{b}</li>\n" for b in bullets)
            parts.append(f"<ul>\n{items}</ul>")
        elif t == "ol":
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            items = "".join(f"<li>{b}</li>\n" for b in bullets)
            parts.append(f"<ol>\n{items}</ol>")
        elif t == "h2_h3":
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            for i, sub in enumerate(subheadings):
                parts.append(f"<h3>{sub}</h3>")
                # split content into paragraphs distributed across subheadings
                paras = content.split("\n\n")
                per = max(1, len(paras) // max(len(subheadings), 1))
                chunk = paras[i * per : (i + 1) * per]
                for p in chunk:
                    if p.strip():
                        parts.append(f"<p>{p.strip()}</p>")
        else:  # default h2
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            for para in content.split("\n\n"):
                if para.strip():
                    parts.append(f"<p>{para.strip()}</p>")
            if bullets:
                items = "".join(f"<li>{b}</li>\n" for b in bullets)
                parts.append(f"<ul>\n{items}</ul>")

    return "\n\n".join(parts)


def faq_to_html(faq: list[dict]) -> str:
    items = []
    for i, item in enumerate(faq, start=1):
        q = item["question"]
        a = item["answer"]
        items.append(
            f'<div class="faq-item">\n'
            f'  <button class="faq-question" role="button" '
            f'id="faq-question-{i}" aria-controls="faq-answer-{i}" aria-expanded="false">\n'
            f'    <h3>{q}</h3>\n'
            f'    <span class="faq-toggle" aria-hidden="true">+</span>\n'
            f'  </button>\n'
            f'  <div class="faq-answer" id="faq-answer-{i}" role="region" '
            f'aria-labelledby="faq-question-{i}">\n'
            f'    <p>{a}</p>\n'
            f'  </div>\n'
            f'</div>'
        )
    return f'<div class="faq-list">\n' + "\n".join(items) + "\n</div>"


def faq_to_schema(faq: list[dict]) -> str:
    entries = []
    for item in faq:
        q = item["question"].replace('"', '\\"')
        a = item["answer"].replace('"', '\\"')
        entries.append(
            f'{{"@type": "Question", "name": "{q}", '
            f'"acceptedAnswer": {{"@type": "Answer", "text": "{a}"}}}}'
        )
    return ",\n        ".join(entries)


def related_cards_html(related: list[dict]) -> str:
    cards = []
    for r in related:
        cards.append(
            f'<article class="related-card">\n'
            f'  <h3>{r["title"]}</h3>\n'
            f'  <p>From the {r["cluster_name"]} series.</p>\n'
            f'  <a href="./{r["slug"]}.html" class="read-more">Read article →</a>\n'
            f'</article>'
        )
    return "\n".join(cards)


def footer_links_html(related: list[dict]) -> str:
    lines = ['<li><a href="./">Blog home</a></li>']
    for r in related:
        lines.append(f'<li><a href="./{r["slug"]}.html">{r["title"]}</a></li>')
    return "\n".join(lines)


def render_html(article: dict, data: dict, related: list[dict], idx: int) -> str:
    pub = article_date(idx)
    pub_str = pub.isoformat()
    pub_human = pub.strftime("%B %-d, %Y")

    body_html = sections_to_html(data["body_sections"])
    faq_html = faq_to_html(data["faq"])
    faq_schema = faq_to_schema(data["faq"])
    takeaways = "\n".join(f"<li>{t}</li>" for t in data["sidebar_takeaways"])

    return HTML_TEMPLATE.format(
        site_url=SITE_URL,
        store_url=STORE_URL,
        slug=article["slug"],
        seo_title=article["seo_title"],
        title=article["title"],
        meta_description=data["meta_description"],
        category=article["category"],
        pub_date=pub_str,
        pub_date_human=pub_human,
        intro=data["intro"],
        read_time=data["read_time"],
        body_html=body_html,
        faq_schema=faq_schema,
        faq_html=faq_html,
        sidebar_takeaways=takeaways,
        sidebar_cta_text=data["sidebar_cta_text"],
        related_title=data["related_title"],
        related_cards=related_cards_html(related),
        footer_links=footer_links_html(related),
    )


def render_medium(article: dict, data: dict) -> str:
    return MEDIUM_TEMPLATE.format(
        site_url=SITE_URL,
        store_url=STORE_URL,
        slug=article["slug"],
        title=article["title"],
        medium_body=data["medium_body"],
    )


def render_devto(article: dict, data: dict) -> str:
    return DEVTO_TEMPLATE.format(
        site_url=SITE_URL,
        store_url=STORE_URL,
        slug=article["slug"],
        title=article["title"],
        meta_description=data["meta_description"],
        tags=data.get("devto_tags", "productivity,googlecalendar,chrome,timemanagement"),
        devto_body=data["devto_body"],
    )

# ─── Blog index updater ───────────────────────────────────────────────────────

def update_blog_index(generated: list[dict]) -> None:
    """Rewrite blog/index.html article grid to include all generated articles."""
    index_path = BLOG_DIR / "index.html"
    if not index_path.exists():
        print("  ⚠  blog/index.html not found — skipping index update")
        return

    content = index_path.read_text(encoding="utf-8")

    # Build new card grid grouped by cluster
    by_cluster: dict[str, list[dict]] = {}
    for a in generated:
        cn = a["cluster_name"]
        by_cluster.setdefault(cn, []).append(a)

    cards = []
    for cluster_name, items in by_cluster.items():
        for a in items:
            pub = article_date(a["id"] - 1)
            pub_human = pub.strftime("%b %-d, %Y")
            cards.append(
                f'<article class="blog-card">\n'
                f'  <div class="blog-card-meta">{pub_human} · {a["category"]}</div>\n'
                f'  <h2 class="blog-card-title">'
                f'<a href="./{a["slug"]}.html">{a["title"]}</a></h2>\n'
                f'  <p class="blog-card-excerpt">{a["cluster_name"]} series.</p>\n'
                f'  <a href="./{a["slug"]}.html" class="read-more">Read →</a>\n'
                f'</article>'
            )

    new_grid = '\n'.join(cards)
    # Replace content between markers if present, otherwise append
    marker_start = "<!-- ARTICLES_START -->"
    marker_end = "<!-- ARTICLES_END -->"
    if marker_start in content and marker_end in content:
        new_content = re.sub(
            re.escape(marker_start) + r".*?" + re.escape(marker_end),
            f"{marker_start}\n{new_grid}\n{marker_end}",
            content,
            flags=re.DOTALL,
        )
        index_path.write_text(new_content, encoding="utf-8")
        print(f"  ✓ blog/index.html updated ({len(cards)} cards)")
    else:
        print("  ⚠  blog/index.html has no <!-- ARTICLES_START --> markers — skipping auto-update")
        print("     Add <!-- ARTICLES_START --> and <!-- ARTICLES_END --> around the article grid.")

# ─── Generator ────────────────────────────────────────────────────────────────

def generate_article(client: anthropic.Anthropic, article: dict, idx: int, dry_run: bool) -> bool:
    slug = article["slug"]
    html_path = BLOG_DIR / f"{slug}.html"
    md_path = MEDIUM_DIR / f"{slug}.md"
    devto_path = DEVTO_DIR / f"{slug}.md"

    if html_path.exists() and md_path.exists() and devto_path.exists():
        print(f"  ↷  #{article['id']:03d} {slug} — already exists, skipping")
        return True

    related_ids = LINK_MAP.get(article["id"], [])
    related = [ID_TO_ARTICLE[i] for i in related_ids if i in ID_TO_ARTICLE]

    if dry_run:
        print(f"  [DRY] #{article['id']:03d} {slug}")
        print(f"         → related: {[r['slug'] for r in related]}")
        return True

    print(f"  ⟳  #{article['id']:03d} {slug} …", end="", flush=True)

    # Fetch competitor article for editorial reference (non-blocking)
    competitor_text = ""
    if article.get("competitor_ref"):
        competitor_text = fetch_competitor_content(article["competitor_ref"])

    prompt = build_prompt(article, related, competitor_text)
    try:
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f" ✗ JSON parse error: {e}")
        return False
    except anthropic.APIError as e:
        print(f" ✗ API error: {e}")
        return False

    BLOG_DIR.mkdir(exist_ok=True)
    MEDIUM_DIR.mkdir(exist_ok=True)
    DEVTO_DIR.mkdir(exist_ok=True)

    html_path.write_text(render_html(article, data, related, idx), encoding="utf-8")
    md_path.write_text(render_medium(article, data), encoding="utf-8")
    devto_path.write_text(render_devto(article, data), encoding="utf-8")

    print(f" ✓  ({data['read_time']} min read)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate blog articles for calendar-extension.site")
    parser.add_argument("--id", type=int, help="Generate a single article by plan ID (1-100)")
    parser.add_argument("--cluster", type=int, choices=range(1, 10), help="Generate one cluster (1-9)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without calling API")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between API calls (default 2)")
    args = parser.parse_args()

    if not args.dry_run:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit("ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=sk-ant-...")
        client = anthropic.Anthropic(api_key=api_key)
    else:
        client = None  # type: ignore

    targets = ARTICLES
    if args.id:
        targets = [a for a in ARTICLES if a["id"] == args.id]
        if not targets:
            raise SystemExit(f"No article with id={args.id}")
    elif args.cluster:
        targets = [a for a in ARTICLES if a["cluster"] == args.cluster]

    print(f"\nSchedule Calendar — Article Generator")
    print(f"Target: {len(targets)} article(s)  |  dry-run: {args.dry_run}\n")

    ok = 0
    fail = 0
    for i, article in enumerate(targets):
        idx = article["id"] - 1  # 0-based for date offset
        success = generate_article(client, article, idx, args.dry_run)
        if success:
            ok += 1
        else:
            fail += 1
        if not args.dry_run and i < len(targets) - 1:
            time.sleep(args.delay)

    print(f"\nDone — {ok} succeeded, {fail} failed")

    if not args.dry_run and ok > 0:
        update_blog_index(ARTICLES)
        print("\nNext step: add <!-- ARTICLES_START --> and <!-- ARTICLES_END -->")
        print("markers to blog/index.html around the article grid, then re-run.")


if __name__ == "__main__":
    main()
