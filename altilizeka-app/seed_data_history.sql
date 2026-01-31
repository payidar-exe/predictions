-- Add new columns for statistics (Safe to run multiple times)
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending'; -- 'pending', 'won', 'lost'
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS winning_amount numeric DEFAULT 0;
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS actual_result jsonb;

-- Clear old history for these specific dates to avoid dupes
DELETE FROM coupons WHERE date IN ('2026-01-14', '2026-01-13', '2026-01-12');

-- 1. Jan 14 (Big Win)
INSERT INTO coupons (date, city, type, star_cost, title, subtitle, status, winning_amount, legs) VALUES
(
  '2026-01-14', 
  'İstanbul', 
  'premium', 
  50, 
  'İstanbul Kahin Analizi', 
  'TUTAR: 450.00 TL', 
  'won', 
  12450.00,
  '[
    {"leg_no":1, "race_time":"14:30", "horses": [{"horse_name":"BOLD SEA ROVER", "program_no":1, "ai_score":85, "is_banko":false}, {"horse_name":"KING OF THE NIGHT", "program_no":2, "ai_score":90, "is_banko":false}]},
    {"leg_no":2, "race_time":"15:00", "horses": [{"horse_name":"LONG RUNNER", "program_no":1, "ai_score":99, "is_banko":true, "ai_note":"BANKO."}]},
    {"leg_no":3, "race_time":"15:30", "horses": [{"horse_name":"GELİBOLU RÜZGARI", "program_no":3, "ai_score":88, "is_banko":false}]},
    {"leg_no":4, "race_time":"16:00", "horses": [{"horse_name":"BURGAS", "program_no":1, "ai_score":95, "is_banko":false}]},
    {"leg_no":5, "race_time":"16:30", "horses": [{"horse_name":"YAVUZHAN", "program_no":2, "ai_score":82, "is_banko":false}]},
    {"leg_no":6, "race_time":"17:00", "horses": [{"horse_name":"HIZLI TAY", "program_no":4, "ai_score":80, "is_banko":false}]}
  ]'::jsonb
);

-- 2. Jan 13 (Small Win)
INSERT INTO coupons (date, city, type, star_cost, title, subtitle, status, winning_amount, legs) VALUES
(
  '2026-01-13', 
  'Adana', 
  'premium', 
  40, 
  'Adana Sürpriz Kurgu', 
  'TUTAR: 240.00 TL', 
  'won', 
  3200.00,
  '[
    {"leg_no":1, "race_time":"18:00", "horses": [{"horse_name":"TORAMANKAYA", "program_no":1, "ai_score":92, "is_banko":true}]}
  ]'::jsonb
);

-- 3. Jan 12 (Loss - Strategic to look real)
INSERT INTO coupons (date, city, type, star_cost, title, subtitle, status, winning_amount, legs) VALUES
(
  '2026-01-12', 
  'Bursa', 
  'premium', 
  40, 
  'Bursa Riskli Analiz', 
  'TUTAR: 120.00 TL', 
  'lost', 
  0,
  '[
    {"leg_no":1, "race_time":"13:30", "horses": [{"horse_name":"ALTIN SİMA", "program_no":1, "ai_score":85, "is_banko":false}]}
  ]'::jsonb
);
