# chat-app reviewer notes

## Architecture

A small Flask monolith defines configuration, SQLAlchemy models, HTTP routes, authentication, and Socket.IO handlers in `app.py`. Jinja2 templates under `templates/` provide the server-rendered UI, while `static/styles.css` contains the global dark theme, responsive styling, and animations. SQLite is stored as `chat.db` beside the application, and real-time messages are persisted as `Message` records before being broadcast to a group room.

## Conventions

- Keep application behavior centralized in `app.py`; the repository currently has no service, repository, migration, or API-layer modules.
- Use Flask-Login for authentication: protected HTTP endpoints apply `@login_required`, and the login redirect target is configured through `login_manager.login_view = 'login'` (`app.py`).
- Normalize credentials and trim user input at route boundaries. Registration and login lowercase emails; profile and registration fields use `.strip()` (`app.py`).
- Store passwords only as Werkzeug hashes through `User.set_password()` and validate with `User.check_password()`; do not add plaintext password persistence (`app.py`).
- Use SQLAlchemy model relationships and integer foreign keys for domain links: `User`, `Group`, `Membership`, and `Message` are all defined in `app.py`.
- Use flash messages plus redirects after form submissions, for example registration, login, profile updates, and group creation (`app.py`).
- Render pages with `render_template()` and pass database objects directly to templates, e.g. `groups.html` receives `groups` and `chat.html` receives `group` and `messages` (`app.py`).
- Socket.IO rooms are named `group_{group_id}`. `send_message` emits `receive_message` to that room, while `join` and `leave` explicitly call `join_room`/`leave_room` (`app.py`).
- Message timestamps sent to the browser use the compact `'%H:%M'` format (`app.py`); preserve this contract when changing the chat client.
- Pin runtime dependencies exactly in `requirements.txt`; Flask, Flask-SocketIO, Flask-SQLAlchemy, and Flask-Login are the core stack.

## Watch out for

- Socket handlers in `app.py` do not enforce authentication or verify group membership. Any change to real-time events should address `current_user`, validate `group_id`, and ensure the sender belongs to the target group.
- `join_group()` and `chat()` create memberships without a database uniqueness constraint or race-safe insertion. Duplicate membership rows are possible under concurrent requests.
- Group creation uses `Group.name` as unique but does not catch `IntegrityError`; duplicate names can produce a server error (`app.py`).
- The app has no visible CSRF protection for POST forms, and `/logout` uses GET. Flag new state-changing routes or security-sensitive form changes that follow this pattern.
- `cors_allowed_origins="*"` (`app.py`) is intentionally broad-looking configuration but is unsafe for a deployed authenticated chat service; avoid widening trust further.
- The fallback `SECRET_KEY='dev-secret-key'` and `debug=True` are development defaults only (`app.py`); they must not be used in production deployments.