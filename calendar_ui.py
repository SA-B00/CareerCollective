"""Accessible, session-based CareerCollective calendar and interoperable calendar exports.

There is no account connection or continuous calendar synchronization. Each downloaded
ICS file is a one-time snapshot. Google Calendar URLs open an event composer.
"""
from __future__ import annotations

import calendar
import hashlib
from datetime import date, timedelta
from urllib.parse import urlencode

ACTIVE = {"Saved", "Applied", "Interview"}
IN_PROGRESS = {"Applied", "Interview"}


def parse_iso(value):
    """Accept only exact ISO calendar dates, without guessing or timezone shifts."""
    try:
        if not isinstance(value, str) or len(value) != 10:
            return None
        parsed = date.fromisoformat(value)
        return parsed if parsed.isoformat() == value else None
    except (TypeError, ValueError):
        return None


def is_demo(row):
    return "FICTIONAL DEMO" in str(row.get("source", "")).upper() or "(DEMO)" in str(row.get("company", "")).upper()


def deadline_events(rows):
    """Date-only events for published or user-entered deadlines, plus submission history."""
    events = []
    for row in rows:
        due = parse_iso(row.get("deadline", ""))
        applied = parse_iso(row.get("applied_on", ""))
        status = str(row.get("status", "Saved"))
        if due:
            events.append({"date": due, "kind": "deadline", "status": status, "row": row})
        if applied and status in {"Applied", "Interview", "Offer", "Rejected", "Withdrawn"}:
            events.append({"date": applied, "kind": "application", "status": status, "row": row})
    return sorted(events, key=lambda e: (e["date"], e["kind"], str(e["row"].get("company", ""))))


def dashboard_counts(rows, today=None):
    today = today or date.today()
    counts = {"urgent": 0, "progress": 0, "apply": 0, "overdue": 0}
    for row in rows:
        status = row.get("status", "Saved")
        due = parse_iso(row.get("deadline", ""))
        if status == "Saved":
            counts["apply"] += 1
        if status in IN_PROGRESS:
            counts["progress"] += 1
        if due and status in ACTIVE:
            delta = (due - today).days
            if 0 <= delta <= 7:
                counts["urgent"] += 1
            if delta < 0:
                counts["overdue"] += 1
    return counts


def event_color(event, today=None):
    today = today or date.today()
    due = (event["date"] - today).days
    if event["kind"] == "deadline" and event["status"] in ACTIVE and -36500 <= due <= 7:
        return "urgent"  # Red when imminent, including overdue active positions.
    if event["status"] in IN_PROGRESS or event["kind"] == "application":
        return "progress"  # Green for progress.
    if event["status"] == "Saved":
        return "apply"  # Blue for opportunities awaiting an application.
    return "other"


def filter_events(events, category, today=None):
    today = today or date.today()
    if category == "urgent":
        return [e for e in events if e["kind"] == "deadline" and e["status"] in ACTIVE and 0 <= (e["date"] - today).days <= 7]
    if category == "overdue":
        return [e for e in events if e["kind"] == "deadline" and e["status"] in ACTIVE and e["date"] < today]
    if category == "progress":
        return [e for e in events if e["status"] in IN_PROGRESS]
    if category == "apply":
        return [e for e in events if e["status"] == "Saved"]
    return events


def _escape_ics(value):
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def _fold_ics(line):
    """Fold content lines to RFC 5545's 75-octet limit, preserving Unicode."""
    parts, current, count = [], "", 0
    for char in line:
        width = len(char.encode("utf-8"))
        if count + width > 75:
            parts.append(current)
            current, count = " " + char, 1 + width
        else:
            current += char
            count += width
    parts.append(current)
    return "\r\n".join(parts)


def event_title(event, language="en"):
    row = event["row"]
    prefix = ("Date limite" if language == "fr" else "Deadline") if event["kind"] == "deadline" else ("Candidature envoyée" if language == "fr" else "Application recorded")
    suffix = " [DEMO]" if is_demo(row) else ""
    return f"{prefix}: {row.get('title', 'Opportunity')} | {row.get('company', '')}{suffix}"


