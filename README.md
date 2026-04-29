# LMS App — Simple Guide

This is a **Learning Management System (LMS)**. Think of it like an internal company training portal where:
- Admins create courses and upload training content
- Learners log in, see their assigned courses, and complete them
- The system remembers exactly where each learner left off

The training content is packaged in a format called **SCORM** — basically a ZIP file containing slides, videos, or quizzes that follow a standard. The app uploads that ZIP, unpacks it, and plays it right inside the browser.

---

## Who uses this app and what can they do?

There are **3 types of users**:

| Who | What they can do |
|-----|-----------------|
| **Admin** | Everything — manage users, create courses, upload content, assign courses to learners, publish courses |
| **Instructor** | Same as Admin for courses — but cannot manage users |
| **Learner** | Can only see courses assigned to them, open and play them, pick up where they left off |

---

## Tech used

| Part | Technology |
|------|-----------|
| Backend (server) | Python with FastAPI |
| Database | MySQL |
| Database helper | SQLAlchemy (talks to DB) + Alembic (handles DB changes) |
| Login/Auth | JWT tokens + bcrypt password hashing |
| Frontend (UI) | Vue 3 |
| Styling | Tailwind CSS |
| HTTP calls | Native fetch with a custom wrapper |

---

## How to run it locally

### What you need installed first
- Python 3.10 or newer
- Node 18 or newer
- MySQL running — XAMPP is the easiest way on Windows

### Step 1 — Create the database

Open phpMyAdmin (via XAMPP) or MySQL and run:

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2 — Set up the backend

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and fill in your MySQL password:

```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/lms_db
SECRET_KEY=anything-long-and-random
```

Then install Python packages and set up the database tables:

```bash
py -m pip install -r requirements.txt
py -m alembic upgrade head
```

Start the backend server:

```bash
py -m uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`.

On first startup it automatically creates a default admin account:
```
Email:    admin@lms.com
Password: Admin@123
```

### Step 3 — Set up the frontend

```bash
cd vue-lms
npm install
npm run dev
```

The UI is now running at `http://localhost:5173`. Open that in your browser.

---

## Folder structure — what lives where

```
lms_app/
├── backend/          ← Python server (FastAPI)
└── vue-lms/          ← Vue 3 frontend (the UI)
```

---

## Backend folder — explained simply

```
backend/
├── .env                  ← Your secret config (DB password, secret key). Never commit this.
├── .env.example          ← A template — copy this to .env and fill it in
├── requirements.txt      ← List of Python packages to install
├── alembic.ini           ← Config for the database migration tool
├── migrate.ps1           ← PowerShell shortcut for running DB migrations
│
├── alembic/versions/     ← Each file here = one database change
│   └── 0001_scorm_full_runtime_schema.py
│
└── app/                  ← All the actual application code lives here
    ├── main.py
    ├── config.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    ├── security.py
    ├── seed.py
    ├── response.py
    ├── routes/
    │   ├── auth.py
    │   ├── users.py
    │   ├── courses.py
    │   └── scorm.py
    └── utils/
        ├── scorm_manifest.py
        └── scorm_zip.py
```

### What each backend file does

**`main.py`** — The starting point of the whole server. It:
- Registers all the routes (auth, users, courses, scorm)
- Sets up CORS so the Vue frontend can talk to it
- Serves extracted SCORM course files as static files
- Runs the seed function on startup to create default roles + admin

**`config.py`** — Reads all settings from the `.env` file. Every other file imports from here instead of reading environment variables directly. One place, all settings.

**`database.py`** — Sets up the connection to MySQL and provides the `get_db()` function that routes use to get a database session.

**`models.py`** — Defines all the database tables as Python classes. This is the single source of truth for what the database looks like. The tables are:
- `users` — everyone who can log in
- `roles` — Administrator, Instructor, Learner
- `user_roles` — which user has which role
- `courses` — course info + SCORM package details
- `course_assignments` — which learner is assigned to which course
- `scorm_progress` — tracks each learner's progress inside a course
- `scorm_interactions` — stores quiz question responses

**`schemas.py`** — Defines the shape of data coming IN to the API (what fields a request body must have) and going OUT (what the response looks like). Uses Pydantic.

