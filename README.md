# LMS App

A Learning Management System built with FastAPI on the backend and Vue 3 on the frontend. It handles user/course management and can serve SCORM 1.2 packages — including full runtime tracking (progress, resume, quiz interactions, scores).

---

## What it does

Three types of users exist:

- **Admin** — manages users, creates courses, uploads SCORM ZIPs, assigns courses to learners, publishes content
- **Instructor** — same as admin for everything course-related, just can't manage users
- **Learner** — sees their assigned courses, plays SCORM content, picks up where they left off

SCORM is basically a zipped e-learning module (slides, quizzes, videos) that follows a standard API. The LMS uploads the ZIP, extracts it, serves the files, and uses a JavaScript runtime to track what the learner does inside.

---

## Stack

| | |
|--|--|
| Backend | FastAPI (Python) |
| Database | MySQL (XAMPP works fine locally) |
| ORM + migrations | SQLAlchemy + Alembic |
| Auth | JWT (python-jose + bcrypt) |
| Frontend | Vue 3 with Composition API (`<script setup>`) |
| Styling | Tailwind CSS |
| HTTP | Native fetch with a custom wrapper |

---

## Getting it running

### You'll need

- Python 3.10+
- Node 18+
- MySQL running locally — XAMPP is easiest
- A database called `lms_db` already created

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Backend setup

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and fill in your MySQL password:

```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/lms_db
SECRET_KEY=anything-long-and-random
```

Then install and migrate:

```bash
py -m pip install -r requirements.txt
py -m alembic upgrade head
```

Start it:

```bash
py -m uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. On first startup it seeds a default admin user:

```
Email:    admin@lms.com
Password: Admin@123
```

### Frontend setup

```bash
cd vue-lms
npm install
npm run dev
```

UI runs at `http://localhost:5173`.

---

## Project structure

```
lms_app/
├── backend/
│   ├── .env                   ← your local secrets (not committed)
│   ├── .env.example           ← copy this to .env
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrate.ps1            ← PowerShell shortcut for Alembic commands
│   │
│   ├── alembic/versions/
│   │   └── 20250417_0001_scorm_full_runtime_schema.py
│   │
│   └── app/
│       ├── main.py            ← entry point, CORS, route registration, static files
│       ├── config.py          ← reads .env (nothing else touches os.environ)
│       ├── database.py        ← engine, session, Base, get_db()
│       ├── models.py          ← all SQLAlchemy table definitions
│       ├── schemas.py         ← Pydantic request/response shapes
│       ├── security.py        ← JWT, bcrypt, get_current_user, require_roles()
│       ├── seed.py            ← creates default roles + admin on startup
│       ├── response.py        ← success_response() / error_response() helpers
│       └── routes/
│           ├── auth.py        ← /api/auth
│           ├── users.py       ← /api/users
│           ├── courses.py     ← /api/courses
│           └── scorm.py       ← /api/scorm (3-layer: launch, save, reporting)
│
└── vue-lms/src/
    ├── main.js
    ├── App.vue                ← restores session, validates token on mount
    ├── router.js              ← all routes + beforeEach auth/role guard
    │
    ├── api/
    │   ├── httpClient.js      ← fetch wrapper: adds auth header, handles 401
    │   └── api.js             ← get/post/put/patch/remove/postForm
    │
    ├── stores/roleStore.js    ← reactive user/role state, persisted to localStorage
    ├── composables/useAccess.js
    │
    └── modules/
        ├── auth/
        ├── users/
        └── courses/
            ├── service.js              ← all course + SCORM API calls
            ├── scorm/
            │   ├── scorm12FullApi.js   ← full SCORM 1.2 runtime (window.API)
            │   └── scorm12LmsApi.js    ← lightweight stub, kept as reference
            └── views/
                ├── Courses.vue                ← routes to admin or learner view based on role
                ├── AdminInstructorCourses.vue
                ├── LearnerCourses.vue
                └── CoursePlayer.vue           ← the SCORM player
```

---

## Backend files

**`main.py`** — FastAPI app setup. Registers all routers, adds CORS (so the Vue dev server can talk to it), mounts `/scorm-content` as a static file server for extracted SCORM ZIPs, and runs `seed_database()` on startup.

