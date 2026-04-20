# LMS App — Complete Architecture Guide

> Everything a new developer needs to understand this project: what it does, how it's structured, what every file is responsible for, and how all the pieces connect.

---

## Table of Contents

1. [What This App Does](#1-what-this-app-does)
2. [Tech Stack](#2-tech-stack)
3. [How to Run the Project](#3-how-to-run-the-project)
4. [Folder Structure (Bird's Eye View)](#4-folders-birds-eye-view)
5. [Backend — File by File](#5-backend--file-by-file)
6. [Frontend — File by File](#6-frontend--file-by-file)
7. [Database Tables](#7-database-tables)
8. [API Endpoints](#8-api-endpoints)
9. [Full Request Flow (Login → Play SCORM)](#9-full-request-flow-login--play-scorm)
10. [SCORM Architecture — 3-Layer Design](#10-scorm-architecture--3-layer-design)
11. [SCORM Tracking — How Resume Works](#11-scorm-tracking--how-resume-works)
12. [Database Migrations (Alembic)](#12-database-migrations-alembic)
13. [Role-Based Access](#13-role-based-access)
14. [Environment Variables](#14-environment-variables)

---

## 1. What This App Does

This is a **Learning Management System (LMS)**. It lets:

| Role | What they can do |
|------|-----------------|
| **Administrator** | Create users, create courses, upload SCORM packages, assign courses to learners, publish courses |
| **Instructor** | Same as admin for courses (create, upload, assign) |
| **Learner** | See courses assigned to them, play SCORM content, resume from where they left off |

**SCORM** is a standard format for e-learning content (like an interactive ZIP file with quizzes, videos, slides). This LMS can upload SCORM 1.2 packages, serve them to learners, and track their progress (location, score, completion status, quiz interactions).

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | **FastAPI** (Python) |
| Database | **MySQL** (via XAMPP / MySQL Workbench) |
| ORM | **SQLAlchemy** |
| DB Migrations | **Alembic** |
| Auth | **JWT tokens** (python-jose) |
| Password hashing | **bcrypt** |
| Frontend | **Vue 3** (Composition API, `<script setup>`) |
| Styling | **Tailwind CSS** |
| Routing (frontend) | **Vue Router** |
| Icons | **lucide-vue-next** |
| HTTP client | Native `fetch` (custom wrapper) |

---

## 3. How to Run the Project

### Prerequisites
- Python 3.10+ (use `py` launcher on Windows)
- Node.js 18+
- MySQL running locally (XAMPP or MySQL Workbench)
- A database called `lms_db` already created in MySQL

### Step 1 — Create the MySQL database
Open MySQL Workbench and run:
```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2 — Configure the backend environment
```
cd backend
copy .env.example .env
```
Edit `backend/.env` and set your MySQL password:
```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/lms_db
SECRET_KEY=any-long-random-string-here
```

### Step 3 — Install dependencies
```bash
cd backend
py -m pip install -r requirements.txt
```

### Step 4 — Run database migrations
```bash
cd backend
py -m alembic upgrade head
```
This creates all tables and applies all schema changes. **Always run this after pulling new code.**

On first run it creates: `roles`, `users`, `courses`, `course_assignments`, `scorm_progress`, `scorm_interactions`.

### Step 5 — Start the backend
```bash
cd backend
py -m uvicorn app.main:app --reload
```
The API runs at `http://localhost:8000`.  
On first startup it seeds a default admin user.

**Default admin login:**
```
Email:    admin@lms.com
Password: Admin@123
```

### Step 6 — Install and start the frontend
```bash
cd vue-lms
npm install
npm run dev
```
The UI runs at `http://localhost:5173`.

---

## 4. Folders — Bird's Eye View

```
lms_app/
├── README.md                  ← You are here
│
├── backend/                   ← FastAPI Python backend
│   ├── .env                   ← Your local secrets (not committed)
│   ├── .env.example           ← Template for .env
│   ├── requirements.txt       ← Python dependencies (includes alembic)
│   ├── alembic.ini            ← Alembic migration config
│   ├── migrate.ps1            ← PowerShell helper script for running migrations
│   │
│   ├── alembic/               ← Database migration files
│   │   ├── env.py             ← Alembic environment (connects to DB, imports models)
│   │   ├── script.py.mako     ← Template for new migration files
│   │   └── versions/
│   │       └── 20250417_0001_scorm_full_runtime_schema.py  ← SCORM schema migration
│   │
│   └── app/
│       ├── main.py            ← App entry point, middleware, exception handlers
│       ├── config.py          ← Reads environment variables
│       ├── database.py        ← DB engine + session setup
│       ├── models.py          ← All SQLAlchemy table definitions
│       ├── schemas.py         ← All Pydantic request/response shapes
│       ├── security.py        ← JWT, password hashing, auth helpers
│       ├── seed.py            ← Creates default roles + admin user on startup
│       ├── response.py        ← Unified success/error JSON response helpers
│       └── routes/
│           ├── auth.py        ← /api/auth  (login, get profile)
│           ├── users.py       ← /api/users (CRUD)
│           ├── courses.py     ← /api/courses (CRUD, SCORM upload, launch)
│           └── scorm.py       ← /api/scorm  (3-layer: launch state, save, reporting)
│
└── vue-lms/                   ← Vue 3 frontend
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.js            ← Vue app bootstrap
        ├── App.vue            ← Root component, handles auth, role store init
        ├── router.js          ← All Vue Router route definitions
        │
        ├── api/
        │   ├── httpClient.js  ← Core fetch wrapper with interceptors
        │   └── api.js         ← get/post/put/patch/remove/postForm helpers
        │
        ├── composables/
        │   └── useAccess.js   ← Composable: isAdmin, isLearner, user, setUserData
        │
        ├── stores/
        │   └── roleStore.js   ← Reactive user/role state + localStorage persistence
        │
        └── modules/
            ├── auth/
            │   ├── service.js       ← login(), getMyProfile()
            │   └── views/
            │       └── Login.vue
            │
            ├── users/
            │   ├── service.js       ← fetchUsers(), createUser()
            │   └── views/
            │       └── Users.vue
            │
            └── courses/
                ├── service.js       ← All course + SCORM API calls (3-layer)
                ├── routes.js        ← Course-specific Vue Router entries
                ├── scorm/
                │   ├── scorm12FullApi.js  ← Full SCORM 1.2 runtime (window.API implementation)
                │   └── scorm12LmsApi.js   ← Lightweight module-style SCORM stub (legacy/reference)
                ├── views/
                │   ├── Courses.vue                ← Smart router: Admin/Instructor or Learner view
                │   ├── AdminInstructorCourses.vue ← Admin/Instructor management table
                │   ├── LearnerCourses.vue          ← Learner's assignments + learning tabs
                │   └── CoursePlayer.vue            ← SCORM player with tl_sco_data + scormPost wiring
                └── modals/
                    ├── CourseUpsertModal.vue    ← Create / Edit course form
                    └── CourseAssignModal.vue    ← Assign learners to a course
```

---

## 5. Backend — File by File

### `app/main.py`
The **entry point** of the FastAPI application.
- Creates the FastAPI app instance
- Adds CORS middleware (allows the Vue frontend to call the API)
- Registers all route groups (`/api/auth`, `/api/users`, `/api/courses`, `/api/scorm`)
- Mounts `/scorm-content` as a static file server (serves extracted SCORM ZIPs)
- Registers global exception handlers so every error returns the same JSON shape
- On startup: calls `seed_database()` to create roles + default admin

> **Note:** `Base.metadata.create_all()` is called here for new tables, but column changes to existing tables require running `alembic upgrade head`.

### `app/config.py`
Reads all environment variables from `.env` using `python-dotenv`.  
Everything the app needs from the environment comes from here.  
**Nothing else in the app reads `os.environ` directly.**

### `app/database.py`
Sets up the SQLAlchemy database connection.
- Creates the `engine` (connection to MySQL)
- Creates `SessionLocal` — a factory for database sessions
- Creates `Base` — all SQLAlchemy models inherit from this
- Provides `get_db()` — a FastAPI dependency that opens/closes a DB session per request

### `app/models.py`
Defines every **database table** as a Python class.

| Class | Table | Purpose |
|-------|-------|---------|
| `Role` | `roles` | The 3 roles: Administrator, Instructor, Learner |
| `User` | `users` | All users with email, hashed password, name |
| `Course` | `courses` | Course metadata + SCORM package info + manifest runtime metadata |
| `CourseAssignment` | `course_assignments` | Which learner is assigned to which course |
| `ScormProgress` | `scorm_progress` | Full SCORM 1.2 runtime state per user per course |
| `ScormInteraction` | `scorm_interactions` | Individual quiz interactions per session |

### `app/schemas.py`
Defines **Pydantic models** — the shapes of request bodies and response JSON.  
FastAPI uses these to validate incoming data and serialize outgoing data.

### `app/security.py`
Handles all **authentication logic**:
- `hash_password(plain)` — hashes a password with bcrypt
- `verify_password(plain, hashed)` — checks a password
- `create_access_token(data)` — creates a signed JWT token
- `get_current_user` — FastAPI dependency that decodes the JWT and returns the User
- `require_roles(allowed_roles)` — raises 403 if the user's role isn't in the allowed list

### `app/seed.py`
Runs once on startup to create the 3 roles and the default admin user if they don't exist yet.

### `app/response.py`
Provides two helpers used by every route:
```python
success_response(message, data, status_code=200)
# Returns: { "success": true, "message": "...", "data": {...} }

error_response(message, status_code=400, error=None)
# Returns: { "success": false, "message": "...", "error": {...} }
```

### `app/routes/auth.py`
- `POST /api/auth/login` — takes email + password, returns a JWT token + user info
- `GET /api/auth/me` — returns the logged-in user's profile

### `app/routes/users.py`
CRUD for users (admin only):
- `GET /api/users` — list all users
- `POST /api/users` — create a new user
- `PUT /api/users/{id}` — update a user
- `DELETE /api/users/{id}` — delete a user

### `app/routes/courses.py`
All course-related endpoints. Also responsible for:
- Parsing `imsmanifest.xml` on SCORM upload (via `scorm_manifest.py`)
- **Now also extracts and stores SCORM runtime metadata** from the manifest:
  `datafromlms`, `masteryscore`, `maxtimeallowed`, `timelimitaction`

### `app/routes/scorm.py`
The SCORM tracking layer — redesigned into **3 clearly separated layers**. See [Section 10](#10-scorm-architecture--3-layer-design) for full details.

| Layer | Endpoint | Purpose |
|-------|----------|---------|
| Launch/Resume | `GET /api/scorm/{id}/state` | Returns `tl_sco_data` for the JS runtime |
| Save | `POST /api/scorm/{id}/commit` | Persists mid-session SCORM data |
| Save | `POST /api/scorm/{id}/finish` | Finalizes session, sets completed_at |
| Reporting | `GET /api/scorm/my-progress` | All-courses summary for dashboard |
| Reporting | `GET /api/scorm/{id}/progress-summary` | One-course detailed report |

### `app/utils/scorm_manifest.py`
Parses `imsmanifest.xml` to find the SCORM launch file. **Now also extracts runtime metadata:**
- `datafromlms` (`adlcp:datafromlms`) — data the LMS sends to the course at launch
- `masteryscore` — pass/fail threshold
- `maxtimeallowed` — time limit
- `timelimitaction` — what to do when time runs out

### `app/utils/scorm_zip.py`
Safely extracts SCORM ZIP files to disk, with security checks to prevent path traversal.

---

## 6. Frontend — File by File

### `src/main.js`
Bootstraps the Vue app: creates the app, creates the role store, provides it globally, mounts to `#app`.

### `src/App.vue`
The root component. On mount: restores session from localStorage, calls `/api/auth/me` to validate the token, populates the role store. Shows `<Login>` or `<RouterView>`.

### `src/router.js`
All Vue Router routes with a `beforeEach` guard for auth + role checks.

### `src/api/httpClient.js`
The core HTTP client:
- Auto-adds `Authorization: Bearer <token>` header
- On 401: clears localStorage, redirects to `/login`
- Unwraps the `{ success, data }` envelope
- Exports `apiUrl(path)` for building full URLs

### `src/api/api.js`
Thin wrappers: `get()`, `post()`, `put()`, `patch()`, `remove()`, `postForm()`.

### `src/stores/roleStore.js`
Reactive store holding `user`, `role`, `availableRoles` — persisted to localStorage.

### `src/composables/useAccess.js`
Composable for components:
```js
const { user, role, isAdmin, isLearner, isInstructor, hasRole, setUserData, clearRole } = useAccess()
```

### `src/modules/courses/service.js`
All course and SCORM API calls. Organized into 3 SCORM layers:

**Layer 1 — Launch/Resume:**
| Function | What it does |
|----------|-------------|
| `fetchScormState(courseId)` | Returns `tl_sco_data` shape from `GET /api/scorm/{id}/state` |

**Layer 2 — Save:**
| Function | What it does |
|----------|-------------|
| `commitScormProgress(courseId, payload)` | Saves mid-session data via `POST /commit` |
| `finishScormSession(courseId, payload)` | Finalizes session via `POST /finish` |

**Layer 3 — Reporting:**
| Function | What it does |
|----------|-------------|
| `fetchMyProgress()` | All-courses summary for the learner dashboard |
| `fetchProgressSummary(courseId)` | One-course detail report for the player/reporting UI |

**Course functions:**
| Function | What it does |
|----------|-------------|
| `fetchCoursesAdmin()` | All courses (admin/instructor) |
| `fetchMyCoursesLearner()` | My assigned courses (learner) |
| `fetchCourse(id)` | Single course |
| `createCourse(payload)` | Create |
| `updateCourse(id, payload)` | Edit |
| `deleteCourse(id)` | Delete |
| `assignCourseUsers(id, userIds)` | Assign learners |
| `uploadScormZip(id, file)` | Upload ZIP |
| `fetchLaunchUrl(id)` | Get SCORM iframe URL |

### `src/modules/courses/views/CoursePlayer.vue`
The SCORM player page. Fully redesigned to work with `scorm12FullApi.js`.

**How it works:**
1. Fetch course details + SCORM launch state in parallel (`Promise.all`)
2. Set `window.tl_sco_data` — the full learner state object the JS runtime reads
3. Set `window.scormPost` — the function `scorm12FullApi.js` calls on every commit/finish
4. Call `installFullScormApi()` — sets `window.API` so the SCORM course can find the runtime
5. Set `iframe.src` — course loads, calls `LMSInitialize()`, reads from `window.tl_sco_data`

**Loading order (critical — must be in this sequence):**
```
window.tl_sco_data = { ...launchState }   ← set learner data
window.scormPost   = async fn(data) {}    ← wires commit/finish to backend
window.API         = installFullScormApi() ← SCORM course finds the LMS runtime
iframe.src = "..."                         ← course loads last
```

### `src/modules/courses/scorm/scorm12FullApi.js`
The **full SCORM 1.2 LMS runtime**. This is the source of truth for all SCORM interaction.

**Key design points:**
- Reads `window.tl_sco_data` **lazily** — only when `LMSInitialize()` is called (not at import time)
- Calls `window.scormPost(data)` on every `LMSCommit()` and `LMSFinish()`
- Implements all 8 required SCORM 1.2 API functions
- Implements the full CMI data model tree (core, score, suspend_data, interactions, objectives, etc.)
- Uses a property path resolver instead of `eval()` for navigating `cmi.interactions.0.id` etc.
- Validates data types against SCORM 1.2 spec (CMIDecimal, CMIString255, CMIVocabulary, etc.)

**Exported functions (the only two things CoursePlayer.vue needs):**
```js
import { installFullScormApi, removeFullScormApi } from '../scorm/scorm12FullApi'

installFullScormApi()   // sets window.API + window.top.API
removeFullScormApi()    // cleans up on component unmount
```

### `src/modules/courses/scorm/scorm12LmsApi.js`
A lightweight **module-style stub** of the SCORM 1.2 API. Used as a reference implementation and for simpler embed scenarios where the full runtime is not needed. Exports `createScorm12Api()`, `installScorm12Api()`, `removeScorm12Api()`.

### `src/modules/courses/views/AdminInstructorCourses.vue`
Admin/Instructor course management: list, create, edit, delete, SCORM upload, assign learners.

### `src/modules/courses/views/LearnerCourses.vue`
Learner's course page with "My Assignments" and "My Learning" tabs. Shows progress bars and status badges loaded from `/api/scorm/my-progress`.

### `src/modules/courses/modals/CourseUpsertModal.vue`
Create/edit course form modal.

### `src/modules/courses/modals/CourseAssignModal.vue`
Assign learners modal with searchable multi-select.

---

## 7. Database Tables

### `roles`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| name | VARCHAR | "Administrator", "Instructor", "Learner" |

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| email | VARCHAR UNIQUE | Login email |
| hashed_password | VARCHAR | bcrypt hash |
| full_name | VARCHAR | Display name |
| is_active | BOOL | Can the user log in |
| created_at | DATETIME | |

### `user_roles` (join table)
Links users to roles (many-to-many).

### `courses`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| title | VARCHAR | Course name |
| description | TEXT | |
| category | VARCHAR | e.g. "Compliance" |
| status | VARCHAR | "Draft" or "Published" |
| scorm_zip_name | VARCHAR | Original ZIP filename |
| scorm_launch_relative | VARCHAR | Path to the SCORM entry HTML |
| scorm_manifest_title | TEXT | Title from imsmanifest.xml |
| scorm_validated_at | DATETIME | When the SCORM ZIP was last uploaded |
| **scorm_datafromlms** | TEXT | `adlcp:datafromlms` from manifest — sent to JS runtime |
| **scorm_masteryscore** | VARCHAR(16) | Pass/fail threshold from manifest |
| **scorm_maxtimeallowed** | VARCHAR(32) | Time limit from manifest |
| **scorm_timelimitaction** | VARCHAR(64) | Time limit action from manifest |
| created_at, updated_at | DATETIME | |

> **Bold** = new columns added in migration `0001`.

### `course_assignments`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| course_id | INT FK | |
| user_id | INT FK | The learner |
| assigned_at | DATETIME | |

### `scorm_progress`
One row per learner per course. Stores all raw SCORM 1.2 runtime state.

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| course_id | INT FK | |
| user_id | INT FK | |
| lesson_location | TEXT | SCO bookmark — stored verbatim, never parsed |
| suspend_data | TEXT | Opaque SCO save string — never parsed |
| lesson_status | VARCHAR(32) | `not attempted` / `incomplete` / `completed` / `passed` / `failed` |
| score_raw | VARCHAR(16) | JS field: `score` |
| **score_min** | VARCHAR(16) | JS field: `minscore` |
| **score_max** | VARCHAR(16) | JS field: `maxscore` |
| total_time | VARCHAR(32) | Accumulated total time (updated on finish only) |
| session_time | VARCHAR(32) | Duration of last session |
| **entry** | VARCHAR(16) | `ab-initio` or `resume` |
| **lesson_mode** | VARCHAR(16) | `normal` / `browse` / `review` |
| **scorm_exit** | VARCHAR(16) | How the learner exited: `suspend` / `time-out` / `logout` / `""` |
| **credit** | VARCHAR(16) | `credit` or `no-credit` |
| **comments** | TEXT | Learner comments to LMS |
| **comments_from_lms** | TEXT | LMS comments shown to learner |
| progress_percent | INT | 0 / 50 / 100 — computed from lesson_status |
| **first_access_time** | DATETIME | When learner first opened the course |
| **last_accessed_time** | DATETIME | Last commit or finish |
| last_commit_at | DATETIME | When LMSCommit was last called |
| completed_at | DATETIME | When status reached completed/passed/failed |
| created_at, updated_at | DATETIME | |

> **Bold** = new columns added in migration `0001`.

### `scorm_interactions` _(new table)_
One row per quiz interaction per progress record.

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| progress_id | INT FK | Links to scorm_progress |
| interaction_index | INT | Position in the interactions array (0-based) |
| interaction_id | VARCHAR(255) | `cmi.interactions.n.id` |
| interaction_time | VARCHAR(32) | Time of interaction (HH:MM:SS) |
| interaction_type | VARCHAR(32) | `true-false` / `choice` / `fill-in` / etc. |
| weighting | VARCHAR(16) | Score weight |
| student_response | TEXT | Learner's answer |
| result | VARCHAR(32) | `correct` / `wrong` / `neutral` / etc. |
| latency | VARCHAR(32) | Time taken to answer |
| correct_responses_json | TEXT | JSON array: `[{ "pattern": "..." }]` |
| created_at, updated_at | DATETIME | |

---

## 8. API Endpoints

All responses use this envelope:
```json
{ "success": true,  "message": "...", "data":  { ... } }
{ "success": false, "message": "...", "error": { ... } }
```

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | No | Login, get JWT token |
| GET | `/api/auth/me` | Yes | Get logged-in user profile |

### Users
| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/users` | Admin | List all users |
| POST | `/api/users` | Admin | Create user |
| PUT | `/api/users/{id}` | Admin | Update user |
| DELETE | `/api/users/{id}` | Admin | Delete user |

### Courses
| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/courses` | Admin, Instructor | All courses |
| GET | `/api/courses/me` | Learner | My assigned courses |
| GET | `/api/courses/assignable-users` | Admin, Instructor | Users available to assign |
| GET | `/api/courses/{id}` | All | Single course |
| POST | `/api/courses` | Admin, Instructor | Create course |
| PATCH | `/api/courses/{id}` | Admin, Instructor | Update course |
| DELETE | `/api/courses/{id}` | Admin, Instructor | Delete course |
| POST | `/api/courses/{id}/assign` | Admin, Instructor | Assign learners |
| POST | `/api/courses/{id}/scorm/upload` | Admin, Instructor | Upload SCORM ZIP |
| GET | `/api/courses/{id}/launch` | All | Get SCORM launch URL |

### SCORM — Layer 1: Launch/Resume
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scorm/{id}/state` | Returns `tl_sco_data` for the JS runtime. Contains all fields the SCORM course needs to resume. |

### SCORM — Layer 2: Save
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scorm/{id}/commit` | Save mid-session SCORM state (called on `LMSCommit()`). Does NOT update `total_time`. |
| POST | `/api/scorm/{id}/finish` | Finalize session (called on `LMSFinish()`). Updates `total_time`, stamps `completed_at`. |

### SCORM — Layer 3: Reporting
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scorm/my-progress` | Map of all course progress for current user. Used by the learner dashboard. |
| GET | `/api/scorm/{id}/progress-summary` | Detailed progress report for one course. Returns `course_progress` + `unit_progress`. |

### Static SCORM files
```
GET /scorm-content/{course_id}/{any/path/to/file.html}
```
Served directly by FastAPI's `StaticFiles`. The browser loads SCORM HTML/JS/CSS through this URL.

---

## 9. Full Request Flow (Login → Play SCORM)

Here is exactly what happens from the moment a learner logs in to the moment SCORM content is playing:

```
1. Learner opens browser at http://localhost:5173

2. App.vue checks localStorage for 'access_token'
   → No token: shows Login.vue

3. Learner enters email + password
   → POST /api/auth/login
   ← { success: true, data: { user, roles, access_token } }
   → Token + user saved to localStorage
   → Role store populated
   → Redirect to /courses

4. Courses.vue detects role = "Learner"
   → Renders LearnerCourses.vue

5. LearnerCourses.vue mounts:
   → GET /api/courses/me          (what courses am I assigned to?)
   → GET /api/scorm/my-progress   (what's my progress on each?)
   Both run in parallel with Promise.all
   → Renders course list with progress bars

6. Learner clicks a course row
   → router.push({ name: 'course-player', params: { courseId: 4 } })
   → URL becomes /courses/4/play

7. CoursePlayer.vue mounts:
   → GET /api/courses/4           (get course title, description)
   → GET /api/scorm/4/state       (get full tl_sco_data for the JS runtime)
   Both run in parallel with Promise.all

8. GET /api/scorm/4/state returns:
   {
     student_id: "7",
     student_name: "Jane Smith",
     lesson_location: "5",
     lesson_status: "incomplete",
     suspend_data: "...",
     total_time: "0030:00:00.00",
     entry: "resume",
     datafromlms: "",
     masteryscore: "",
     ...
   }

9. GET /api/courses/4/launch
   ← { launch_url: "/scorm-content/4/unpacked/index.html" }

10. CoursePlayer sets:
    window.tl_sco_data = { ...launchState }  ← learner's saved state
    window.scormPost   = async fn(data) {}   ← wires LMSCommit/Finish to backend
    installFullScormApi()                    ← window.API = { LMSInitialize, ... }

11. iframe src is set to http://localhost:8000/scorm-content/4/unpacked/index.html
    → Browser loads the SCORM HTML/JS from the backend static server

12. SCORM content JS calls window.API.LMSInitialize("")
    → scorm12FullApi.js runs initSCOState() — reads window.tl_sco_data
    → Builds the CMI tree with lesson_location = "5", entry = "resume"
    → Course jumps the learner straight to slide/page 5 (resume!)

13. As learner progresses, SCORM content calls:
    window.API.LMSSetValue("cmi.core.lesson_location", "8")
    window.API.LMSCommit()
    → commitData() fires in scorm12FullApi.js
    → window.scormPost({ lesson_location: "8", score: "", ... }) is called
    → POST /api/scorm/4/commit saves to DB
    → Progress bar updates in real-time on the right panel

14. Learner finishes the course:
    window.API.LMSSetValue("cmi.core.lesson_status", "completed")
    window.API.LMSFinish()
    → commitData("finish") fires
    → window.scormPost({ lesson_status: "completed", session_time: "00:30:00", ... })
    → POST /api/scorm/4/finish
    → DB: progress_percent = 100, completed_at = now, total_time updated
    → Status badge changes to "Completed"

15. Next time the learner opens this course:
    Step 8 returns entry: "resume"
    → SCORM content sees the status and resumes or shows a summary
```

---

## 10. SCORM Architecture — 3-Layer Design

The SCORM system is split into 3 clearly separated layers so that raw SCORM runtime state never gets mixed with business/dashboard data.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — SCORM Launch/Resume                                  │
│  GET /api/scorm/{id}/state                                      │
│                                                                 │
│  Returns tl_sco_data — the exact shape scorm12FullApi.js reads │
│  at LMSInitialize() time. Contains student identity, saved      │
│  progress, and LMS-configured metadata from imsmanifest.xml.   │
│  NO dashboard fields here.                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2 — SCORM Save APIs                                      │
│  POST /api/scorm/{id}/commit                                    │
│  POST /api/scorm/{id}/finish                                    │
│                                                                 │
│  Accept the raw JSON sent by scorm12FullApi.js commitData().   │
│  JS field names are mapped to DB columns:                       │
│    score     → score_raw                                        │
│    minscore  → score_min                                        │
│    maxscore  → score_max                                        │
│    scorm_exit → scorm_exit                                      │
│  suspend_data stored verbatim — never parsed.                   │
│  total_time only updated on finish.                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3 — LMS Reporting                                        │
│  GET /api/scorm/my-progress                                     │
│  GET /api/scorm/{id}/progress-summary                           │
│                                                                 │
│  Return business-friendly data for dashboards and reports.      │
│  progress-summary returns:                                      │
│    course_progress: { total_time_seconds, score, status, ... }  │
│    unit_progress:   { status, score, first/last_access, ... }   │
│  Completely separate shape from the raw launch state.           │
└─────────────────────────────────────────────────────────────────┘
```

### How `scorm12FullApi.js` connects to the backend

```
CoursePlayer.vue
│
├── window.tl_sco_data = { ...launchState }
│     ↑ from GET /api/scorm/{id}/state
│
├── window.scormPost = async (data) => { POST /api/scorm/{id}/commit or /finish }
│     ↑ decides commit vs finish by presence of session_time in payload
│
└── installFullScormApi() → window.API = { LMSInitialize, LMSFinish, ... }
      ↑ from scorm12FullApi.js

scorm12FullApi.js (runs inside the parent frame, accessed by the iframe)
│
├── LMSInitialize()  → initSCOState() reads window.tl_sco_data → buildCmi()
├── LMSSetValue()    → updates cmi + SCOState
├── LMSGetValue()    → reads from cmi
├── LMSCommit()      → commitData("") → window.scormPost(SCOState)
└── LMSFinish()      → commitData("finish") → window.scormPost(SCOState + session_time)
```

### Why `tl_sco_data` is read lazily

`scorm12FullApi.js` is imported as an ES module. ES modules execute top-level code immediately at import time — before `loadPlayer()` has a chance to fetch and set `window.tl_sco_data`.

The fix: `SCOState = {}` at the top of the file. `initSCOState()` is only called inside `LMSInitialize()`, which runs when the SCORM course calls it — by which time `window.tl_sco_data` is already set.

---

## 11. SCORM Tracking — How Resume Works

SCORM 1.2 defines a standard set of data elements. The important ones for tracking are:

| SCORM key | JS payload field | DB column | Meaning |
|-----------|-----------------|-----------|---------|
| `cmi.core.lesson_location` | `lesson_location` | `lesson_location` | Bookmark — where to resume |
| `cmi.suspend_data` | `suspend_data` | `suspend_data` | Arbitrary SCO state string |
| `cmi.core.lesson_status` | `lesson_status` | `lesson_status` | Completion/pass status |
| `cmi.core.score.raw` | `score` | `score_raw` | Numeric score |
| `cmi.core.score.min` | `minscore` | `score_min` | Minimum score |
| `cmi.core.score.max` | `maxscore` | `score_max` | Maximum score |
| `cmi.core.total_time` | `total_time` | `total_time` | Cumulative time (finish only) |
| `cmi.core.session_time` | `session_time` | `session_time` | This session's time |
| `cmi.core.exit` | `scorm_exit` | `scorm_exit` | How learner exited |
| `cmi.core.entry` | `entry` | `entry` | `ab-initio` or `resume` |
| `cmi.interactions.n.*` | `interactions[]` | `scorm_interactions` | Quiz answers |

**The key insight:** `GET /api/scorm/{id}/state` is called before the iframe loads. The response is assigned to `window.tl_sco_data`. When the SCORM course calls `LMSInitialize()`, `scorm12FullApi.js` reads `window.tl_sco_data` and builds the entire CMI tree from it. The course immediately sees `lesson_location`, `suspend_data`, `entry = "resume"` and jumps straight to the right slide.

---

## 12. Database Migrations (Alembic)

This project uses **Alembic** for database schema migrations. All schema changes are tracked as version files in `backend/alembic/versions/`.

### Run all pending migrations
```bash
cd backend
py -m alembic upgrade head
```
**Run this every time you pull new code.**

### Roll back the last migration
```bash
py -m alembic downgrade -1
```

### Check current migration state
```bash
py -m alembic current
```

### See migration history
```bash
py -m alembic history
```

### Auto-generate a new migration after changing `models.py`
```bash
py -m alembic revision --autogenerate -m "describe your change"
py -m alembic upgrade head
```

### Or use the PowerShell helper script
```powershell
cd backend

.\migrate.ps1                        # apply all pending migrations (default)
.\migrate.ps1 new "add user avatar"  # auto-generate a new migration
.\migrate.ps1 downgrade -1           # roll back last migration
.\migrate.ps1 current                # show current state
.\migrate.ps1 history                # show all migrations
```

### Existing migrations

| Version | File | What it does |
|---------|------|-------------|
| `0001` | `20250417_0001_scorm_full_runtime_schema.py` | Adds SCORM runtime columns to `courses` and `scorm_progress`, widens columns, creates `scorm_interactions` table |

---

## 13. Role-Based Access

### Backend enforcement
`security.py` provides `require_roles(["Administrator", "Instructor"])` — a FastAPI dependency:
```python
@router.post("/courses")
def create_course(
    ...,
    current_user: User = Depends(require_roles(["Administrator", "Instructor"]))
):
```
If the user's role isn't in the list, they get HTTP 403.

### Frontend enforcement
`router.js` has a `beforeEach` guard that checks `meta.roles` against the current user's role.

Components use `useAccess()` to conditionally show/hide UI:
```vue
<button v-if="isAdmin">Admin only</button>
<div v-if="hasRole(['Administrator', 'Instructor'])">Admin or Instructor UI</div>
```

### Role summary
| Feature | Admin | Instructor | Learner |
|---------|-------|-----------|---------|
| Create/edit/delete users | ✓ | ✗ | ✗ |
| Create/edit/delete courses | ✓ | ✓ | ✗ |
| Upload SCORM | ✓ | ✓ | ✗ |
| Assign courses | ✓ | ✓ | ✗ |
| View my assigned courses | ✗ | ✗ | ✓ |
| Play SCORM content | ✓ | ✓ | ✓ |
| Track progress | ✓ | ✓ | ✓ |

---

## 14. Environment Variables

All configured in `backend/.env`. Copy `backend/.env.example` to get started.

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+pymysql://root:pass@127.0.0.1:3306/lms_db` | MySQL connection string |
| `SECRET_KEY` | `my-super-secret-key-123` | Used to sign JWT tokens. Change this in production! |
| `APP_NAME` | `LMS API` | Shown in FastAPI docs at `/docs` |
| `DEBUG` | `true` | Shows detailed error messages in API responses |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS origin for the Vue frontend |
| `ADMIN_EMAIL` | `admin@lms.com` | Default admin user created on first startup |
| `ADMIN_PASSWORD` | `Admin@123` | Default admin password |
| `SCORM_STORAGE_PATH` | `storage/scorm` | Where extracted SCORM ZIPs are saved on disk |
| `SCORM_MAX_ZIP_BYTES` | `157286400` | Max SCORM ZIP upload size (150 MB default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | How long a JWT token stays valid (1440 = 24 hours) |

---

*This document covers the full architecture as of the current implementation. When you add a new feature, update the relevant section here and add a new Alembic migration if the schema changes.*