**`security.py`** — Handles all login/auth logic:
- Hashes passwords before saving
- Checks passwords on login
- Creates JWT tokens (the thing stored in the browser after login)
- `get_current_user` — reads the token and returns the logged-in user
- `require_roles(...)` — blocks a route if the user doesn't have the right role

**`seed.py`** — Runs once when the server starts. Creates the three roles (Administrator, Instructor, Learner) and the default admin user if they don't already exist in the database.

**`response.py`** — A tiny helper that makes sure every API response has the same shape:
```json
{ "success": true, "message": "Done", "data": { ... } }
{ "success": false, "message": "Something went wrong", "error": { ... } }
```

---

### Routes — the API endpoints

**`routes/auth.py`** — Login and "who am I" endpoints.
- `POST /api/auth/login` — takes email + password, returns a JWT token
- `GET /api/auth/me` — returns the currently logged-in user's info

**`routes/users.py`** — Admin-only user management.
- List all users, create a user, update a user, delete a user

**`routes/courses.py`** — Everything about courses.
- Create, edit, delete courses
- Upload a SCORM ZIP file to a course
- Assign learners to a course
- Get the launch URL so a learner can open a course

**`routes/scorm.py`** — Tracks what happens while a learner plays a course. Split into 3 clear layers:
- **Layer 1 (Launch)** — `GET /api/scorm/{id}/state` — Returns the learner's saved state so the course can resume where they left off
- **Layer 2 (Save)** — `POST /api/scorm/{id}/commit` and `/finish` — Saves progress while the course is playing
- **Layer 3 (Reporting)** — `GET /api/scorm/my-progress` and `/progress-summary` — Returns progress data for dashboards

---

### Utils — helper tools

**`utils/scorm_zip.py`** — Handles ZIP file safety:
- Checks the file is actually a ZIP (not just renamed)
- Checks it's not too large
- Extracts it safely (prevents a security issue called "zip-slip" where a malicious ZIP could write files outside the intended folder)

**`utils/scorm_manifest.py`** — Reads the `imsmanifest.xml` file inside a SCORM package. This XML file is like a "table of contents" for the course — it says which HTML file to open first, what the course is called, what the pass/fail score threshold is, and how much time is allowed.

---

## Frontend folder — explained simply

```
vue-lms/src/
├── main.js                        ← Starts the Vue app
├── App.vue                        ← Root component, checks if you're logged in on load
├── index.css                      ← Global styles
│
├── api/
│   ├── httpClient.js              ← All HTTP requests go through here
│   └── api.js                     ← Simple get/post/patch/delete helpers
│
├── router/
│   └── index.js                   ← All page routes + login/role protection
│
├── stores/
│   ├── roleStore.js               ← Stores who's logged in (saved to localStorage)
│   └── appStore.js                ← Other global app state
│
├── composables/
│   └── useAccess.js               ← Easy access to "who am I, what's my role"
│
├── config/
│   └── navigation.js              ← Sidebar menu links (changes based on role)
│
├── data/
│   └── appData.js                 ← Static data used across the app
│
├── components/
│   ├── layout/                    ← Layout shell (sidebar, header, page wrapper)
│   │   ├── Layout.vue             ← Main layout wrapper — sidebar + header + content area
│   │   ├── Sidebar.vue            ← Left navigation sidebar
│   │   └── Header.vue             ← Top bar (user info, logout)
│   │
│   ├── dashboard/                 ← Dashboard widgets (cards, charts, quick actions)
│   │   ├── AdminDashboard.vue
│   │   ├── InstructorDashboard.vue
│   │   ├── LearnerDashboard.vue
│   │   ├── OverviewWidget.vue
│   │   ├── CoursesProgressWidget.vue
│   │   ├── UsersWidget.vue
│   │   ├── PortalActivityWidget.vue
│   │   ├── QuickActionsWidget.vue
│   │   └── TimelineWidget.vue
│   │
│   ├── charts/                    ← Chart components
│   │   ├── CoursesDonutChart.vue
│   │   └── PortalActivityChart.vue
│   │
│   ├── common/                    ← Shared reusable UI components
│   │   └── index.js
│   │
│   └── modals/                    ← Shared modal dialogs
│
└── modules/                       ← Feature modules (each feature lives in its own folder)
    ├── auth/
    ├── courses/
    ├── users/
    ├── dashboard/
    ├── reports/
    ├── settings/
    └── misc/
```

