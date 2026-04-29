/**
 * SCORM 1.2 Full LMS API  —  Easy-to-read version
 *
 * How the whole thing works (plain English):
 *  1. tl_sco_data  – server sends the learner's saved state when the page loads.
 *  2. SCOState     – we copy that data here; all changes during the session go here.
 *  3. window.API   – SCORM courses look for this object and call its 8 functions.
 *  4. cmi          – the course tree of all readable/writable data fields.
 *  5. LMSCommit / LMSFinish call scormPost() to send SCOState back to the server.
 */

// ─── Debug Logging ────────────────────────────────────────────
// Set to false to silence all console output.

var DEBUG = true;

function log(msg) {
    if (DEBUG) console.log(msg);
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 1 – LEARNER STATE
//  Starts as null. Filled inside LMSInitialize() by reading
//  window.tl_sco_data, which CoursePlayer.vue sets before the
//  SCORM iframe loads.
// ═══════════════════════════════════════════════════════════════

var SCOState = {};  // populated in LMSInitialize() from window.tl_sco_data

function initSCOState() {
    var d = window.tl_sco_data || {};
    SCOState = {
        suspend_data:    d.suspend_data    || '',   // course's free-form save data
        lesson_location: d.lesson_location || '',   // last bookmark
        total_time:      d.total_time      || '0000:00:00.00',
        lesson_status:   d.lesson_status   || 'not attempted',
        datafromlms:     d.datafromlms     || '',   // data from the course manifest
        score:           d.score_raw       || '',   // last raw score
        entry:           d.entry           || 'ab-initio'
    };
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 2 – ERROR SYSTEM
//  SCORM requires specific numeric codes for every type of error.
//  Each LMS function resets the error to '0' before doing anything.
// ═══════════════════════════════════════════════════════════════

// Short one-line descriptions  (returned by LMSGetErrorString)
var ERROR_MESSAGES = {
    '0':   'No Error',
    '101': 'General exception',
    '201': 'Invalid argument error',
    '202': 'Element cannot have children',
    '203': 'Element not an array – cannot have count',
    '301': 'Not initialized',
    '401': 'Not implemented error',
    '402': 'Invalid set value – element is a keyword',
    '403': 'Element is read only',
    '404': 'Element is write only',
    '405': 'Incorrect Data Type'
};

// Longer diagnostic messages  (returned by LMSGetDiagnostic)
var ERROR_DETAILS = {
    '0':   'Successful operation. There were no errors.',
    '101': 'A general fault occurred.',
    '201': 'You cannot set such a value – Invalid argument error.',
    '202': 'This element cannot have children.',
    '203': 'This element is not an array.',
    '301': 'The system has to be initialized first. Call LMSInitialize().',
    '401': 'This property is not implemented.',
    '402': 'You cannot set a value to a keyword element.',
    '403': "You can only read this element's value.",
    '404': "You can only write this element's value.",
    '405': 'The value you provided is the wrong data type for this element.'
};

// Holds the current error code and its detail message.
var currentErrorCode   = '0';
var currentErrorDetail = ERROR_DETAILS['0'];

// Call at the start of every LMS function to clear the previous error.
function resetError() {
    currentErrorCode   = '0';
    currentErrorDetail = ERROR_DETAILS['0'];
}

// Record an error without throwing (used in some edge cases).
function setError(code, detail) {
    currentErrorCode   = String(code);
    currentErrorDetail = detail || ERROR_DETAILS[currentErrorCode] || 'Unknown error';
}

// Throw a SCORM error object — caught by the LMS functions' try/catch blocks.
function throwError(code, detail) {
    throw {
        isScormError: true,
        code:         String(code),
        detail:       detail || ERROR_DETAILS[String(code)] || ''
    };
}

// Called inside every catch block to record the error without crashing the page.
function handleCaughtError(err) {
    if (err && err.isScormError) {
        setError(err.code, err.detail);
        log('SCORM Error ' + err.code + ': ' + err.detail);
    } else {
        throw err; // unexpected JS error — let it surface normally
    }
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 3 – LMS SESSION STATE
//  Tracks whether LMSInitialize has been called.
// ═══════════════════════════════════════════════════════════════

// -1 = not started yet   0 = running   1 = finished
var lmsState = -1;

// Call this at the start of any function that requires the session to be running.
function requireRunning() {
    if (lmsState !== 0) throwError('301');
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 4 – CMI DATA MODEL
//
//  The CMI (Course Management Information) tree is the data store
//  that SCORM courses read/write.  Every leaf node is a plain object
//  with a .get() and a .set() method.
//
//  Rules:
//   • Read-only fields  → set() throws error 403
//   • Write-only fields → get() throws error 404
//   • Keyword fields    → set() throws error 402
// ═══════════════════════════════════════════════════════════════

// Tracks the array index of the interaction currently being accessed.
// Needed when validating student_response and correct_responses patterns.
var currentInteractionIndex = 0;

// The active CMI object (rebuilt fresh on each LMSInitialize call).
var cmi = null;

function buildCmi() {
    return {

        // ── cmi.core ───────────────────────────────────────────
        core: {

            _children: {
                value: 'student_id,student_name,lesson_location,credit,lesson_status,' +
                       'entry,score,total_time,lesson_mode,exit,session_time',
                get: function() { return this.value; },
                set: function() { throwError('402'); }           // keyword – cannot be set
            },

            // Learner's ID – provided by LMS, courses can only read it
            student_id: {
                value: (window.tl_sco_data || {}).student_id || '',
                get: function() { return this.value; },
                set: function() { throwError('403'); }           // read-only
            },

            // Learner's display name – provided by LMS, read-only
            student_name: {
                value: (window.tl_sco_data || {}).student_name || '',
                get: function() { return this.value; },
                set: function() { throwError('403'); }           // read-only
            },

            // Bookmark – where the learner left off in the course
            lesson_location: {
                value: '',
                get: function() {
                    if (SCOState.lesson_location !== undefined) {
                        this.value = SCOState.lesson_location;
                    }
                    return this.value;
                },
                set: function(param) {
                    if (!isValidType(param, 'CMIString255')) throwError('405');
                    this.value = param;
                    SCOState.lesson_location = param;
                    return 'true';
                }
            },

            // Whether this session counts for credit ('credit' or 'no-credit')
            credit: {
                value: 'credit',
                get: function() { return this.value; },
                set: function() { throwError('403'); }           // read-only
            },

            // The learner's completion/pass status
            // Allowed values: passed, completed, failed, incomplete, browsed, not attempted
            lesson_status: {
                value: 'not attempted',
                get: function() {
                    if (SCOState.lesson_status) this.value = SCOState.lesson_status;
                    return this.value;
                },
                set: function(param) {
                    if (!isValidType(param, 'CMIVocabulary', 'Status') || param === 'not attempted') {
                        throwError('405');
                    }
                    this.value = param;
                    SCOState.lesson_status = param;
                    return 'true';
                }
            },

            // First visit = 'ab-initio'  |  returning visit = 'resume'
            entry: {
                value: 'ab-initio',
                get: function() {
                    if (SCOState.entry !== undefined) this.value = SCOState.entry;
                    return this.value;
                },
                set: function() { throwError('403'); }           // read-only
            },

            // Score sub-object  (cmi.core.score.raw / min / max)
            score: {
                _children: {
                    value: 'raw,min,max',
                    get: function() { return this.value; },
                    set: function() { throwError('402'); }
                },
                raw: {
                    value: SCOState.score || '',
                    get: function() { return this.value; },
                    set: function(param) {
                        if (!isValidScoreOrBlank(param)) throwError('405');
                        this.value = param;
                        SCOState.score = param;
                        return 'true';
                    }
                },
                min: {
                    value: '',
                    get: function() { return this.value; },
                    set: function(param) {
                        if (!isValidScoreOrBlank(param)) throwError('405');
                        this.value = param;
                        SCOState.minscore = param;
                        return 'true';
                    }
                },
                max: {
                    value: '',
                    get: function() { return this.value; },
                    set: function(param) {
                        if (!isValidScoreOrBlank(param)) throwError('405');
                        this.value = param;
                        SCOState.maxscore = param;
                        return 'true';
                    }
                }
            },

            // Total time the learner has spent across ALL visits (cumulative, read-only)
            total_time: {
                value: '0000:00:00.00',
                get: function() {
                    if (SCOState.total_time) this.value = SCOState.total_time;
                    return this.value;
                },
                set: function() { throwError('403'); }           // read-only
            },

            // How the content is being used: 'normal', 'browse', or 'review'
            lesson_mode: {
                value: 'normal',
                get: function() {
                    if (SCOState.lesson_mode) this.value = SCOState.lesson_mode;
                    return this.value;
                },
                set: function() { throwError('403'); }           // read-only
            },

            // How the learner exited: 'time-out', 'suspend', 'logout', or ''
            // Write-only – the course tells the LMS how the learner left
            exit: {
                value: '',
                get: function() { throwError('404'); },          // write-only
                set: function(param) {
                    if (!isValidType(param, 'CMIVocabulary', 'Exit')) throwError('405');
                    this.value = param;
                    SCOState.scorm_exit = param;
                    return 'true';
                }
            },

            // Time spent in THIS session only (not cumulative)
            // Write-only – the course sets this just before finishing
            session_time: {
                value: '',
                get: function() { throwError('404'); },          // write-only
                set: function(param) {
                    if (!isValidType(param, 'CMITimespan')) throwError('405');
                    this.value = param;
                    SCOState.session_time = param;
                    return 'true';
                }
            }
        },

        // ── cmi.suspend_data ───────────────────────────────────
        // A free-form string (up to 4096 chars) the course uses to
        // save its own internal state so the learner can resume later.
        suspend_data: {
            value: '',
            get: function() {
                if (SCOState.suspend_data) this.value = SCOState.suspend_data;
                return this.value;
            },
            set: function(param) {
                if (!isValidType(param, 'CMIString4096')) throwError('405');
                this.value = param;
                SCOState.suspend_data = param;
                return 'true';
            }
        },

        // ── cmi.launch_data ────────────────────────────────────
        // Data from the course manifest (adlcp:datafromlms). Read-only.
        launch_data: {
            value: '',
            get: function() {
                if (SCOState.datafromlms) this.value = SCOState.datafromlms;
                return this.value;
            },
            set: function() { throwError('403'); }               // read-only
        },

        // ── cmi.comments ───────────────────────────────────────
        // Comments from the learner to the LMS. Each set() APPENDS.
        comments: {
            value: '',
            get: function() { return this.value; },
            set: function(param) {
                if (!isValidType(param, 'CMIString4096')) throwError('405');
                this.value += param; // appends, does not overwrite
                SCOState.comments = this.value;
                return 'true';
            }
        },

        // ── cmi.comments_from_lms ──────────────────────────────
        // Comments the LMS shows to the learner. Read-only.
        comments_from_lms: {
            value: '',
            get: function() {
                if (SCOState.comments_from_lms) this.value = SCOState.comments_from_lms;
                return this.value;
            },
            set: function() { throwError('403'); }               // read-only
        },

        // ── cmi.student_data ───────────────────────────────────
        // Mastery/time-limit settings set by the LMS. Courses can read but not write.
        student_data: {
            _children: {
                value: 'mastery_score,max_time_allowed,time_limit_action',
                get: function() { return this.value; },
                set: function() { throwError('402'); }
            },
            mastery_score: {
                value: '',
                get: function() {
                    if (SCOState.masteryscore) this.value = SCOState.masteryscore;
                    return this.value;
                },
                set: function() { throwError('403'); }
            },
            max_time_allowed: {
                value: '',
                get: function() {
                    if (SCOState.maxtimeallowed) this.value = SCOState.maxtimeallowed;
                    return this.value;
                },
                set: function() { throwError('403'); }
            },
            time_limit_action: {
                value: '',
                get: function() {
                    if (SCOState.timelimitaction) this.value = SCOState.timelimitaction;
                    return this.value;
                },
                set: function() { throwError('403'); }
            }
        },

        // ── cmi.student_preference ─────────────────────────────
        // Learner's display/audio preferences.
        student_preference: {
            _children: {
                value: 'language,speech,audio,speed,text',
                get: function() { return this.value; },
                set: function() { throwError('402'); }
            },
            audio: {
                value: '',
                get: function() { return this.value; },
                set: function(param) {
                    if (!isValidType(param, 'CMISInteger') || param < -1 || param > 100) throwError('405');
                    this.value = param;
                    return 'true';
                }
            },
            language: {
                value: 'english',
                get: function() { return this.value; },
                set: function(param) {
                    if (!isValidType(param, 'CMIString255')) throwError('405');
                    this.value = param;
                    return 'true';
                }
            },
            speed: {
                value: '0',
                get: function() { return this.value; },
                set: function(param) {
                    if (!isValidType(param, 'CMISInteger') || param < -100 || param > 100) throwError('405');
                    this.value = param;
                    return 'true';
                }
            },
            text: {
                value: '0',
                get: function() { return this.value; },
                set: function(param) {
                    var allowed = (param === '1' || param === '0' || param === '-1');
                    if (!isValidType(param, 'CMISInteger') || !allowed) throwError('405');
                    this.value = param;
                    return 'true';
                }
            }
        },

        // ── cmi.objectives ─────────────────────────────────────
        // Array of learning objectives. New entries are auto-created
        // the first time the course accesses cmi.objectives.0, etc.
        objectives: makeEmptyArray('objectives'),

        // ── cmi.interactions ───────────────────────────────────
        // Array of quiz interactions. New entries are auto-created
        // the first time the course accesses cmi.interactions.0, etc.
        interactions: makeEmptyArray('interactions')
    };
}


// ─────────────────────────────────────────────────────────────
//  Array helpers
//  objectives and interactions are plain JS arrays with extra
//  _children and _count properties attached to the array itself.
// ─────────────────────────────────────────────────────────────

var ARRAY_CHILDREN = {
    objectives:   'id,score,status',
    interactions: 'id,objectives,time,type,correct_responses,weighting,student_response,result,latency'
};

function makeEmptyArray(name) {
    var arr = [];
    arr._children = {
        value: ARRAY_CHILDREN[name] || '',
        get: function() { return this.value; },
        set: function() { throwError('402'); }
    };
    arr._count = {
        get: function() { return arr.length; },
        set: function() { throwError('402'); }
    };
    return arr;
}

// Creates a blank entry for cmi.objectives[n]
function createObjectiveEntry() {
    return {
        id: {
            value: null,
            get: function() {
                if (this.value === null) { this.value = ''; throwError('201'); }
                return this.value;
            },
            set: function(param) {
                if (!isValidType(param, 'CMIIdentifier')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        score: {
            _children: {
                value: 'raw,min,max',
                get: function() { return this.value; },
                set: function() { throwError('402'); }
            },
            raw: makeScoreField('score'),
            min: makeScoreField('minscore'),
            max: makeScoreField('maxscore')
        },
        status: {
            value: 'not attempted',
            get: function() {
                var s = SCOState.lesson_status;
                if (s === 'passed' || s === 'failed' || s === 'completed') this.value = s;
                return this.value;
            },
            set: function(param) {
                if (!isValidType(param, 'CMIVocabulary', 'Status')) throwError('405');
                this.value = param;
                // Only update the overall status if it hasn't been set by the course yet
                if (SCOState.lesson_status === 'not attempted') SCOState.lesson_status = param;
                return 'true';
            }
        }
    };
}

// Creates a blank entry for cmi.interactions[n]
function createInteractionEntry() {
    var inter = {
        id: {
            value: '',
            get: function() { throwError('404'); },              // write-only
            set: function(param) {
                if (!isValidType(param, 'CMIIdentifier')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        time: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                if (!isValidType(param, 'CMITime')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        type: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                if (!isValidType(param, 'CMIVocabulary', 'Interaction')) throwError('405');
                this.value = param;
                return 'true';
            },
            // Used internally when validating student_response
            getValue: function() { return this.value; }
        },
        weighting: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                if (!isValidType(param, 'CMIDecimal')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        student_response: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                // The valid format depends on the interaction type (e.g. 'choice', 'fill-in')
                var interactionType = cmi.interactions[currentInteractionIndex].type.getValue();
                if (!isValidType(param, 'CMIFeedback', interactionType)) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        result: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                if (!isValidType(param, 'CMIVocabulary', 'Result')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        latency: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                if (!isValidType(param, 'CMITimespan')) throwError('405');
                this.value = param;
                return 'true';
            }
        },
        objectives: [],
        correct_responses: []
    };

    inter.objectives._count = {
        get: function() { return inter.objectives.length; },
        set: function() { throwError('402'); }
    };

    inter.correct_responses._count = {
        get: function() { return inter.correct_responses.length; },
        set: function() { throwError('402'); }
    };

    return inter;
}

// Creates a blank entry for cmi.interactions[n].correct_responses[m]
function createCorrectResponseEntry() {
    return {
        pattern: {
            value: '',
            get: function() { throwError('404'); },
            set: function(param) {
                var interactionType = cmi.interactions[currentInteractionIndex].type.getValue();
                if (!isValidType(param, 'CMIFeedback', interactionType)) throwError('405');
                this.value = param;
                return 'true';
            }
        }
    };
}

// Small reusable score field factory (raw/min/max all behave the same way)
function makeScoreField(stateKey) {
    return {
        value: '',
        get: function() { return this.value; },
        set: function(param) {
            if (!isValidScoreOrBlank(param)) throwError('405');
            this.value = param;
            SCOState[stateKey] = param;
            return 'true';
        }
    };
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 5 – CMI PROPERTY PATH RESOLVER
//
//  Courses call LMSGetValue("cmi.core.lesson_status") with a dot-
//  separated path string.  This function walks the cmi object tree
//  and returns the matching field object (which has .get() / .set()).
//
//  It also handles numeric indices for arrays:
//    "cmi.interactions.0.id"  →  cmi.interactions[0].id
//  Auto-creating array entries if they don't exist yet.
// ═══════════════════════════════════════════════════════════════

function resolveProperty(path) {
    if (typeof path !== 'string' || !path) throwError('201');

    var parts = path.split('.');

    // Every SCORM path must start with 'cmi'
    if (parts[0] !== 'cmi') throwError('201');

    var current = cmi;

    for (var i = 1; i < parts.length; i++) {
        var part = parts[i];

        // Is this part a numeric array index?  e.g. '0' in 'cmi.interactions.0.id'
        if (/^\d+$/.test(part)) {
            var index      = parseInt(part, 10);
            var parentName = parts[i - 1]; // 'interactions', 'objectives', or 'correct_responses'

            // Indices must be added one at a time – you can't jump from 0 to 5
            if (index > current.length) throwError('201');

            // Auto-create the entry on first access
            if (!current[index]) {
                if (parentName === 'interactions') {
                    current[index] = createInteractionEntry();
                } else if (parentName === 'objectives') {
                    current[index] = createObjectiveEntry();
                } else if (parentName === 'correct_responses') {
                    current[index] = createCorrectResponseEntry();
                } else {
                    throwError('201');
                }
            }

            // Keep track of the current interaction index for student_response validation
            if (parentName === 'interactions') currentInteractionIndex = index;

            current = current[index];

        } else {
            // Normal named property – just step into it
            if (current[part] === undefined) {
                if (part === '_children') throwError('202');
                if (part === '_count')    throwError('203');
                throwError('201');
            }
            current = current[part];
        }
    }

    return current;
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 6 – THE 8 LMS API FUNCTIONS
//  These are the only functions that SCORM courses ever call.
// ═══════════════════════════════════════════════════════════════

function LMSInitialize(param) {
    log('LMSInitialize("' + param + '")');
    resetError();

    var result = 'false';
    try {
        if (param !== '') throwError('201', 'Parameter must be an empty string');
        if (lmsState !== -1 && lmsState !== 1) throwError('101', 'Already initialized');

        // Read window.tl_sco_data now (set by CoursePlayer.vue before the iframe loaded)
        initSCOState();

        cmi      = buildCmi(); // build a fresh data tree using the loaded SCOState
        lmsState = 0;          // mark as running
        result   = 'true';
    } catch (err) {
        handleCaughtError(err);
    }

    log('LMSInitialize → ' + result);
    return result;
}

function LMSFinish(param) {
    log('LMSFinish("' + param + '")');
    resetError();

    var result = 'false';
    try {
        if (param !== '') throwError('201', 'Parameter must be an empty string');
        requireRunning();

        // 1. Set a final lesson_status if the course never set one
        if (!SCOState.lesson_status) {
            var mastery = SCOState.masteryscore;
            if (mastery) {
                // Compare score against mastery threshold
                var passed = parseFloat(cmi.core.score.raw.get()) >= parseFloat(mastery);
                var status = passed ? 'passed' : 'failed';
                SCOState.lesson_status = status;
                cmi.core.lesson_status.set(status);
            } else {
                SCOState.lesson_status = 'completed';
                cmi.core.lesson_status.set('completed');
            }
        }

        // 2. Decide 'entry' for the learner's NEXT visit based on how they left
        SCOState.entry = (SCOState.scorm_exit === 'suspend') ? 'resume' : '';

        // 3. Send all data to the server
        commitData('finish');

        lmsState = 1; // mark as finished
        result   = 'true';
    } catch (err) {
        handleCaughtError(err);
    }

    log('LMSFinish → ' + result);
    return result;
}

function LMSGetValue(path) {
    log('LMSGetValue("' + path + '")');
    resetError();

    var result = '';
    try {
        requireRunning();
        var prop = resolveProperty(path);
        result   = String(prop.get());
    } catch (err) {
        handleCaughtError(err);
    }

    log('LMSGetValue → "' + result + '"');
    return result;
}

function LMSSetValue(path, value) {
    log('LMSSetValue("' + path + '", "' + value + '")');
    resetError();

    var result = 'false';
    try {
        requireRunning();
        var prop = resolveProperty(path);
        result   = String(prop.set(value));
    } catch (err) {
        handleCaughtError(err);
    }

    log('LMSSetValue → ' + result);
    return result;
}

function LMSCommit(param) {
    log('LMSCommit("' + param + '")');
    resetError();

    var result = 'false';
    try {
        if (param !== '') throwError('201', 'Parameter must be an empty string');
        requireRunning();
        commitData('');
        result = 'true';
    } catch (err) {
        handleCaughtError(err);
    }

    log('LMSCommit → ' + result);
    return result;
}

function LMSGetLastError() {
    log('LMSGetLastError → ' + currentErrorCode);
    return currentErrorCode;
}

function LMSGetErrorString(code) {
    var key     = (code === '' || code == null) ? currentErrorCode : String(code);
    var message = ERROR_MESSAGES[key] || ERROR_MESSAGES['0'];
    log('LMSGetErrorString(' + key + ') → ' + message);
    return message;
}

function LMSGetDiagnostic(code) {
    var key    = (code === '' || code == null) ? currentErrorCode : String(code);
    var detail = ERROR_DETAILS[key] || currentErrorDetail || '';
    log('LMSGetDiagnostic(' + key + ') → ' + detail);
    return detail;
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 7 – DATA COMMIT
//  Packages up SCOState and sends it to the server via scormPost().
//  Called by both LMSCommit and LMSFinish.
// ═══════════════════════════════════════════════════════════════

function commitData(mode) {
    // mode = '' for a mid-session commit
    // mode = 'finish' to include session_time (only sent at the very end)

    // Sync the credit field from CMI into SCOState
    SCOState.credit = cmi.core.credit.get();

    // Collect all interaction data into a plain array so it can be JSON-serialized
    SCOState.interactions = [];
    for (var i = 0; i < cmi.interactions.length; i++) {
        var inter = cmi.interactions[i];
        var entry = {
            id:               inter.id.value,
            latency:          inter.latency.value,
            result:           inter.result.value,
            student_response: inter.student_response.value,
            time:             inter.time.value,
            type:             inter.type.value,
            weighting:        inter.weighting.value,
            correct_responses: []
        };
        for (var j = 0; j < inter.correct_responses.length; j++) {
            entry.correct_responses.push({
                pattern: inter.correct_responses[j].pattern.value
            });
        }
        SCOState.interactions.push(entry);
    }

    // Make a shallow copy so we can safely delete fields without touching SCOState
    var dataToSend = Object.assign({}, SCOState);

    // Only include session_time when finishing (not on mid-session commits)
    if (mode !== 'finish') {
        delete dataToSend.session_time;
    }

    // The server doesn't understand 'browsed' – translate it to 'incomplete'
    if (dataToSend.lesson_status === 'browsed') {
        dataToSend.lesson_status = 'incomplete';
    }

    // Notify a native mobile wrapper if one is present (compatibility mode)
    if (typeof JSInterface !== 'undefined' && typeof JSInterface.commit !== 'undefined') {
        JSInterface.commit(JSON.stringify(dataToSend));
    }

    // Send the data to the server
    if (typeof window.scormPost === 'function') {
        window.scormPost(dataToSend);
    } else {
        log('[SCORM] scormPost not available, skipping commit');
    }
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 8 – DATA TYPE VALIDATION
//
//  Before any value is stored, we check it matches the expected
//  SCORM data type.  Returns true if valid, false if not.
// ═══════════════════════════════════════════════════════════════

// Shorthand: a score must be a decimal 0–100 OR a blank string
function isValidScoreOrBlank(param) {
    var isDecimal = isValidType(param, 'CMIDecimal') && param >= 0 && param <= 100;
    var isBlank   = isValidType(param, 'CMIBlank');
    return isDecimal || isBlank;
}

/**
 * isValidType(value, type, subtype)
 *
 * type    – the SCORM data type name (e.g. 'CMIDecimal', 'CMIVocabulary')
 * subtype – only needed for CMIFeedback and CMIVocabulary
 *           (e.g. 'Status', 'Exit', 'Interaction', 'choice', 'fill-in', …)
 */
function isValidType(value, type, subtype) {
    switch (type) {

        case 'CMIBlank':
            // Must be an empty string
            return /^$/.test(value);

        case 'CMIBoolean':
            // Must be literally 'true' or 'false'
            return /^(true|false)$/.test(value);

        case 'CMIDecimal':
            // A positive or negative number, optionally with a decimal point
            return /^-?\d+(\.\d+)?$/i.test(value);

        case 'CMIIdentifier':
            // Up to 1024 characters: letters, digits, spaces, and common punctuation
            return /^[\s\w\-\.\(\)\,\:\;\+\%\']{1,1024}$/i.test(value);

        case 'CMIInteger':
            // A whole number from 0 to 65536
            return /^[0-9]{1,5}$/i.test(value) && value <= 65536;

        case 'CMISInteger':
            // A signed integer from -32768 to +32768
            return /^(\-|\+)?[0-9]{1,5}$/i.test(value) && value <= 32768 && value >= -32768;

        case 'CMIString255':
            // Any string up to 255 characters (including newlines)
            return /^(.|\n){0,255}$/i.test(value);

        case 'CMIString4096':
            // Extended to 65535 to match SCORM 2004's limit
            return /^.{0,65535}$/mi.test(value);

        case 'CMITime':
            // A clock time in the format HH:MM:SS (with optional decimal seconds)
            var t = /^(\d\d):(\d\d):(\d\d)(.\d{1,2})?$/i.exec(value);
            return t && t[1] < 24 && t[2] < 60 && t[3] < 60;

        case 'CMITimespan':
            // A duration in the format HHHH:MM:SS (with optional decimal seconds)
            return /^\d{2,4}:\d\d:\d\d(.\d{1,2})?$/i.test(value);

        case 'CMIFeedback':
            // Format depends on the interaction type (choice, fill-in, matching, etc.)
            switch (subtype) {
                case 'true-false':  return /^(0|1|t|f)$/.test(value);
                case 'choice':      return /^.{0,4096}$/i.test(value);
                case 'fill-in':     return /^\s*.[\s\S]{1,4096}$/i.test(value);
                case 'numeric':     return /^-?\d+(\.\d+)?$/i.test(value);
                case 'likert':      return /^.{0,1024}$/i.test(value);
                case 'matching':    return /^[a-z0-9].[a-z0-9](,[a-z0-9].[a-z0-9])*$/i.test(value);
                case 'performance': return /^.{0,4096}$/i.test(value);
                case 'sequencing':  return /^[a-z0-9](,[a-z0-9])*$/i.test(value);
                default:            return false;
            }

        case 'CMIVocabulary':
            // A fixed set of allowed words, depends on which field we're validating
            switch (subtype) {
                case 'Mode':             return /^(normal|review|browse)$/.test(value);
                case 'Status':           return /^(passed|completed|failed|incomplete|browsed|not attempted)$/.test(value);
                case 'Exit':             return /^(time-out|suspend|logout|)$/.test(value);
                case 'Credit':           return /^(credit|no-credit)$/.test(value);
                case 'Entry':            return /^(ab-initio|resume|)$/.test(value);
                case 'Interaction':      return /^(true-false|choice|fill-in|matching|performance|likert|sequencing|numeric)$/.test(value);
                case 'Result':           return /^(correct|wrong|unanticipated|neutral|(-?\d+(\.\d+)?))$/.test(value);
                case 'TimeLimitAction':  return /^(exit,message|exit,no message|continue,message|continue,no message)$/.test(value);
                default:                 return false;
            }

        default:
            return false;
    }
}


// ═══════════════════════════════════════════════════════════════
//  SECTION 9 – INSTALL THE API ON window.API
//
//  SCORM courses look for window.API on the parent frame.
//  We attach all 8 functions to it here.
//  This must run BEFORE the SCORM iframe is loaded.
// ═══════════════════════════════════════════════════════════════

function API() {}

API.LMSInitialize     = LMSInitialize;
API.LMSFinish         = LMSFinish;
API.LMSGetValue       = LMSGetValue;
API.LMSSetValue       = LMSSetValue;
API.LMSCommit         = LMSCommit;
API.LMSGetLastError   = LMSGetLastError;
API.LMSGetErrorString = LMSGetErrorString;
API.LMSGetDiagnostic  = LMSGetDiagnostic;

/**
 * Call this BEFORE loading the SCORM iframe.
 * Sets window.API so the course can find the LMS runtime.
 * Also sets window.top.API for nested same-origin frames.
 */
export function installFullScormApi() {
  window.API = API;
  try {
    if (window.top) window.top.API = API;
  } catch {
    // ignore cross-origin top frame
  }
}

/**
 * Call this when the SCORM player component is unmounted.
 * Cleans up window.API so it doesn't leak between courses.
 */
export function removeFullScormApi() {
  // Reset module-level state so next session starts fresh
  lmsState = -1;
  SCOState = {};
  cmi      = null;

  try {
    if (window.API === API) delete window.API;
  } catch {
    window.API = undefined;
  }
  try {
    if (window.top && window.top.API === API) delete window.top.API;
  } catch {
    // ignore cross-origin top frame
  }
}
