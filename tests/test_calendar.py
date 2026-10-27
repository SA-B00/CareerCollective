from datetime import date
from urllib.parse import parse_qs, urlparse

from calendar_ui import (parse_iso, deadline_events, dashboard_counts, event_color,
                         filter_events, build_ics, google_event_url)

ROWS = [
    {"job_id":"a", "title":"Assistant Events", "company":"Test (DEMO)", "deadline":"2026-10-29", "status":"Saved", "applied_on":"", "source":"FICTIONAL DEMO - not sent", "url":""},
    {"job_id":"b", "title":"Stage Data", "company":"DataCo", "deadline":"2026-11-20", "status":"Applied", "applied_on":"2026-10-23", "source":"manual", "url":"https://example.com"},
    {"job_id":"c", "title":"Marketing", "company":"Test (DEMO)", "deadline":"2026-10-20", "status":"Saved", "applied_on":"", "source":"FICTIONAL DEMO - not sent", "url":""},
    {"job_id":"d", "title":"Marketing", "company":"Other", "deadline":"", "status":"Interview", "applied_on":"2026-10-24", "source":"manual", "url":""},
]

def test_exact_calendar_dates():
    assert parse_iso("2026-10-29") == date(2026,10,29)
    assert parse_iso("2026-02-30") is None
    assert parse_iso("29/10/2026") is None


def test_calendar_counts_and_filters():
    expected={"urgent":1, "progress":2, "apply":2, "overdue":1}
    assert dashboard_counts(ROWS,date(2026,10,27)) == expected
    events=deadline_events(ROWS)
    assert len(events)==5
    assert len(filter_events(events,"urgent",date(2026,10,27)))==1
    assert len(filter_events(events,"overdue",date(2026,10,27)))==1
    assert event_color(filter_events(events,"urgent",date(2026,10,27))[0],date(2026,10,27))=="urgent"
    assert len(filter_events(events,"progress"))==3


def test_ics_is_interoperable_and_fictional_labelled():
    events=deadline_events(ROWS)
    payload=build_ics(events).decode("utf-8")
    assert payload.startswith("BEGIN:VCALENDAR\r\n")
    assert payload.count("BEGIN:VEVENT")==5
    assert "DTSTART;VALUE=DATE:20261029" in payload
    assert "DTEND;VALUE=DATE:20261030" in payload
    assert "[DEMO]" in payload
    assert "FICTIONAL EXAMPLE" in payload.replace("\r\n ", "")
    assert "TRIGGER:-P1D" in payload
    assert all(len(line.encode("utf-8"))<=75 for line in payload.split("\r\n") if line)


def test_google_link_for_calendar_event():
    ev=filter_events(deadline_events(ROWS),"urgent",date(2026,10,27))[0]
    url=google_event_url(ev)
    args=parse_qs(urlparse(url).query)
    assert args["dates"][0]=="20261029/20261030"
    assert "DEMO" in args["text"][0]
    assert args["action"][0]=="TEMPLATE"