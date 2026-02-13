# Phishing Awareness Simulator (Gophish + Python)

This project provides a controlled, training-only CLI tool built on the Gophish framework. It creates mock phishing campaigns in a safe environment, then reports click and open rates to help teams understand social engineering risks and user behavior.

## Safety First

- This tool is for training in controlled environments only.
- You must obtain explicit authorization to run any awareness campaign.
- Sending is disabled by default and requires multiple opt-in steps.

## What This Tool Does

- Validates your Gophish configuration and required resources (group, template, page, SMTP profile).
- Creates a campaign in Gophish or performs a dry-run plan.
- Fetches campaign results and calculates open and click rates.
- Exports per-recipient results to CSV and supports polling updates.

## Project Structure

- `src/` - Python CLI and helper modules.
- `config/` - Example configuration.
- `docs/` - Detailed documentation.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

   The CLI auto-loads `.env` on startup.

3. Update `config/sample_config.yaml` to match your Gophish resources.

4. Run a dry run (default behavior):
   ```bash
   python src/main.py --config config/sample_config.yaml --dry-run
   ```

5. When you are ready, explicitly enable sending:
   - Set `allow_live_send: true` and `dry_run: false` in the config.
   - Pass the confirmation phrase on the CLI.

   ```bash
   python src/main.py --config config/sample_config.yaml --confirm I-UNDERSTAND-THIS-IS-AWARENESS
   ```

6. Fetch metrics:
   ```bash
   python src/main.py --report-only --campaign-id 1 --config config/sample_config.yaml
   ```

7. Export CSV (optional):
   ```bash
   python src/main.py --report-only --campaign-id 1 --csv-out reports/campaign-1.csv --config config/sample_config.yaml
   ```

## Documentation

- See `docs/SETUP.md` for setup and Gophish prerequisites.
- See `docs/USAGE.md` for CLI examples and reporting details.
- See `docs/ETHICS.md` for legal and ethical guidance.

## Notes

- This tool assumes you already have a running Gophish instance.
- All campaign resources referenced by name must exist in Gophish before launching.
- If your Gophish admin UI uses a self-signed certificate, set `verify_tls: false` in the config.
