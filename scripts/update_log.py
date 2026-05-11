#!/usr/bin/env python3
"""
Update Research Log — Called by cron tasks to publish daily research to the study space.

Usage:
  python3 scripts/update_log.py --day 2 --title "沟通建立过程" --content "..." --reflection "..."

  # Or with a JSON payload:
  python3 scripts/update_log.py --payload '{"day":2,"title":"...",...}'

The script reads and writes ~/hermes-study-space/data/research.json
"""

import json
import os
import sys
import argparse
import textwrap
from datetime import datetime

RESEARCH_JSON = os.path.expanduser('~/hermes-study-space/data/research.json')


def load_research():
    with open(RESEARCH_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_research(data):
    with open(RESEARCH_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Updated Day {data['phases'][0]['day'] if data['phases'] else '?'} — saved to research.json")


def update_day(day, title=None, summary=None, sections=None, reflections=None, status='completed'):
    data = load_research()
    phase = next((p for p in data['phases'] if p['day'] == day), None)

    if not phase:
        print(f"❌ Day {day} not found in research.json")
        return False

    if title:
        phase['title'] = title
    if summary:
        phase['summary'] = summary
    if status:
        phase['status'] = status
    if sections is not None:
        phase['sections'] = sections
    if reflections is not None:
        phase['reflections'] = reflections

    save_research(data)
    return True


def main():
    parser = argparse.ArgumentParser(description='Update research log day')
    parser.add_argument('--day', type=int, help='Day number')
    parser.add_argument('--title', help='Phase title')
    parser.add_argument('--summary', help='Phase summary')
    parser.add_argument('--status', choices=['pending', 'in-progress', 'completed'], help='Status')
    parser.add_argument('--content', help='JSON content for sections array (escaped string)')
    parser.add_argument('--reflection', help='JSON reflection(s) array')
    parser.add_argument('--payload', help='Full JSON payload for complex updates')

    args = parser.parse_args()

    if args.payload:
        payload = json.loads(args.payload)
        return update_day(**payload)

    sections = json.loads(args.content) if args.content else None
    reflections = json.loads(args.reflection) if args.reflection else None

    update_day(
        day=args.day,
        title=args.title,
        summary=args.summary,
        sections=sections,
        reflections=reflections,
        status=args.status
    )


if __name__ == '__main__':
    main()