### What each frontend file/folder does

**`main.js`** — Creates the Vue app, plugs in the router, and mounts it to the HTML page. Nothing fancy — it's the on-switch.

**`App.vue`** — The very first thing that loads. On startup it checks if there's a saved login token in the browser. If yes, it calls the backend to confirm it's still valid. If valid, shows the app. If not, shows the login page.

**`api/httpClient.js`** — Every single network request in the app goes through this file. It:
- Automatically adds the login token to every request (`Authorization: Bearer ...`)
- If the server says "not logged in" (401), it clears your session and sends you to login
- Unwraps the `{ success, data }` envelope so the rest of the code just gets the data directly
- Also exports `apiUrl(path)` to build the full backend URL

**`api/api.js`** — Thin wrappers on top of httpClient: `get()`, `post()`, `patch()`, `remove()`, `postForm()`. Import these in any file that needs to call the backend.

**`router/index.js`** — Defines every page and its URL. Also runs a check before every page load — if you're not logged in, you get sent to login. If you're the wrong role for that page, you get sent to your dashboard.

**`stores/roleStore.js`** — Stores who's currently logged in (their name, email, role). Saved to `localStorage` so refreshing the page doesn't log you out.

**`stores/appStore.js`** — Other global state shared across the app.

**`composables/useAccess.js`** — A shortcut that any Vue component can use to ask "who am I?":
```js
const { user, role, isAdmin, isLearner, isInstructor } = useAccess()
```
Used to show/hide buttons based on the user's role.

**`config/navigation.js`** — The list of links shown in the sidebar. Different roles see different links — Admins see Users and Reports, Learners only see Courses.

---

### Feature modules — each big feature has its own folder

Every module folder typically has:
- `views/` — the actual pages (Vue components)
- `service.js` — all the API calls for that feature
- `routes.js` — the URL routes for that feature's pages

---

**`modules/auth/`**
- `views/Login.vue` — The login page (email + password form)
- `service.js` — calls `POST /api/auth/login` and `GET /api/auth/me`

**`modules/users/`**
- `views/Users.vue` — Table of all users, create/edit/delete buttons (Admin only)
- `views/Groups.vue` — Groups page (UI stub, not fully implemented yet)
- `service.js` — API calls for user management

**`modules/courses/`** — The biggest module
- `views/Courses.vue` — Smart router: shows Admin view or Learner view depending on your role
- `views/AdminInstructorCourses.vue` — Course management page for Admins/Instructors. Create courses, upload SCORM ZIPs, assign learners, publish
- `views/LearnerCourses.vue` — Course list for learners. Shows progress bars for each course
- `views/CoursePlayer.vue` — The SCORM player. Opens the course in an iframe and manages all the communication between the course content and the backend
- `views/GradingHub.vue` — Grading page (UI stub)
- `views/LearningPaths.vue` — Learning paths page (UI stub)
- `modals/CourseUpsertModal.vue` — The popup form for creating or editing a course
- `modals/CourseAssignModal.vue` — The popup for choosing which learners to assign to a course
- `service.js` — All API calls for courses and SCORM
- `scorm/scorm12FullApi.js` — The full SCORM 1.2 runtime. This is what makes `window.API.LMSInitialize()`, `LMSSetValue()`, `LMSCommit()` etc. work inside the course iframe
- `scorm/scorm12LmsApi.js` — An older simpler SCORM stub, kept for reference. Not used by the player

**`modules/dashboard/`**
- `views/Dashboard.vue` — Loads the right dashboard widget based on your role (Admin, Instructor, or Learner dashboard)

**`modules/reports/`**
- `views/Reports.vue` — Reports page
- `views/Automations.vue` — Automations list page
- `components/AutomationModal.vue` — Modal for creating/editing automations
- `components/AutomationRow.vue` — One row in the automations list

**`modules/settings/`**
- `views/AccountSettings.vue` — User account settings page

**`modules/misc/`**
- `views/StubPage.vue` — A placeholder page shown for features that are linked in the nav but not built yet

---

## Database tables — in plain English

