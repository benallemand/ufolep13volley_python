-- Migration: Add version column to live_scores for optimistic concurrency control
-- Issue: #196 - Dissocier saisie du score et enregistrement (autosave / réseau instable)

ALTER TABLE live_scores
    ADD COLUMN version INT NOT NULL DEFAULT 1 AFTER is_active;
