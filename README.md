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
10. [SCORM Tracking — How Resume Works](#10-scorm-tracking--how-resume-works)
11. [Role-Based Access](#11-role-based-access)
12. [Environment Variables](#12-environment-variables)

---

## 1. What This App Does

This is a **Learning Management System (LMS)**. It lets:

| Role | What they can do |
|------|-----------------|
| **Administrator** | Create users, create courses, upload SCORM packages, assign courses to learners, publish courses |
| **Instructor** | Same as admin for courses (create, upload, assign) |
| **Learner** | See courses assigned to them, play SCORM content, resume from where they left off |

**SCORM** is a standard format for e-learning content (like an interactive ZIP file with quizzes, videos, slides). This LMS can upload SCORM 1.2 packages, serve them to learners, and track their progress (location, score, completion status).

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | **FastAPI** (Python) |
| Database | **MySQL** (via XAMPP / MySQL Workbench) |
| ORM | **SQLAlchemy** |
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
- Python 3.10+
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

### Step 3 — Install and start the backend
```bash
cd backend
pip install -r requirements.txt
py -m uvicorn app.main:app --reload
```
The API runs at `http://localhost:8000`.  
On first startup it auto-creates all tables and seeds a default admin user.

**Default admin login:**
```
Email:    admin@lms.com
Password: Admin@123
```

### Step 4 — Install and start the frontend
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
│   ├── requirements.txt       ← Python dependencies
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
│           └── scorm.py       ← /api/scorm  (progress tracking & resume)
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
                ├── service.js       ← All course + SCORM API calls
                ├── routes.js        ← Course-specific Vue Router entries
                ├── scorm/
                │   └── scorm12LmsApi.js  ← window.API implementation (SCORM 1.2 runtime)
                ├── views/
                │   ├── Courses.vue              ← Smart router: Admin/Instructor or Learner view
                │   ├── AdminInstructorCourses.vue  ← Admin/Instructor management table
                │   ├── LearnerCourses.vue           ← Learner's "My Assignments" + "My Learning"
                │   └── CoursePlayer.vue             ← SCORM player page with progress + resume
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

### `app/config.py`
Reads all environment variables from `.env` using `python-dotenv`.  
Everything the app needs from the environment comes from here — DB URL, secret key, SCORM storage path, allowed CORS origins, etc.  
**Nothing else in the app reads `os.environ` directly — they all import from `config.py`.**

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
| `Course` | `courses` | Course metadata + SCORM package info |
| `CourseAssignment` | `course_assignments` | Which learner is assigned to which course |
| `ScormProgress` | `scorm_progress` | SCORM runtime state per user per course (for resume) |

### `app/schemas.py`
Defines **Pydantic models** — the shapes of request bodies and response JSON.  
FastAPI uses these to validate incoming data and serialize outgoing data.  
Examples: `LoginRequest`, `CourseCreate`, `CourseResponse`, `UserCreate`.

### `app/security.py`
Handles all **authentication logic**:
- `hash_password(plain)` — hashes a password with bcrypt
- `verify_password(plain, hashed)` — checks a password
- `create_access_token(data)` — creates a signed JWT token
- `decode_access_token(token)` — decodes and validates a JWT
- `get_current_user` — FastAPI dependency: reads the `Authorization` header, decodes the token, returns the logged-in User from DB
- `require_roles(allowed_roles)` — dependency factory: raises 403 if the user's role isn't allowed

### `app/seed.py`
Runs **once on startup** to create:
1. The 3 roles (`Administrator`, `Instructor`, `Learner`) if they don't exist
2. A default admin user (`admin@lms.com` / `Admin@123`) if no admin exists yet

This is safe to run on every restart — it checks before inserting.

### `app/response.py`
Provides two helper functions used by **every route**:
```python
success_response(message, data, status_code=200)
# Returns: { "success": true, "message": "...", "data": {...} }

error_response(message, status_code=400, error=None)
# Returns: { "success": false, "message": "...", "error": {...} }
```
This ensures every API response has the same structure. The frontend can always check `response.success`.

### `app/routes/auth.py`
Two endpoints:
- `POST /api/auth/login` — takes email + password, returns a JWT token + user info
- `GET /api/auth/me` — requires a valid token, returns the logged-in user's profile

### `app/routes/users.py`
CRUD for users (admin only):
- `GET /api/users` — list all users
- `POST /api/users` — create a new user
- `PUT /api/users/{id}` — update a user
- `DELETE /api/users/{id}` — delete a user

### `app/routes/courses.py`
All course-related endpoints:
- `GET /api/courses` — list all courses (admin/instructor)
- `GET /api/courses/me` — list courses assigned to the logged-in learner
- `GET /api/courses/assignable-users` — list users who can be assigned
- `GET /api/courses/{id}` — get one course
- `POST /api/courses` — create a course
- `PATCH /api/courses/{id}` — update a course
- `DELETE /api/courses/{id}` — delete a course
- `POST /api/courses/{id}/assign` — assign learners to a course
- `POST /api/courses/{id}/scorm/upload` — upload and extract a SCORM ZIP file
- `GET /api/courses/{id}/launch` — get the URL to load the SCORM content in an iframe

### `app/routes/scorm.py`
Handles **SCORM progress tracking** (the new feature):
- `GET /api/scorm/my-progress` — returns a map of `{course_id: {lesson_status, progress_percent}}` for the current user. Used by the learner course list to show progress bars.
- `GET /api/scorm/{id}/state` — returns all saved SCORM values for a course. Used by the player to **resume** — it reads `lesson_location`, `suspend_data`, `entry` etc. and pre-loads them into `window.API` before the iframe loads.
- `POST /api/scorm/{id}/commit` — saves SCORM values. Called every time the SCORM content calls `LMSCommit()`.
- `POST /api/scorm/{id}/finish` — finalizes the session. Called when SCORM content calls `LMSFinish()`.

---

## 6. Frontend — File by File

### `src/main.js`
Bootstraps the Vue app: creates the app instance, creates the role store, provides it globally via `app.provide()`, mounts to `#app`.

### `src/App.vue`
The **root component** that wraps everything.
- On mount: reads `access_token` and `userData` from localStorage
- If a token exists, calls `GET /api/auth/me` to restore the session
- Populates the role store with user data + roles
- Shows `<Login>` if not authenticated, or `<RouterView>` if authenticated

### `src/router.js`
Defines all Vue Router routes and has a `beforeEach` guard that:
- Redirects to `/login` if the user is not authenticated
- Redirects to `/` if the user tries to access a route their role doesn't have access to

### `src/api/httpClient.js`
The **core HTTP client**. This is what actually calls `fetch()`.
- Provides `request(path, options, meta)` — the single function all API calls go through
- Has **request interceptors**: automatically adds the `Authorization: Bearer <token>` header and sets `Content-Type: application/json`
- Has **response interceptors**: if a response comes back with HTTP 401 (token expired), it clears localStorage and redirects to `/login` automatically
- Unwraps the backend envelope: if the response has `{ success: true, data: {...} }`, it returns just the `data` part
- Exports `apiUrl(path)` — converts a relative path like `/scorm-content/...` to a full URL like `http://localhost:8000/scorm-content/...`

### `src/api/api.js`
A thin wrapper on top of `httpClient.js` that provides simple named functions:
```js
get(path)                     // GET request
post(path, body)              // POST request with JSON body
put(path, body)               // PUT request
patch(path, body)             // PATCH request
remove(path)                  // DELETE request
postForm(path, formData)      // POST with FormData (for file uploads)
```
All module service files import from here.

### `src/stores/roleStore.js`
A simple **reactive store** (no Vuex/Pinia — just Vue's `reactive()`).
Holds:
- `state.user` — the logged-in user object `{ id, email, full_name }`
- `state.role` — the active role string (`"Administrator"`, `"Learner"`, etc.)
- `state.availableRoles` — all roles the user has
Persists everything to `localStorage` so the session survives a page refresh.

### `src/composables/useAccess.js`
A Vue composable that any component can call to get auth/role state:
```js
const { user, role, isAdmin, isLearner, isInstructor, hasRole, setUserData, clearRole } = useAccess()
```
Components use this instead of importing `roleStore` directly.

### `src/modules/auth/service.js`
Two functions:
- `login(credentials)` — calls `POST /api/auth/login`
- `getMyProfile()` — calls `GET /api/auth/me`

### `src/modules/auth/views/Login.vue`
The login page. Submits email + password, stores the returned token + user data via `setUserData()`, then navigates to `/`.

### `src/modules/users/service.js`
- `fetchUsers()` — calls `GET /api/users`
- `createUser(payload)` — calls `POST /api/users`

### `src/modules/users/views/Users.vue`
Admin-only page. Shows a table of all users with the ability to create new ones.

### `src/modules/courses/service.js`
All course and SCORM API calls. Acts as the **single source of truth** for how course data is fetched and mapped.

Key functions:
| Function | What it does |
|----------|-------------|
| `fetchCoursesAdmin()` | Get all courses (admin/instructor) |
| `fetchMyCoursesLearner()` | Get courses assigned to the current learner |
| `fetchCourse(id)` | Get one course by ID |
| `createCourse(payload)` | Create a new course |
| `updateCourse(id, payload)` | Edit a course |
| `deleteCourse(id)` | Delete a course |
| `assignCourseUsers(id, userIds)` | Assign learners to a course |
| `uploadScormZip(id, file)` | Upload a SCORM ZIP file |
| `fetchLaunchUrl(id)` | Get the URL to load in the SCORM iframe |
| `fetchMyProgress()` | Get progress map for all learner's courses |
| `fetchScormState(id)` | Get saved SCORM state for one course (for resume) |
| `commitScormProgress(id, data)` | Save SCORM values on LMSCommit |
| `finishScormSession(id, data)` | Finalize session on LMSFinish |

The file also has `mapCourse()` — converts the snake_case backend response into camelCase for the frontend.

### `src/modules/courses/routes.js`
Defines which Vue components handle which URL paths for the courses module.
- `/courses` → `Courses.vue` (accessible to all roles)
- `/courses/:courseId/play` → `CoursePlayer.vue`

### `src/modules/courses/views/Courses.vue`
A **smart router component** — it doesn't have its own UI. It just checks the user's role:
- Admin or Instructor → renders `<AdminInstructorCourses>`
- Learner → renders `<LearnerCourses>`

### `src/modules/courses/views/AdminInstructorCourses.vue`
The management table for admins/instructors. Features:
- List of all courses with status, category, SCORM info
- Create course button → opens `CourseUpsertModal`
- Edit icon → opens `CourseUpsertModal` pre-filled
- Delete icon → confirms and deletes
- Assign icon (only enabled for **Published** courses) → opens `CourseAssignModal`
- Upload SCORM button → file input that uploads a ZIP
- Shows snackbar notifications for all actions
- Prevents double-clicking the create button (shows a spinner)

### `src/modules/courses/views/LearnerCourses.vue`
The learner's course page. Features:
- **My Assignments** tab: all courses assigned to this learner, each showing a progress bar + status badge (Not Started / In Progress / Completed)
- **My Learning** tab: only courses the learner has actually started (progress > 0)
- Clicking a row (or the Start/Resume/Review button) navigates to the SCORM player
- Progress data is loaded from `/api/scorm/my-progress` in parallel with the course list

### `src/modules/courses/views/CoursePlayer.vue`
The SCORM player page. This is the most complex page. Layout:
```
[Header: Back button | Course title | Status badge]
[Thin progress bar across full width]
[SCORM iframe (left, main area) | Right aside panel]
                                   [Progress ring with %]
                                   [Course description + tags]
                                   [Lesson list with status icon]
```
How it works:
1. Loads course details + saved SCORM state **in parallel** (`Promise.all`)
2. Pre-loads saved state into `window.API` before the iframe starts loading (enables resume)
3. Hooks `onCommit` → calls `POST /api/scorm/{id}/commit` to save progress
4. Hooks `onFinish` → calls `POST /api/scorm/{id}/finish` to finalize
5. Updates the progress bar and status in real-time as the learner progresses

### `src/modules/courses/scorm/scorm12LmsApi.js`
Implements the **SCORM 1.2 JavaScript API** that the content inside the iframe expects to find on `window.API`.

SCORM content (the iframe) calls functions like:
- `window.API.LMSInitialize()` — start a session
- `window.API.LMSSetValue("cmi.core.lesson_location", "5")` — save where the learner is
- `window.API.LMSGetValue("cmi.core.lesson_status")` — read current status
- `window.API.LMSCommit()` — save all changes (this triggers our `onCommit` callback → API call)
- `window.API.LMSFinish()` — end session (this triggers our `onFinish` callback → API call)

The file exports:
- `createScorm12Api(options)` — creates the API object with optional initial values (for resume)
- `installScorm12Api(options)` — attaches the API to `window.API` and `window.top.API`
- `removeScorm12Api()` — cleans up when leaving the player page

### `src/modules/courses/modals/CourseUpsertModal.vue`
A modal form for creating or editing a course. Fields: title, category, status (Draft/Published), description, SCORM file upload. All fields are required. Shows inline validation errors. Has a loading spinner on submit to prevent double-clicks.

### `src/modules/courses/modals/CourseAssignModal.vue`
A modal for assigning learners to a course. Shows a searchable list of users. Can select multiple. Scrollable with minimum height.

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
| scorm_launch_relative | VARCHAR | Path to the SCORM entry HTML (e.g. `index.html`) |
| scorm_manifest_title | TEXT | Title from imsmanifest.xml |
| scorm_validated_at | DATETIME | When the SCORM ZIP was last uploaded |
| created_at, updated_at | DATETIME | |

### `course_assignments`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| course_id | INT FK | |
| user_id | INT FK | The learner |
| assigned_at | DATETIME | |

### `scorm_progress`
One row per learner per course. Stores all SCORM runtime state.

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | |
| course_id | INT FK | |
| user_id | INT FK | |
| lesson_location | VARCHAR(1024) | Where the learner stopped (SCO-specific format) |
| suspend_data | TEXT | Full arbitrary state saved by the SCO |
| lesson_status | VARCHAR | `not attempted` / `incomplete` / `completed` / `passed` / `failed` |
| score_raw | VARCHAR | Numeric score from the SCO |
| session_time | VARCHAR | Duration of the last session |
| total_time | VARCHAR | Accumulated total time across all sessions |
| progress_percent | INT | 0, 50, or 100 (computed from lesson_status) |
| created_at | DATETIME | |
| last_commit_at | DATETIME | When LMSCommit was last called |
| completed_at | DATETIME | When status reached completed/passed/failed |
| updated_at | DATETIME | |

---

## 8. API Endpoints

All responses use this envelope:
```json
{ "success": true,  "message": "...", "data":  { ... } }
{ "success": false, "message": "...", "error": { ... } }
```

### Auth
| Method | Path | Auth required | Description |
|--------|------|--------------|-------------|
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

### SCORM Progress
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scorm/my-progress` | Map of all course progress for current user |
| GET | `/api/scorm/{id}/state` | Load saved state for resume |
| POST | `/api/scorm/{id}/commit` | Save SCORM values (on LMSCommit) |
| POST | `/api/scorm/{id}/finish` | Finalize session (on LMSFinish) |

### Static SCORM files
```
GET /scorm-content/{course_id}/{any/path/to/file.html}
```
Served directly by FastAPI's `StaticFiles`. The browser loads the SCORM content (HTML, JS, CSS, images) through this URL.

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
   → GET /api/scorm/4/state       (get saved progress for resume)
   Both run in parallel with Promise.all

8. CoursePlayer gets saved state:
   { lesson_location: "5", lesson_status: "incomplete", entry: "resume", ... }

9. GET /api/courses/4/launch
   ← { launch_url: "/scorm-content/4/index.html" }

10. installScorm12Api() is called with the saved state values
    → window.API = { LMSInitialize, LMSSetValue, LMSGetValue, LMSCommit, LMSFinish, ... }
    → window.API already has lesson_location = "5", entry = "resume" pre-loaded

11. iframe src is set to http://localhost:8000/scorm-content/4/index.html
    → Browser loads the SCORM HTML/JS from the backend static server

12. SCORM content JS calls window.API.LMSInitialize()
    → Sees entry = "resume", lesson_location = "5"
    → Jumps the learner straight to slide/page 5 (resume!)

13. As learner progresses, SCORM content calls:
    window.API.LMSSetValue("cmi.core.lesson_location", "8")
    window.API.LMSCommit()
    → Our onCommit callback fires
    → POST /api/scorm/4/commit { lesson_location: "8", ... }
    → DB updated: lesson_location = "8", progress_percent = 50
    → Progress bar updates in real-time on the right panel

14. Learner finishes the course:
    window.API.LMSSetValue("cmi.core.lesson_status", "completed")
    window.API.LMSFinish()
    → Our onFinish callback fires
    → POST /api/scorm/4/finish { lesson_status: "completed", ... }
    → DB updated: progress_percent = 100, completed_at = now
    → Status badge changes to "Completed"

15. Next time the learner opens this course:
    Step 8 returns entry: "ab-initio" replaced by entry: "resume"
    → SCORM content sees it was already completed and shows a summary/review
```

---

## 10. SCORM Tracking — How Resume Works

SCORM 1.2 defines a standard set of data elements the content can read/write through `window.API`. The important ones for tracking are:

| SCORM key | Stored as | Meaning |
|-----------|-----------|---------|
| `cmi.core.lesson_location` | `lesson_location` | A string the SCO uses to know where to resume (e.g. slide number, chapter ID) |
| `cmi.suspend_data` | `suspend_data` | Arbitrary data the SCO saves for full state restoration (can be JSON, a long string, etc.) |
| `cmi.core.lesson_status` | `lesson_status` | `not attempted` / `incomplete` / `completed` / `passed` / `failed` |
| `cmi.core.score.raw` | `score_raw` | Numeric quiz/test score |
| `cmi.core.total_time` | `total_time` | Total time spent across all sessions |
| `cmi.core.entry` | (computed) | `ab-initio` = fresh start, `resume` = continue from where you left off |

**The key insight:** when the player page loads, it fetches the saved state from the DB **before** the iframe loads. It passes these values into `createScorm12Api()` so the CMI data tree is pre-populated. When the SCORM content calls `LMSGetValue("cmi.core.lesson_location")`, it already gets back the saved value — so it knows where to resume.

---

## 11. Role-Based Access

### How roles are enforced on the backend
`security.py` provides `require_roles(["Administrator", "Instructor"])` — a FastAPI dependency. Add it to any route:
```python
@router.post("/courses")
def create_course(
    ...,
    current_user: User = Depends(require_roles(["Administrator", "Instructor"]))
):
```
If the user's role isn't in the list, they get a 403 response.

### How roles are enforced on the frontend
`router.js` has a `beforeEach` guard that checks `meta.roles` on each route against the current user's role. If they don't match, the router redirects.

Components use `useAccess()` to conditionally show/hide UI elements:
```vue
<button v-if="isAdmin">Admin only button</button>
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

## 12. Environment Variables

All configured in `backend/.env`. Copy `backend/.env.example` to get started.

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+pymysql://root:pass@127.0.0.1:3306/lms_db` | MySQL connection string |
| `SECRET_KEY` | `my-super-secret-key-123` | Used to sign JWT tokens. Change this in production! |
| `APP_NAME` | `LMS API` | Shown in FastAPI docs |
| `DEBUG` | `true` | Shows detailed error messages in responses |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS origin for the Vue frontend |
| `ADMIN_EMAIL` | `admin@lms.com` | Default admin user created on first startup |
| `ADMIN_PASSWORD` | `Admin@123` | Default admin password |
| `SCORM_STORAGE_PATH` | `./scorm_storage` | Where extracted SCORM ZIPs are saved on disk |
| `SCORM_MAX_ZIP_BYTES` | `524288000` | Max SCORM ZIP upload size (500 MB default) |

---

*This document covers the full architecture as of the current codebase. When you add a new feature, update the relevant section here.*
