# Privacy Policy — uja-bulletin-filter

This is a personal, non-commercial project built for a single user (the
project's author) to filter their own UJA university bulletin emails.

## What it accesses

This app requests **read-only** access to Gmail
(`gmail.readonly` scope) for one purpose only: to find and read the
daily UJA bulletin email in the author's own inbox.

## What it does with that access

- It reads the subject and body of the bulletin email.
- It never sends, deletes, or modifies any email.
- It never accesses any other email in the inbox beyond the bulletin.
- The extracted content is processed locally/in the project's own
  automation (GitHub Actions) to filter activities and send a summary to
  the author's own Telegram account.

## Data storage and sharing

- No data is sold, shared, or used for advertising.
- No data is stored beyond what's needed to run the daily summary.
- This app is used only by its author, for personal use.

## Contact

Questions about this project: see the repository at
https://github.com/Naviocac/uja-bulletin-filter