# TikTok iOS parser

This repository contains the code for parsing TikTok iOS application.

## Relevant Files
- `./TikTok.py`: script to parse TikTok chat messages

## How to run

Requires python3 installed.
Packages: sqlite3, argparse, json, xlsxwriter
Database required: AwemeIM.db, db.sqlite

### TikTok.py
`python tiktok.py -u AwemeIM.db -f db.sqlite -o <output file>`
