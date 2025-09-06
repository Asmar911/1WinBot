# Run 1WinBot in GitHub Actions

This repo includes a scheduled workflow that runs the bot with action 2 (`-a 2`) on GitHub Actions. It’s configured for near‑continuous operation by running about 5h45m every 6 hours, and uploads logs as an artifact. You can also trigger it manually.

## What it does
- Sets up Python 3.13 and installs `requirements.txt`.
- Creates `.env` from repository secrets.
- Restores Telegram session files from a base64-encoded tar (optional).
- Runs `python main.py -a 2` with a randomized timeout (~340–355 minutes) to stay just under the 6‑hour job limit.
- Uploads the combined console output as `run.log` artifact.

Workflow file: `.github/workflows/run-bot.yml`.

Important: GitHub-hosted runners are ephemeral and each job has a hard 6‑hour cap. “Always on” is approximated by scheduled restarts. For truly 24/7 uninterrupted runtime, use a self‑hosted runner or a VPS/host (Render, Railway, Fly.io, etc.).

## Prerequisites
- Environment file (public-safe):
  - Do not commit `.env` to a public repo. The workflow now always creates `.env` from repository secrets.
  - Add these repository secrets (Settings → Secrets and variables → Actions):
    - `API_ID`: Your Telegram API ID
    - `API_HASH`: Your Telegram API hash
- Sessions archive (recommended):
  - `SESSIONS_TGZ_B64`: Base64 of a tar.gz containing your `sessions/` folder with one or more `*.session` files.
    - Create it locally:
      ```bash
      # from repo root, after you’ve created sessions with action 1 locally
      tar -czf sessions.tgz sessions
      base64 sessions.tgz > sessions.tgz.b64
      # Open sessions.tgz.b64 and copy its content into a new secret named SESSIONS_TGZ_B64
      ```
  - `PROXIES_TXT` (optional): Content for `bot/config/proxies.txt` if you use proxies.
  - `USE_PROXY_FROM_FILE` (optional): Set to `True` if you want to bind proxies from file.

## Schedule and behavior
- Default schedule: starts every 6 hours (`0 */6 * * *`).
- Default duration: randomized between 340–355 minutes (~5h45m) per run.
- Expected behavior: small gaps between runs (minutes) due to queue/boot; if a run ends early, the next scheduled start picks it up.

You can tweak the range by editing inputs `duration_minutes_min` / `duration_minutes_max`, or by providing them when triggering manually. Adjust the cron if you prefer shorter cycles.

## Start it manually
- Go to the repository → Actions → `Run Bot (-a 2)` → Run workflow.
- Optionally set `duration_minutes_min` and `duration_minutes_max` (defaults are 15 and 35).

## View logs
- Actions → select the `Run Bot (-a 2)` workflow run → open the `run-bot` job.
- Expand steps to see live logs (including the output of the Python process).
- The full combined output is also attached as an artifact named `run-log`; download `run.log` from the run page.

### Time-limited runs and exit codes
- The workflow uses `timeout --signal=SIGINT --kill-after=15s` to stop the bot at the planned time.
- If the command hits the time limit, the workflow treats it as a normal, successful stop (not a failure), even if `timeout` would return 124 otherwise.

## Notes
- The bot expects one or more session files in `sessions/`. Without them, `-a 2` will error with “Not found session files”. Use action 1 locally to generate sessions and package them into `SESSIONS_TGZ_B64`.
- Ensure `.env` includes valid `API_ID` and `API_HASH` (either committed or created from secrets). Other settings fall back to defaults in `bot/config/config.py`.
- Runners are ephemeral and public logs are visible to anyone with access to the repo. Avoid printing sensitive data.
