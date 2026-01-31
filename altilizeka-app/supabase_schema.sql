-- AltılıZeka Database Schema
-- Run this in Supabase SQL Editor

-- 1. Profiles Table (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  avatar_url TEXT,
  star_balance INTEGER DEFAULT 50 NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view their own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- 2. Star Packages Table
CREATE TABLE IF NOT EXISTS star_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  stars INTEGER NOT NULL,
  price_tl DECIMAL(10,2) NOT NULL,
  ios_product_id TEXT,
  android_product_id TEXT,
  is_popular BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default packages
INSERT INTO star_packages (name, stars, price_tl, ios_product_id, android_product_id, is_popular) VALUES
  ('100 Yıldız', 100, 49.00, 'com.altilizeka.stars.100', 'stars_100', FALSE),
  ('250 Yıldız', 250, 99.00, 'com.altilizeka.stars.250', 'stars_250', TRUE),
  ('500 Yıldız', 500, 179.00, 'com.altilizeka.stars.500', 'stars_500', FALSE);

-- 3. Coupons Table
CREATE TABLE IF NOT EXISTS coupons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  city TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('free', 'premium')),
  star_cost INTEGER DEFAULT 0,
  title TEXT NOT NULL,
  subtitle TEXT,
  legs JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE coupons ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Everyone can view coupons
CREATE POLICY "Anyone can view coupons" ON coupons
  FOR SELECT TO authenticated, anon USING (true);

-- 4. User Coupons (Purchased)
CREATE TABLE IF NOT EXISTS user_coupons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  coupon_id UUID REFERENCES coupons(id) ON DELETE CASCADE,
  purchased_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, coupon_id)
);

-- Enable RLS
ALTER TABLE user_coupons ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own purchases" ON user_coupons
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own purchases" ON user_coupons
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 5. Star Transactions
CREATE TABLE IF NOT EXISTS star_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('purchase', 'spend', 'bonus')),
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE star_transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own transactions" ON star_transactions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own transactions" ON star_transactions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 6. Function to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, star_balance)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'display_name', 50);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 7. Sample Coupon Data (for testing)
INSERT INTO coupons (date, city, type, star_cost, title, subtitle, legs) VALUES
  (CURRENT_DATE, 'İstanbul Veliefendi', 'free', 0, 'Günün Banko Kuponu', NULL, 
   '[{"leg_no": 1, "race_time": "14:30", "field_size": 8, "horses": [{"program_no": 4, "horse_name": "GÜLŞAH SULTAN", "is_banko": true, "ai_note": "Son idmanında çok diri görüldü, kum pisti seviyor."}]}, {"leg_no": 2, "race_time": "15:00", "field_size": 10, "horses": [{"program_no": 2, "horse_name": "STORM RIDER", "is_banko": true, "ai_note": "Jokey değişikliği performansı artırabilir."}, {"program_no": 7, "horse_name": "RÜZGARIN OĞLU", "is_banko": false, "ai_note": null}]}]'::jsonb),
  (CURRENT_DATE, 'Ankara 75. Yıl', 'premium', 50, 'Sürpriz Analiz Paketi', 'YÜKSEK GANYAN',
   '[{"leg_no": 1, "race_time": "21:00", "field_size": 12, "horses": [{"program_no": 9, "horse_name": "DEMİR PENÇE", "is_banko": true, "ai_note": "Bugün banko tercihimiz. Jokey değişikliği %15 performans artışı sağlayabilir."}]}]'::jsonb),
  (CURRENT_DATE, 'Bursa Osmangazi', 'premium', 50, 'Bursa Altılısı Tahmini', 'ÖZEL ANALİZ',
   '[{"leg_no": 1, "race_time": "18:30", "field_size": 9, "horses": [{"program_no": 3, "horse_name": "KAPLAN", "is_banko": true, "ai_note": "Form grafiği çok iyi, mesafe avantajı var."}]}]'::jsonb);
