# Public portfolio demo

This isolated deployment uses the original Django views and templates with synthetic data only. It is read-only, including Django admin, and does not accept document uploads, payments, messages, or registrations. No client database, credentials, or media are imported.

Render configuration:
- Runtime: Python 3.12
- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start: `bash start-demo.sh`
- Environment: `DJANGO_SETTINGS_MODULE=demo_settings` and a newly generated `SECRET_KEY`.
- Entry point: `/demo/`

SQLite is recreated and seeded at startup. Free-host restarts reset all sample data. This is a portfolio demonstration and does not provide durable customer storage. A production deployment needs a persistent database, object storage, configured email/payment providers, and a separate review of application permissions.
