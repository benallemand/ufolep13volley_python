-- Migration: Create live_scores table for real-time score tracking
-- Issue: #186 - Live Scoring feature

CREATE TABLE IF NOT EXISTS live_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_match VARCHAR(20) NOT NULL,
    set_en_cours TINYINT NOT NULL DEFAULT 1,
    score_dom TINYINT NOT NULL DEFAULT 0,
    score_ext TINYINT NOT NULL DEFAULT 0,
    sets_dom TINYINT NOT NULL DEFAULT 0,
    sets_ext TINYINT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_match (id_match)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