One thing to know: `Base.metadata.create_all()` is here for convenience, but it won't add columns to existing tables. For any schema change, you need to run `alembic upgrade head`.

**`config.py`** — reads everything from `.env`. All other files import from here instead of hitting `os.environ` directly.

**`database.py`** — engine, `SessionLocal`, `Base`, and the `get_db()` FastAPI dependency.

**`models.py`** — all the tables as SQLAlchemy classes. The important ones for SCORM are `ScormProgress` (one row per learner per course, holds all runtime state) and `ScormInteraction` (one row per quiz interaction).

**`security.py`** — `hash_password`, `verify_password`, `create_access_token`, `get_current_user`, and `require_roles(["Administrator", "Instructor"])`. The last one is a dependency you drop on any route that needs role checking.

**`seed.py`** — runs once on startup. Creates the three roles if they don't exist, creates the default admin user if it doesn't exist.

**`response.py`** — two helpers used everywhere:

```python
success_response(message, data, status_code=200)
# { "success": true, "message": "...", "data": {...} }

error_response(message, status_code=400, error=None)
# { "success": false, "message": "...", "error": {...} }
```

**`routes/courses.py`** — course CRUD, SCORM ZIP upload, assignment. On upload, it parses `imsmanifest.xml` (via `utils/scorm_manifest.py`) to find the launch file and extract runtime metadata like `datafromlms`, `masteryscore`, `maxtimeallowed`, `timelimitaction`.

**`routes/scorm.py`** — the SCORM tracking layer. Split into 3 clear layers — see the SCORM section below.

---

## Frontend files

**`App.vue`** — on mount, checks localStorage for a token and calls `/api/auth/me` to validate it. Either shows the login page or the app.

**`httpClient.js`** — the core fetch wrapper. Auto-attaches `Authorization: Bearer <token>`, handles 401 (clears storage, redirects to login), and unwraps the `{ success, data }` envelope. Also exports `apiUrl(path)` for building full backend URLs.

**`roleStore.js`** — reactive store for `user`, `role`, `availableRoles`. Saved to localStorage so a page refresh doesn't log you out.

**`useAccess.js`** — composable that gives components easy access to the role store:

```js
const { user, role, isAdmin, isLearner, isInstructor, hasRole, setUserData, clearRole } = useAccess()
```

**`CoursePlayer.vue`** — the SCORM player. Fetches the course details and launch state in parallel, then sets everything up in the right order before loading the iframe:

```
window.tl_sco_data = { ...launchState }   ← learner's saved state
window.scormPost   = async fn(data) {}    ← wires LMSCommit/Finish to the backend
installFullScormApi()                     ← window.API = { LMSInitialize, ... }
iframe.src = "..."                        ← course loads last
```

The order matters. Don't move things around here.

**`scorm12FullApi.js`** — the full SCORM 1.2 runtime. Implements all 8 SCORM API functions and the full CMI data model tree. Reads `window.tl_sco_data` lazily (only when `LMSInitialize()` is called, not at import time — more on why below). Calls `window.scormPost(data)` on every commit and finish.

```js
import { installFullScormApi, removeFullScormApi } from '../scorm/scorm12FullApi'

installFullScormApi()   // call before setting iframe.src
removeFullScormApi()    // call in onUnmounted
```

**`scorm12LmsApi.js`** — a simpler module-style SCORM stub kept as a reference. Not used by the main player.

**`LearnerCourses.vue`** — shows the learner's assigned courses with progress bars. Pulls from `/api/courses/me` and `/api/scorm/my-progress` at the same time.

---

## Database tables

### `users` and `roles`

Standard stuff — users have email, bcrypt-hashed password, full name, is_active. A `user_roles` join table links them to roles (many-to-many, though in practice each user has one role).

### `courses`

Holds course metadata plus some SCORM-specific fields populated at upload time:

| Column | What it stores |
|--------|----------------|
| `scorm_launch_relative` | path to the entry HTML file inside the extracted ZIP |
| `scorm_manifest_title` | title from `imsmanifest.xml` |
| `scorm_datafromlms` | `adlcp:datafromlms` — data the LMS sends to the course at launch |
| `scorm_masteryscore` | pass/fail threshold |
| `scorm_maxtimeallowed` | time limit |
| `scorm_timelimitaction` | what happens when time runs out |

