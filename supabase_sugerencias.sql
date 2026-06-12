-- ============================================================
-- SUGERENCIAS (Anonymous Suggestion Box)
-- Run this in Supabase SQL Editor
-- ============================================================

CREATE TABLE IF NOT EXISTS sugerencias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    category TEXT NOT NULL,        -- mejora_proceso, ambiente_laboral, conflicto, idea_nueva, reconocimiento, queja, otro
    message TEXT NOT NULL,
    urgency TEXT DEFAULT 'media',  -- baja, media, alta
    word_count INTEGER,
    submitted_at TIMESTAMPTZ DEFAULT NOW()
    -- NO member/email/name field — 100% anonymous
);

CREATE INDEX idx_sugerencias_category ON sugerencias(category);
CREATE INDEX idx_sugerencias_urgency ON sugerencias(urgency);
