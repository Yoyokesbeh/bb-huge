#!/usr/bin/env python3
"""Simple example: create -> get -> update a Program with logo_url using the REST API.
Environment variables required:
- BB_HUGE_URL (e.g. http://localhost:5000)
- DEV_KEY
- EXAMPLE_LOGO_URL (optional)
"""
import os
import requests
import sys

BB_HUGE_URL = os.environ.get('BB_HUGE_URL', 'http://localhost:5000')
DEV_KEY = os.environ.get('DEV_KEY')
LOGO = os.environ.get('EXAMPLE_LOGO_URL', 'https://via.placeholder.com/128.png')

if not DEV_KEY:
    print('DEV_KEY required in env', file=sys.stderr)
    sys.exit(2)

headers = {'X-Dev-Key': DEV_KEY, 'Content-Type': 'application/json'}

def create_program(name='Example Program', logo=LOGO):
    payload = {'name': name, 'platform': 'private', 'program_url': None, 'logo_url': logo}
    r = requests.post(f"{BB_HUGE_URL}/api/v1/programs", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()

def get_program(pid):
    r = requests.get(f"{BB_HUGE_URL}/api/v1/programs/{pid}", headers=headers)
    r.raise_for_status()
    return r.json()

def update_program(pid, logo):
    r = requests.patch(f"{BB_HUGE_URL}/api/v1/programs/{pid}", json={'logo_url': logo}, headers=headers)
    r.raise_for_status()
    return r.json()

if __name__ == '__main__':
    try:
        p = create_program('bb-huge example program', LOGO)
        print('Created:', p)
        got = get_program(p['id'])
        print('Fetched:', got)
        new_logo = LOGO
        updated = update_program(p['id'], new_logo)
        print('Updated:', updated)
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        sys.exit(1)
