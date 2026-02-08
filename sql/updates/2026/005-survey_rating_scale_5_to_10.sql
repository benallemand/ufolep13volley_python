-- Migration des notes de survey de l'échelle /5 vers /10
-- Issue #201: Survey : passer la notation de 0→5 à 0→10
-- Conversion: nouvelle_note = ancienne_note * 2

UPDATE survey SET
    on_time = on_time * 2,
    spirit = spirit * 2,
    referee = referee * 2,
    catering = catering * 2,
    `global` = `global` * 2;