def build_ics(events, language="en"):
    """Return one-off, importable .ics bytes. It does not continuously sync."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CareerCollective//Student deadline calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:CareerCollective deadlines"]
    for event in events:
        day = event["date"]
        row = event["row"]
        stable_id = f"{row.get('job_id', '')}|{event['kind']}|{day.isoformat()}"
        uid = hashlib.sha256(stable_id.encode("utf-8")).hexdigest()[:26] + "@careercollective.example"
        details = f"Status: {row.get('status', 'Saved')}. Source: {row.get('source', 'Not listed')}."
        if is_demo(row):
            details += " FICTIONAL EXAMPLE. No real application has been sent."
        if row.get("url", "").startswith(("https://", "http://")):
            details += " URL: " + row["url"]
        fields = ["BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:20261027T110000Z", f"DTSTART;VALUE=DATE:{day:%Y%m%d}", f"DTEND;VALUE=DATE:{(day+timedelta(days=1)):%Y%m%d}", f"SUMMARY:{_escape_ics(event_title(event, language))}", f"DESCRIPTION:{_escape_ics(details)}", "STATUS:CONFIRMED"]
        if event["kind"] == "deadline" and event["status"] == "Saved":
            fields += ["BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:Application deadline tomorrow", "END:VALARM"]
        fields.append("END:VEVENT")
        lines += fields
    lines.append("END:VCALENDAR")
    return ("\r\n".join(_fold_ics(line) for line in lines) + "\r\n").encode("utf-8")


def google_event_url(event, language="en"):
    if event["kind"] != "deadline":
        return ""
    day = event["date"]
    row = event["row"]
    description = f"CareerCollective: {row.get('status', 'Saved')}."
    if is_demo(row):
        description += " Fictional demonstration. No real application was submitted."
    if str(row.get("url", "")).startswith(("https://", "http://")):
        description += " " + row["url"]
    params = {"action": "TEMPLATE", "text": event_title(event, language), "dates": f"{day:%Y%m%d}/{day+timedelta(days=1):%Y%m%d}", "details": description}
    return "https://calendar.google.com/calendar/render?" + urlencode(params)


CALENDAR_STYLE = """
<style>
.st-key-cc_chip_urgent button {background:#fff1f2!important;border:1px solid #f5b6be!important;color:#9e2130!important;font-weight:700!important;}
.st-key-cc_chip_progress button {background:#eaf7f0!important;border:1px solid #a3dcc0!important;color:#17653f!important;font-weight:700!important;}
.st-key-cc_chip_apply button {background:#eaf3ff!important;border:1px solid #bad5ff!important;color:#1b5b9a!important;font-weight:700!important;}
.st-key-cc_chip_overdue button {background:#fff1f2!important;border:1px solid #f2c1c6!important;color:#9e2130!important;font-weight:700!important;}
[class*="st-key-cc_day_urgent_"] button {border:1px solid #e996a0!important;background:#fff0f1!important;color:#9c2231!important;}
[class*="st-key-cc_day_progress_"] button {border:1px solid #a8d9bb!important;background:#effaf2!important;color:#166643!important;}
[class*="st-key-cc_day_apply_"] button {border:1px solid #a8c8f6!important;background:#edf5ff!important;color:#155596!important;}
[class*="st-key-cc_day_other_"] button {border:1px solid #e1e8f2!important;background:#f9fbff!important;color:#42536e!important;}
[class*="st-key-cc_day_"] button {min-height:66px!important;white-space:pre-line!important;padding:0.4rem 0.1rem!important;font-size:0.83rem!important;}
</style>
"""


def render_status_strip(rows, language="en"):
    """Clickable summary chips, routing to the corresponding calendar filter."""
    import streamlit as st

    counts = dashboard_counts(rows)
    labels = {"en": {"urgent": "Deadlines in 7 days", "progress": "In progress", "apply": "To apply", "overdue": "Overdue"}, "fr": {"urgent": "Échéances à 7 jours", "progress": "En cours", "apply": "À postuler", "overdue": "En retard"}}
    st.markdown(CALENDAR_STYLE, unsafe_allow_html=True)

    def navigate(target):
        st.session_state.cc_calendar_filter = target
        st.session_state.nav_page = "calendar"
        dates = [e["date"] for e in filter_events(deadline_events(rows), target)]
        st.session_state.cc_calendar_month = (min(dates).replace(day=1).isoformat() if dates else date.today().replace(day=1).isoformat())
        if dates:
            st.session_state.cc_calendar_date = min(dates).isoformat()

    cols = st.columns(4, gap="small")
    for col, status in zip(cols, ("urgent", "progress", "apply", "overdue")):
        col.button(f"{counts[status]}  |  {labels[language][status]}", key="cc_chip_" + status, use_container_width=True, on_click=navigate, args=(status,))


def render_calendar(rows, language="en"):
    import streamlit as st

    st.markdown(CALENDAR_STYLE, unsafe_allow_html=True)
    today = date.today()
    events = deadline_events(rows)
    filtered = filter_events(events, st.session_state.get("cc_calendar_filter", "all"), today)
    month = parse_iso(st.session_state.get("cc_calendar_month", "")) or today.replace(day=1)
    month = month.replace(day=1)
    selected = parse_iso(st.session_state.get("cc_calendar_date", "")) or today

    st.caption(("Select a date to view its applications and deadlines. Only known deadlines are shown." if language == "en" else "Sélectionnez une date pour consulter les échéances et candidatures. Seules les dates connues sont affichées."))
    filters = {"en": {"all": "All events", "urgent": "Urgent deadlines", "progress": "In progress", "apply": "To apply", "overdue": "Past due"}, "fr": {"all": "Tous les événements", "urgent": "Échéances urgentes", "progress": "En cours", "apply": "À postuler", "overdue": "Dates dépassées"}}
    st.selectbox("Filter / Filtre", list(filters[language]), format_func=lambda key: filters[language][key], key="cc_calendar_filter")

    def move_month(delta):
        value = parse_iso(st.session_state.cc_calendar_month) or today.replace(day=1)
        year, idx = divmod(value.year * 12 + (value.month - 1) + delta, 12)
        st.session_state.cc_calendar_month = date(year, idx + 1, 1).isoformat()

    def jump_today():
        st.session_state.cc_calendar_month = today.replace(day=1).isoformat()
        st.session_state.cc_calendar_date = today.isoformat()

    prev, label, now, nxt = st.columns([1, 3, 1, 1])
    prev.button("Previous" if language == "en" else "Précédent", on_click=move_month, args=(-1,), use_container_width=True)
    label.markdown("### " + month.strftime("%B %Y"))
    now.button("Today" if language == "en" else "Aujourd'hui", on_click=jump_today, use_container_width=True)
    nxt.button("Next" if language == "en" else "Suivant", on_click=move_month, args=(1,), use_container_width=True)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if language == "en" else ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    for col, value in zip(st.columns(7, gap="small"), days):
        col.markdown(f"**{value}**")
    events_by_date = {}
    for event in filtered:
        events_by_date.setdefault(event["date"], []).append(event)

    def select_day(day):
        st.session_state.cc_calendar_date = day.isoformat()

    for week in calendar.monthcalendar(month.year, month.month):
        for col, day_number in zip(st.columns(7, gap="small"), week):
            if not day_number:
                col.write(" ")
                continue
            day = date(month.year, month.month, day_number)
            on_day = events_by_date.get(day, [])
            priority = "other"
            if any(event_color(e, today) == "urgent" for e in on_day):
                priority = "urgent"
            elif any(event_color(e, today) == "progress" for e in on_day):
                priority = "progress"
            elif any(event_color(e, today) == "apply" for e in on_day):
                priority = "apply"
            count_line = f"{len(on_day)} event" + ("s" if len(on_day) != 1 else "") if on_day else " "
            col.button(f"{day_number}\n{count_line}", key=f"cc_day_{priority}_{day:%Y%m%d}", on_click=select_day, args=(day,), use_container_width=True)

    st.markdown("**" + ("Selected date" if language == "en" else "Date sélectionnée") + ": " + selected.isoformat() + "**")
    on_selected = events_by_date.get(selected, [])
    if not on_selected:
        st.caption("No tracked events on this date." if language == "en" else "Aucun événement suivi à cette date.")
    else:
        for number, event in enumerate(on_selected):
            row = event["row"]
            with st.container(border=True):
                st.markdown("**" + event_title(event, language) + "**")
                st.caption(f"{row.get('city', '')} | {row.get('status', '')} | {selected.isoformat()}")
                if is_demo(row):
                    st.caption("FICTIONAL DEMO | No application was submitted" if language == "en" else "DÉMONSTRATION FICTIVE | Aucune candidature envoyée")
                if event["kind"] == "deadline":
                    st.link_button("Add to Google Calendar" if language == "en" else "Ajouter à Google Agenda", google_event_url(event, language))
                st.download_button("Download calendar event (.ics)" if language == "en" else "Télécharger l'événement (.ics)", data=build_ics([event], language), file_name=f"careercollective-{selected.isoformat()}-{number}.ics", mime="text/calendar", key=f"cc_event_export_{selected.isoformat()}_{number}")

    st.divider()
    st.download_button("Export all tracked dates (.ics)" if language == "en" else "Exporter toutes les dates suivies (.ics)", data=build_ics(events, language), file_name="CareerCollective_calendar.ics", mime="text/calendar", type="primary")
    st.caption(("One-time calendar export, compatible with Google Calendar, Outlook and Apple Calendar. Events do not sync automatically after edits to this session." if language == "en" else "Export ponctuel compatible avec Google Agenda, Outlook et Apple Calendar. Les modifications ultérieures ne sont pas synchronisées automatiquement."))