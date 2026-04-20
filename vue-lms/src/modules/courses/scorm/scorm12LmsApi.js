/**
 * SCORM 1.2 LMS API
 *
 * SCORM courses look for a global "window.API" object with these functions.
 * Without it, the course will show "unable to find LMS API".
 *
 * This file provides that API and keeps all course data in memory.
 * To save progress to a server, use the onSetValue / onCommit / onFinish callbacks.
 */

// ─────────────────────────────────────────────
// Default CMI Data (all the fields a SCORM course might read/write)
// ─────────────────────────────────────────────

function getDefaultCmiData(overrides) {
  // These are all the standard SCORM 1.2 data fields with their default values.
  const defaults = {
    // Core learner info
    'cmi.core._children':
      'student_id,student_name,lesson_location,credit,lesson_status,entry,score,lesson_mode,exit,session_time',
    'cmi.core.student_id': '',
    'cmi.core.student_name': '',

    // Where the learner left off
    'cmi.core.lesson_location': '',

    // Pass/fail/incomplete status
    'cmi.core.lesson_status': 'not attempted',

    // normal, browse, or review
    'cmi.core.lesson_mode': 'normal',

    // credit or no-credit
    'cmi.core.credit': 'credit',

    // "ab-initio" = first time, "resume" = coming back
    'cmi.core.entry': 'ab-initio',

    // How the learner exited last time
    'cmi.core.exit': '',

    // Score fields
    'cmi.core.score._children': 'raw,min,max',
    'cmi.core.score.raw': '',
    'cmi.core.score.min': '',
    'cmi.core.score.max': '',

    // Time tracking
    'cmi.core.session_time': '00:00:00',
    'cmi.core.total_time': '00:00:00',

    // Free-form data the course can save (used to resume progress)
    'cmi.suspend_data': '',

    // Data the LMS sends to the course at launch
    'cmi.launch_data': '',

    // Learner comments
    'cmi.comments': '',
    'cmi.comments_from_lms': '',

    // Objectives and interactions (usually filled dynamically by the course)
    'cmi.objectives._children': '',
    'cmi.interactions._children': '',

    // Student preferences
    'cmi.student_data._children': 'mastery_score,time_limit_action',
    'cmi.student_data.mastery_score': '',
    'cmi.student_data.time_limit_action': '',

    'cmi.student_preference._children': 'audio,language,speed,text',
    'cmi.student_preference.audio': '',
    'cmi.student_preference.language': '',
    'cmi.student_preference.speed': '',
    'cmi.student_preference.text': '',
  }

  // Merge in any values passed by the caller (e.g. to restore saved progress)
  return Object.assign({}, defaults, overrides)
}

// ─────────────────────────────────────────────
// Error Code Lookup
// ─────────────────────────────────────────────

// SCORM requires error codes to be returned as strings.
const ERROR_MESSAGES = {
  '0': 'No error',
  '101': 'General exception – API already initialized',
  '301': 'Not initialized – call LMSInitialize first',
}

function getErrorMessage(code) {
  return ERROR_MESSAGES[String(code)] || 'Unknown error'
}

// ─────────────────────────────────────────────
// Create a SCORM 1.2 API instance
// ─────────────────────────────────────────────

/**
 * Creates a new SCORM 1.2 API object.
 *
 * Options you can pass in:
 *   studentId       – learner's ID
 *   studentName     – learner's display name
 *   lessonStatus    – restored status (e.g. "passed", "incomplete")
 *   lessonLocation  – restored lesson location (bookmark)
 *   suspendData     – restored suspend_data string
 *   totalTime       – restored total time spent
 *   entry           – "ab-initio" (first visit) or "resume"
 *   onInitialize()  – called when the course calls LMSInitialize
 *   onSetValue({ element, value }) – called every time a value is set
 *   onCommit({ cmi })              – called when the course commits data
 *   onFinish({ cmi })              – called when the course finishes
 */
