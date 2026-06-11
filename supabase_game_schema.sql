-- ============================================================
-- GAME-BASED ASSESSMENT SCHEMA
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- 1. GAME SESSIONS — one row per game played
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Link to existing data
    email TEXT NOT NULL,              -- correlate with participants.email
    name TEXT NOT NULL,
    phone TEXT,
    position TEXT,                     -- almacen, ventas_mostrador, pueblaventas

    -- Game metadata
    game_type TEXT NOT NULL,           -- game_terman, game_disc, game_competencias, game_big5
    test_equivalent TEXT NOT NULL,     -- terman, disc, competencias, big5 (maps to questionnaire test_type)

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,              -- total game duration in milliseconds

    -- Device/context
    user_agent TEXT,
    screen_width INTEGER,
    screen_height INTEGER,

    -- Status
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned'))
);

-- Index for correlation queries
CREATE INDEX idx_game_sessions_email ON game_sessions(email);
CREATE INDEX idx_game_sessions_game_type ON game_sessions(game_type);

-- 2. GAME EVENTS — granular behavioral data (every meaningful action)
CREATE TABLE IF NOT EXISTS game_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,

    -- Event identification
    mini_game TEXT NOT NULL,           -- e.g., 'verbal', 'math', 'spatial', 'comprehension' for terman
    event_type TEXT NOT NULL,          -- 'response', 'timeout', 'skip', 'error_recovery', 'strategy_change'
    event_index INTEGER NOT NULL,     -- sequential event number within the mini-game

    -- Timing (the core behavioral data)
    timestamp_ms BIGINT NOT NULL,     -- milliseconds since game start
    reaction_time_ms INTEGER,         -- time from stimulus presentation to response

    -- Response data
    stimulus JSONB,                   -- what was shown (e.g., {"sequence": [2,4,6,8], "options": [10,12,9,11]})
    response JSONB,                   -- what the user did (e.g., {"selected": 10, "position": [x,y]})
    correct BOOLEAN,                  -- was the response correct (for cognitive tasks)

    -- Behavioral metrics
    attempts INTEGER DEFAULT 1,       -- how many tries before moving on
    hesitation_ms INTEGER,            -- time before first interaction (mouse move, etc.)

    -- Dimensional mapping
    dimension TEXT,                   -- which construct this maps to (e.g., 'V', 'D', 'O', 'LID')

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analysis
CREATE INDEX idx_game_events_session ON game_events(session_id);
CREATE INDEX idx_game_events_mini_game ON game_events(mini_game);
CREATE INDEX idx_game_events_dimension ON game_events(dimension);

-- 3. GAME RESULTS — scored results in same format as questionnaire results
CREATE TABLE IF NOT EXISTS game_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,

    -- Link to existing data for correlation
    email TEXT NOT NULL,
    game_type TEXT NOT NULL,           -- game_terman, game_disc, game_competencias, game_big5
    test_equivalent TEXT NOT NULL,     -- terman, disc, competencias, big5

    -- Scores in SAME FORMAT as questionnaire results (for direct correlation)
    scores JSONB NOT NULL,            -- e.g., {"V": 38, "M": 41, "S": 34, "C": 32}
    percentages JSONB NOT NULL,       -- e.g., {"V": 76.0, "M": 82.0, "S": 85.0, "C": 91.4}
    dominant_trait TEXT,              -- e.g., "CI: 110" or "I" or "Trabajo en Equipo"
    description TEXT,                 -- e.g., "Nivel Superior de razonamiento"

    -- Game-specific behavioral metrics (NOT available from questionnaires)
    behavioral_metrics JSONB,         -- {
                                      --   "avg_reaction_time_ms": 1250,
                                      --   "accuracy_rate": 0.85,
                                      --   "speed_accuracy_tradeoff": 0.72,
                                      --   "consistency_index": 0.91,
                                      --   "frustration_recovery_ms": 800,
                                      --   "exploration_rate": 0.65,
                                      --   "risk_tolerance": 0.45,
                                      --   "learning_curve_slope": 0.12
                                      -- }

    -- Correlation with questionnaire (filled in when both exist)
    questionnaire_participant_id UUID, -- FK to participants.id if questionnaire was also taken
    correlation_data JSONB,           -- computed correlation between game and questionnaire scores

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for correlation queries
CREATE INDEX idx_game_results_email ON game_results(email);
CREATE INDEX idx_game_results_test_equiv ON game_results(test_equivalent);

-- 4. GAME CORRELATIONS — precomputed correlation analysis per person
CREATE TABLE IF NOT EXISTS game_correlations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL,

    -- What's being compared
    test_type TEXT NOT NULL,           -- terman, disc, competencias, big5
    game_result_id UUID REFERENCES game_results(id),
    questionnaire_result_id UUID,     -- references results.id
    interview_session_id UUID,        -- references interview_sessions.session_id (if exists)

    -- Correlation metrics
    dimension_correlations JSONB,     -- {"V": {"game": 76.0, "questionnaire": 82.0, "diff": -6.0}, ...}
    overall_correlation FLOAT,        -- Pearson r between game and questionnaire percentages
    agreement_level TEXT,             -- 'high' (r>.7), 'moderate' (.4-.7), 'low' (<.4)

    -- Interview cross-reference (if available)
    interview_metrics JSONB,          -- {"honesty_avg": 7.5, "stability_avg": 7.2, ...}

    -- Insights
    discrepancies JSONB,              -- dimensions where game and questionnaire diverge significantly
    notes TEXT,

    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_game_correlations_email ON game_correlations(email);

-- ============================================================
-- VIEWS for easy querying
-- ============================================================

-- View: Compare game vs questionnaire results side by side
CREATE OR REPLACE VIEW game_vs_questionnaire AS
SELECT
    gr.email,
    gr.test_equivalent AS test_type,
    gr.scores AS game_scores,
    gr.percentages AS game_percentages,
    gr.behavioral_metrics,
    r.scores AS questionnaire_scores,
    r.percentages AS questionnaire_percentages,
    gr.created_at AS game_date,
    r.created_at AS questionnaire_date
FROM game_results gr
LEFT JOIN participants p ON p.email = gr.email AND p.test_type = gr.test_equivalent
LEFT JOIN results r ON r.participant_id = p.id AND r.test_type = gr.test_equivalent;

-- View: Full candidate profile (questionnaire + game + interview)
CREATE OR REPLACE VIEW candidate_full_profile AS
SELECT
    p.email,
    p.name,
    p.position,
    p.test_type,
    r.scores AS questionnaire_scores,
    r.percentages AS questionnaire_percentages,
    r.dominant_trait AS questionnaire_dominant,
    gr.scores AS game_scores,
    gr.percentages AS game_percentages,
    gr.dominant_trait AS game_dominant,
    gr.behavioral_metrics,
    isc.recommendation AS interview_recommendation,
    isc.strengths AS interview_strengths,
    gc.overall_correlation,
    gc.agreement_level,
    gc.discrepancies
FROM participants p
LEFT JOIN results r ON r.participant_id = p.id
LEFT JOIN game_results gr ON gr.email = p.email AND gr.test_equivalent = p.test_type
LEFT JOIN interview_scores isc ON isc.participant_email = p.email
LEFT JOIN game_correlations gc ON gc.email = p.email AND gc.test_type = p.test_type;
