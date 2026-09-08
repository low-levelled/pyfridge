# Computer Science Concepts — pyfridge & Security Research

A running reference of CS concepts that come up across the pyfridge build and security research work. Written in plain language, built question by question.

---

## 1. Package Managers — What is Homebrew?

**Homebrew** is a package manager for macOS. A package manager is a tool that installs, updates, and removes software for you — handling dependencies automatically so you don't have to track down installers manually.

When you run `brew install postgresql@14`, Homebrew:
1. Downloads the PostgreSQL binaries compiled for your Mac
2. Places them in `/opt/homebrew/` (Apple Silicon) or `/usr/local/` (Intel)
3. Registers a background service (LaunchAgent) so PostgreSQL starts automatically when you log in
4. Creates a database role matching your macOS username

**Why it matters here:** Homebrew is how PostgreSQL got onto this machine. It also made the initial connection work without a password by bootstrapping a role named after the logged-in user (`duufi`). That's a Homebrew convention — production installations don't do this.

---

## 2. PostgreSQL Roles and Authentication

### What is a role?
In PostgreSQL, a **role** is the identity that connects to the database. It's equivalent to a user account. Roles can:
- Have a password (or not)
- Be allowed to log in (or just exist as a group)
- Have specific permissions on specific databases and tables

### How you create and control roles
Roles are managed with SQL — not in `schema.sql` but run against the same PostgreSQL instance:

```sql
-- Create a locked-down app role
CREATE ROLE pyfridge_app WITH LOGIN PASSWORD 'secret';

-- Allow it to connect to the database
GRANT CONNECT ON DATABASE pyfridge TO pyfridge_app;

-- Allow it to read/write tables, but not drop them
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO pyfridge_app;
```

In production you'd have:
- An **admin role** — can do everything (migrations, drops, schema changes)
- An **app role** — can only read and write data; cannot destroy structure

Each gets its own credentials stored in `.env`.

### When does the username/password actually come into play?
Every time the Python code calls `psycopg2.connect()` — which happens on every `pyfridge` command — PostgreSQL runs an auth check before any SQL executes:

```
pyfridge inventory
    → db.py calls psycopg2.connect(user="duufi", dbname="pyfridge")
    → PostgreSQL: does role "duufi" exist? ✓
    → PostgreSQL: does "duufi" have access to "pyfridge"? ✓
    → connection opens → query runs → data returned
```

If the role doesn't exist, you get a `FATAL: role does not exist` error before a single line of SQL runs. That was the first error hit when the `.env` had `DB_USER=postgres`.

---

## 3. Peer Authentication — Why No Password Locally

PostgreSQL's authentication behavior is controlled by a config file called **`pg_hba.conf`** (host-based authentication). It defines: who can connect, from where, and how they prove identity.

On a Homebrew Mac install, `pg_hba.conf` is set to **peer/trust** for local connections. This means:

1. You're connecting from `localhost` (not a remote server)
2. The OS reports your process is running as user `duufi`
3. PostgreSQL has a role named `duufi`
4. Names match → connection allowed, no password required

This is specific to PostgreSQL — MySQL and most other databases don't work this way. It's a deliberate feature for developer convenience on local machines.

**The chain:**
```
pg_hba.conf → "trust local connections"
OS          → "this process is running as duufi"
PostgreSQL  → "role duufi exists"
Result      → connected, no password asked
```

On a real production server, `pg_hba.conf` requires passwords (or certificates) for all connections, and the app role credentials live in the `.env`.

---

## 4. Environment Files — What is `.env`?

A `.env` file is a plain text file that stores **environment-specific configuration** — values that differ between machines or environments (local, staging, production). It's loaded at runtime so the code never hard-codes credentials.

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pyfridge
DB_USER=duufi
DB_PASSWORD=
```

**Why it never goes to git:**
`.env` is listed in `.gitignore`. If credentials were committed, anyone with repo access — or anyone who found the repo public — would have your database password. The `.env.example` file goes to git instead: it documents what variables are needed with placeholder values, so anyone cloning the repo knows what to fill in.

**How the code reads it:**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

host = os.getenv("DB_HOST", "localhost")  # second arg is the default
```

`os.getenv()` reads from the environment. `load_dotenv()` populates the environment from the `.env` file before the code runs. The default value (`"localhost"`) is a fallback if the variable isn't set at all.

---

## 5. Virtual Environments — What is `.venv`?

A **virtual environment** is an isolated Python installation for a specific project. It has its own copy of `pip` and its own installed packages, separate from the system Python.

```bash
python3 -m venv .venv        # create the venv
source .venv/bin/activate    # activate it (sets PATH to use this Python)
pip install -e ".[dev]"      # install pyfridge + dev dependencies into it
```

**Why it matters:**
Without a venv, packages install globally and version conflicts between projects are common. With a venv, `pyfridge` gets `psycopg2==2.9.x` and another project can use a different version — they don't collide.

The `.venv/` directory is in `.gitignore` because it's large, machine-specific, and reproducible from `pyproject.toml`. Anyone cloning the repo recreates it with `pip install -e .`.

---

## 6. Editable Installs — What does `pip install -e` do?

The `-e` flag stands for **editable**. Instead of copying the package files into `.venv/lib/`, it creates a link back to the source directory.

```bash
pip install -e ".[dev]"
#            ^   ^^^
#            |   install "dev" extras (pytest, etc.)
#            editable mode
```

**The effect:** When you edit `pyfridge/inventory.py`, the change is live immediately — you don't have to reinstall. The installed `pyfridge` command always runs the current code in `~/Downloads/pyfridge/pyfridge/`.

This is standard for active development. When publishing to PyPI, you'd do a normal (non-editable) install.

---

## 7. `pyproject.toml` — The Modern Python Package File

`pyproject.toml` is the single config file that defines a Python package — its name, version, dependencies, entry points, and build system. It replaced the older `setup.py` / `setup.cfg` pattern.

Key sections in pyfridge:

```toml
[project]
name = "pyfridge"
version = "0.1.0"
dependencies = [
    "psycopg2-binary",   # PostgreSQL driver
    "python-dotenv",     # reads .env files
    "tabulate",          # formats tables in terminal output
]

[project.scripts]
pyfridge = "pyfridge.cli:main"  # "pyfridge" command → cli.py main()
```

The `[project.scripts]` line is what makes `pyfridge inventory` work as a terminal command. It maps the command name to the Python function that runs when you call it.

---

## 8. Git Workflow Basics

**What gets committed:**
- Source code (`.py`, `.sql`, `.toml`, `.sh`)
- Templates (`.env.example`)
- Documentation (`README.md`, this file)

**What never gets committed:**
- `.env` (credentials)
- `.venv/` (reproducible, machine-specific)
- `__pycache__/`, `*.pyc` (generated bytecode)
- `dist/`, `build/` (build artifacts)

All of the above are in `.gitignore`.

**The workflow so far:**
```
git add <specific files>          # stage what you want to commit
git commit -m "description"       # snapshot with a message
git push                          # sync to GitHub (remote)
```

Push makes it available on any machine and acts as a backup. The GitHub repo at `github.com/low-levelled/pyfridge` is the source of truth.

---

*This document grows as new concepts come up. Each entry maps to something that came up in actual work — not a textbook, but a field notes record.*