### `users`
Stores every person who can log in — their email, hashed password, full name, and whether their account is active.

### `roles`
Just three rows: `Administrator`, `Instructor`, `Learner`.

### `user_roles`
Links users to roles. One user = one role in practice.

### `courses`
Everything about a course — title, description, category, status (Draft or Published). Also stores info about the uploaded SCORM package: which file to open first, the title from the package, pass/fail score thresholds, time limits.

### `course_assignments`
Records which learner is assigned to which course, when they were assigned, and by who.

### `scorm_progress`
**One row per learner per course.** This is where all progress is saved between sessions:
- `lesson_status` — not attempted / incomplete / completed / passed / failed
- `lesson_location` — like a bookmark, the exact spot where they stopped
- `suspend_data` — a private save-blob the course content uses to remember its own state (the backend stores it but never reads it)
- `score_raw` — their quiz score
- `total_time` — how long they've spent in the course in total
- `progress_percent` — 0%, 50%, or 100% based on status
- `first_access_time` / `last_accessed_time` / `completed_at` — timestamps

### `scorm_interactions`
**One row per question/interaction per learner per course.** When a course has a quiz, each question answer is saved here: the question ID, what the learner answered, whether it was correct, how long they took, and what the right answer was.

---

## All API endpoints at a glance

All responses always look like this:
```json
{ "success": true,  "message": "Done",  "data": { ... } }
{ "success": false, "message": "Error", "error": { ... } }
```

### Login
| Method | URL | Who can use it |
|--------|-----|---------------|
| POST | `/api/auth/login` | Anyone (no login needed) |
| GET | `/api/auth/me` | Logged-in users |

### Users
| Method | URL | Who can use it |
|--------|-----|---------------|
| GET | `/api/users` | Admin only |
| POST | `/api/users` | Admin only |
| PUT | `/api/users/{id}` | Admin only |
| DELETE | `/api/users/{id}` | Admin only |

### Courses
| Method | URL | Who can use it |
|--------|-----|---------------|
| GET | `/api/courses` | Admin, Instructor |
| GET | `/api/courses/me` | Learner |
| GET | `/api/courses/{id}` | Everyone |
| POST | `/api/courses` | Admin, Instructor |
| PATCH | `/api/courses/{id}` | Admin, Instructor |
| DELETE | `/api/courses/{id}` | Admin, Instructor |
| POST | `/api/courses/{id}/assign` | Admin, Instructor |
| POST | `/api/courses/{id}/scorm/upload` | Admin, Instructor |
| GET | `/api/courses/{id}/launch` | Everyone |

### SCORM progress tracking
| Method | URL | What it does |
|--------|-----|-------------|
| GET | `/api/scorm/{id}/state` | Gives the course player the learner's saved state |
| POST | `/api/scorm/{id}/commit` | Saves progress mid-session |
| POST | `/api/scorm/{id}/finish` | Saves final state when the learner exits |
| GET | `/api/scorm/my-progress` | Summary of all courses progress for the learner |
| GET | `/api/scorm/{id}/progress-summary` | Detailed progress for one course |

### Static SCORM files
```
GET /scorm-content/{course_id}/{path/to/file}
```
This is how the browser loads the actual course content (HTML, JS, images inside the ZIP).

---

## How a SCORM course works — step by step

Here's exactly what happens when a learner clicks "Play Course":

**1. The player loads**
`CoursePlayer.vue` opens. It immediately fires two requests at the same time:
- Get the course info (title, description)
- Get the learner's saved progress from the backend

**2. Progress comes back**
The backend checks if this learner has played this course before. If yes, it sends back all their saved data:
```json
{
  "student_name": "Jane Smith",
  "lesson_status": "incomplete",
  "lesson_location": "5",
  "entry": "resume",
  "suspend_data": "..."
}
```
If it's their first time, `entry` is `"ab-initio"` (fresh start) and all values are empty/default.

**3. Setup before the course loads**
The player sets:
- `window.tl_sco_data` = the learner's saved state (so the SCORM runtime can read it)
- `window.scormPost` = a function that sends data to the backend (so the course can save progress)
- Installs `window.API` = the full SCORM 1.2 API (so the course content can call `LMSInitialize`, `LMSSetValue`, etc.)