export function createScorm12Api(options = {}) {
  // Set up the CMI data store, optionally restoring saved progress
  const cmi = getDefaultCmiData({
    'cmi.core.student_id': options.studentId || '',
    'cmi.core.student_name': options.studentName || '',
    'cmi.core.lesson_status': options.lessonStatus || 'not attempted',
    'cmi.core.lesson_location': options.lessonLocation || '',
    'cmi.core.entry': options.entry || 'ab-initio',
    'cmi.core.total_time': options.totalTime || '00:00:00',
    'cmi.suspend_data': options.suspendData || '',
  })

  // Track whether the API session has been started
  let isInitialized = false

  // Track the last error code (SCORM requires this)
  let lastError = '0'

  // Helper to set the current error code
  function setError(code) {
    lastError = String(code)
  }

  // ── The actual SCORM API methods ──────────────────────────────

  const api = {

    /**
     * Called by the course to start a session.
     * Must be called before any Get/Set operations.
     */
    LMSInitialize() {
      lastError = '0'

      if (isInitialized) {
        setError('101') // already initialized
        return 'false'
      }

      isInitialized = true

      if (typeof options.onInitialize === 'function') {
        options.onInitialize()
      }

      return 'true'
    },

    /**
     * Called by the course when it is done (user exits or completes).
     */
    LMSFinish() {
      lastError = '0'

      if (!isInitialized) {
        setError('301') // not initialized
        return 'false'
      }

      isInitialized = false

      if (typeof options.onFinish === 'function') {
        options.onFinish({ cmi: { ...cmi } })
      }

      return 'true'
    },

    /**
     * Called by the course to read a data value (e.g. lesson_status, student_name).
     * Returns the value as a string, or "" if not found.
     */
    LMSGetValue(element) {
      lastError = '0'

      if (!element || typeof element !== 'string') {
        setError('301')
        return ''
      }

      // Return the value if it exists, otherwise return empty string
      if (Object.prototype.hasOwnProperty.call(cmi, element)) {
        return String(cmi[element])
      }

      return ''
    },

    /**
     * Called by the course to save a data value (e.g. score, lesson_location).
     * Returns "true" on success, "false" on failure.
     */
    LMSSetValue(element, value) {
      lastError = '0'

      if (!isInitialized) {
        setError('301')
        return 'false'
      }

      if (!element || typeof element !== 'string') {
        setError('301')
        return 'false'
      }

      // Save the value (convert null/undefined to empty string)
      cmi[element] = value != null ? String(value) : ''

      if (typeof options.onSetValue === 'function') {
        options.onSetValue({ element, value: cmi[element] })
      }

      return 'true'
    },

    /**
     * Called by the course to flush/save data to the LMS.
     * In a real LMS this would send data to the server.
     */
    LMSCommit() {
      lastError = '0'

      if (!isInitialized) {
        setError('301')
        return 'false'
      }

      if (typeof options.onCommit === 'function') {
        options.onCommit({ cmi: { ...cmi } })
      }

      return 'true'
    },

    /**
     * Returns the code of the last error that occurred.
     * "0" means no error.
     */
    LMSGetLastError() {
      return lastError
    },

    /**
     * Returns a human-readable description of an error code.
     */
    LMSGetErrorString(errorCode) {
      return getErrorMessage(errorCode != null ? errorCode : lastError)
    },

    /**
     * Returns extra diagnostic info for an error code.
     * We just return the same message as LMSGetErrorString.
     */
    LMSGetDiagnostic(errorCode) {
      return api.LMSGetErrorString(errorCode)
    },
  }

  return api
}

// ─────────────────────────────────────────────
// Install / Remove the API on window
// ─────────────────────────────────────────────

// Keep a reference to the currently installed API so we can remove it later
let currentApi = null

/**
 * Puts the SCORM API on window.API so SCORM courses can find it.
 * Call this before loading the SCORM iframe.
 *
 * @param {object} options – same options as createScorm12Api
 * @returns the API object
 */
export function installScorm12Api(options = {}) {
  // Remove any previously installed API first
  removeScorm12Api()

  // Create a fresh API instance
  currentApi = createScorm12Api(options)

  // SCORM 1.2 courses look for window.API on the parent frame
  window.API = currentApi

  // Some nested courses also check window.top.API (only works same-origin)
  try {
    if (window.top) {
      window.top.API = currentApi
    }
  } catch {
    // Ignore – this fails if the top frame is a different origin
  }

  return currentApi
}

/**
 * Removes the SCORM API from window.API.
 * Call this when you unmount the SCORM player component.
 */
export function removeScorm12Api() {
  if (typeof window === 'undefined') {
    return // not in a browser environment
  }

  // Only remove it if WE were the ones who set it
  if (window.API === currentApi) {
    try {
      delete window.API
    } catch {
      window.API = undefined
    }
  }

  // Also clean up window.top.API if we set that too
  try {
    if (window.top && window.top.API === currentApi) {
      delete window.top.API
    }
  } catch {
    // Ignore cross-origin errors
  }

  currentApi = null
}