### `scorm_progress`

One row per learner per course. This is where all SCORM runtime state lives between sessions.

Key columns:

| Column | Meaning |
|--------|---------|
| `lesson_location` | bookmark — exactly where to resume |
| `suspend_data` | opaque string the SCO saves — stored verbatim, never parsed |
| `lesson_status` | `not attempted` / `incomplete` / `completed` / `passed` / `failed` |
| `score_raw` / `score_min` / `score_max` | scores |
| `total_time` | cumulative time (only updated on LMSFinish) |
| `entry` | `ab-initio` or `resume` |
| `scorm_exit` | how the learner left (`suspend`, `time-out`, `logout`, `""`) |

### `scorm_interactions`

One row per quiz interaction per progress record. Stores the question ID, learner's response, correct answer pattern, result, latency, etc.

---

## API endpoints

All responses follow the same envelope:

```json
{ "success": true,  "message": "...", "data":  { ... } }
{ "success": false, "message": "...", "error": { ... } }
```

### Auth

| Method | Path | Auth required |
|--------|------|--------------|
| POST | `/api/auth/login` | No |
| GET | `/api/auth/me` | Yes |

### Users (Admin only)

| Method | Path |
|--------|------|
| GET | `/api/users` |
| POST | `/api/users` |
| PUT | `/api/users/{id}` |
| DELETE | `/api/users/{id}` |

### Courses

| Method | Path | Who |
|--------|------|-----|
| GET | `/api/courses` | Admin, Instructor |
| GET | `/api/courses/me` | Learner |
| GET | `/api/courses/{id}` | All |
| POST | `/api/courses` | Admin, Instructor |
| PATCH | `/api/courses/{id}` | Admin, Instructor |
| DELETE | `/api/courses/{id}` | Admin, Instructor |
| POST | `/api/courses/{id}/assign` | Admin, Instructor |
| POST | `/api/courses/{id}/scorm/upload` | Admin, Instructor |
| GET | `/api/courses/{id}/launch` | All |