**4. The course loads**
Only now does the iframe URL get set. The course HTML loads and immediately calls `window.API.LMSInitialize("")`. The runtime reads `window.tl_sco_data`, and since `entry = "resume"` and `lesson_location = "5"`, the course jumps straight to slide 5.

**5. While playing**
Every time the learner moves forward, the course calls `LMSSetValue(...)` to update their position and `LMSCommit()` to save. The runtime collects all the data and sends it to `POST /api/scorm/{id}/commit`. This updates the database row.

**6. When the learner exits**
The course calls `LMSFinish()`. This sends a final save to `POST /api/scorm/{id}/finish`. The backend adds up the total time spent, and if the course is marked as completed/passed/failed, it timestamps that.

**7. Next time they open it**
Steps 1–4 repeat, but this time `entry = "resume"` so they pick up exactly where they left off.

---

## How SCORM upload works — step by step

When an Admin uploads a `.zip` file:

1. **Validate** — check it's actually a ZIP and not too large (default max: 150 MB)
2. **Save the ZIP** to `storage/scorm/{course_id}/package.zip`
3. **Extract** the ZIP safely to `storage/scorm/{course_id}/unpacked/`
4. **Read `imsmanifest.xml`** inside the extracted folder to find:
   - Which HTML file to launch first (the entry point)
   - The course title
   - Pass/fail score threshold (`masteryscore`)
   - Time limit (`maxtimeallowed`)
5. **Save all this info** to the `courses` table in the database
6. The course is now ready to be published and played

---

## Permissions quick reference

| Action | Admin | Instructor | Learner |
|--------|:-----:|:----------:|:-------:|
| Manage users | ✓ | — | — |
| Create / edit / delete courses | ✓ | ✓ | — |
| Upload SCORM packages | ✓ | ✓ | — |
| Assign learners to courses | ✓ | ✓ | — |
| View & play assigned courses | — | — | ✓ |
| Preview any course | ✓ | ✓ | — |

---

## Environment variables (`.env` file)

| Variable | What it's for | Example |
|----------|--------------|---------|
| `DATABASE_URL` | Connection to MySQL | `mysql+pymysql://root:pass@127.0.0.1:3306/lms_db` |
| `SECRET_KEY` | Used to sign JWT tokens — keep this secret | Any long random string |
| `APP_NAME` | Shows in the API docs page | `LMS API` |
| `DEBUG` | Shows detailed error messages in API responses | `true` |
| `ALLOWED_ORIGINS` | Which frontend URLs can talk to the backend (CORS) | `http://localhost:5173` |
| `ADMIN_EMAIL` | Default admin created on first startup | `admin@lms.com` |
| `ADMIN_PASSWORD` | Default admin password | `Admin@123` |
| `SCORM_STORAGE_PATH` | Where uploaded SCORM ZIPs are stored on disk | `storage/scorm` |
| `SCORM_MAX_ZIP_BYTES` | Max upload size in bytes | `157286400` (= 150 MB) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long login stays valid | `1440` (= 24 hours) |

---

## Database migrations (making changes to the database)

When you need to add/change/remove a database column, you don't edit the database manually. You use Alembic — it tracks changes and applies them safely.

**Apply all pending changes** (run this after pulling new code):
```bash
cd backend
py -m alembic upgrade head
```

**Other useful commands:**
```bash
py -m alembic current        # see what version the DB is on
py -m alembic history        # see all migrations ever made
py -m alembic downgrade -1   # undo the last migration
```

**After you change `models.py`**, create a new migration automatically:
```bash
py -m alembic revision --autogenerate -m "describe what you changed"
py -m alembic upgrade head
```

**PowerShell shortcut (Windows):**
```powershell
.\migrate.ps1                        # apply all pending migrations
.\migrate.ps1 new "add user avatar"  # generate new migration file
.\migrate.ps1 downgrade -1           # undo last migration
.\migrate.ps1 current                # check current version
.\migrate.ps1 history                # see all migrations
```

### Migrations so far

| Version | What it changed |
|---------|----------------|
| `0001` | Added all SCORM tracking columns to `courses` and `scorm_progress`, created the `scorm_interactions` table |

---

*When you add a new feature, add a note to the relevant section here. When you change the database schema, create an Alembic migration.*