### SCORM

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/scorm/{id}/state` | Returns `tl_sco_data` for the JS runtime |
| POST | `/api/scorm/{id}/commit` | Saves mid-session state (LMSCommit) |
| POST | `/api/scorm/{id}/finish` | Finalizes session (LMSFinish), updates `total_time` |
| GET | `/api/scorm/my-progress` | All-courses summary for the learner dashboard |
| GET | `/api/scorm/{id}/progress-summary` | Detailed progress for one course |

Static SCORM files are served from:
```
GET /scorm-content/{course_id}/{path/to/file}
```

---

## How a SCORM session actually works

Here's the full flow from a learner clicking "Play" to the SCORM content resuming where they left off:

1. `CoursePlayer.vue` mounts and fires two requests in parallel:
   - `GET /api/courses/{id}` — course title, description
   - `GET /api/scorm/{id}/state` — the learner's full saved state

2. The state response looks like:
   ```json
   {
     "student_id": "7",
     "student_name": "Jane Smith",
     "lesson_location": "5",
     "lesson_status": "incomplete",
     "suspend_data": "...",
     "entry": "resume",
     ...
   }
   ```

3. `CoursePlayer` sets `window.tl_sco_data` to this, wires `window.scormPost` to call the backend, then calls `installFullScormApi()` to put the SCORM runtime on `window.API`.

4. Only then does it set `iframe.src`. The iframe loads the SCORM content from the static file server.

5. The SCORM content calls `window.API.LMSInitialize("")`. The runtime reads `window.tl_sco_data`, builds the full CMI tree, and the course sees `lesson_location = "5"` and `entry = "resume"` — so it jumps straight to slide 5.

6. As the learner moves through the content, the course calls `LMSSetValue("cmi.core.lesson_location", "8")` and then `LMSCommit()`. The runtime collects everything and calls `window.scormPost(data)`, which hits `POST /api/scorm/{id}/commit`.

7. When they finish or close, `LMSFinish()` fires — same thing but with `session_time` included, which hits `/finish` instead of `/commit`. The backend adds `session_time` to `total_time` and stamps `completed_at`.

8. Next session: `entry` comes back as `"resume"`, and the course picks up from wherever they left off.

---

## The SCORM 3-layer design

The backend SCORM API is intentionally split into three separate concerns:

**Layer 1 — Launch state (`GET /state`)**: Returns only what the SCORM JS runtime needs. Fields match what `scorm12FullApi.js` expects to read at `LMSInitialize()` time. No dashboard data in here.

**Layer 2 — Save (`POST /commit`, `POST /finish`)**: Accepts raw data from `commitData()` in the JS runtime. Field names from the JS side get mapped to DB columns (e.g., `score` → `score_raw`, `minscore` → `score_min`). `total_time` is only updated on finish, not on every commit.

**Layer 3 — Reporting (`GET /my-progress`, `GET /progress-summary`)**: Returns human-friendly data for dashboards. Completely different shape from the launch state — progress percentages, readable timestamps, status labels, etc.

---

## Why `tl_sco_data` is read lazily

`scorm12FullApi.js` is an ES module, so its top-level code runs immediately at import time. But at import time, the player hasn't fetched the learner's state yet — `window.tl_sco_data` doesn't exist.

The fix: `SCOState = {}` at module level. `initSCOState()` (which actually reads `window.tl_sco_data`) only runs inside `LMSInitialize()`, which is called by the SCORM content — by which point the player has already set everything up.

---

## Database migrations

Alembic handles all schema changes. Run this after pulling any new code:

```bash
cd backend
py -m alembic upgrade head
```

Other useful commands:

```bash
py -m alembic current        # what version is the DB at?
py -m alembic history        # all migrations
py -m alembic downgrade -1   # roll back one step
```

To create a new migration after changing `models.py`:

```bash
py -m alembic revision --autogenerate -m "describe your change"
py -m alembic upgrade head
```

There's also a PowerShell helper if you prefer:

```powershell
.\migrate.ps1                       # apply all pending
.\migrate.ps1 new "add user avatar" # generate new migration
.\migrate.ps1 downgrade -1
.\migrate.ps1 current
.\migrate.ps1 history
```

**Migrations so far:**

| Version | What it does |
|---------|-------------|
| `0001` | Adds SCORM runtime columns to `courses` and `scorm_progress`, widens some column types, creates `scorm_interactions` table |

---

## Role-based access

Backend routes are protected like this:

```python
@router.post("/courses")
def create_course(
    ...,
    current_user: User = Depends(require_roles(["Administrator", "Instructor"]))
):
```

Any role not in the list gets a 403.

On the frontend, `router.js` checks `meta.roles` in `beforeEach`. Components use `useAccess()` to show or hide UI elements:

```vue
<button v-if="isAdmin">Admin only</button>
<div v-if="hasRole(['Administrator', 'Instructor'])">Admin or Instructor</div>
```

What each role can do:

| | Admin | Instructor | Learner |
|--|:--:|:--:|:--:|
| Manage users | ✓ | — | — |
| Create/edit/delete courses | ✓ | ✓ | — |
| Upload SCORM | ✓ | ✓ | — |
| Assign courses | ✓ | ✓ | — |
| View assigned courses | — | — | ✓ |
| Play SCORM | ✓ | ✓ | ✓ |

---

## Environment variables

Copy `backend/.env.example` to `backend/.env` and fill these in:

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `mysql+pymysql://root:pass@127.0.0.1:3306/lms_db` | |
| `SECRET_KEY` | `some-long-random-string` | Change this before going to production |
| `APP_NAME` | `LMS API` | Shows up in `/docs` |
| `DEBUG` | `true` | Includes detailed errors in API responses |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS — add your frontend URL |
| `ADMIN_EMAIL` | `admin@lms.com` | Created on first startup |
| `ADMIN_PASSWORD` | `Admin@123` | |
| `SCORM_STORAGE_PATH` | `storage/scorm` | Where extracted ZIPs go on disk |
| `SCORM_MAX_ZIP_BYTES` | `157286400` | 150 MB default |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |

---

*If you add a new feature, update the relevant section here. If the schema changes, add an Alembic migration.*
