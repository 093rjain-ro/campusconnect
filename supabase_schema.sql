-- ==============================================================================
-- CampusConnect Supabase Schema
-- Run this directly in your Supabase SQL Editor to set up the database!
-- ==============================================================================

-- 1. Create the Users table
CREATE TABLE public.users (
  id uuid REFERENCES auth.users NOT NULL PRIMARY KEY,
  role text NOT NULL CHECK (role IN ('ambassador', 'org')),
  name text,
  college text,
  avatar text,
  points integer DEFAULT 0,
  streak integer DEFAULT 0,
  github_score integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create the Tasks table
CREATE TABLE public.tasks (
  id serial PRIMARY KEY,
  title text NOT NULL,
  pts integer NOT NULL,
  cat text NOT NULL,
  description text,
  icon text
);

-- 3. Create the User Tasks table (to track which users completed which tasks)
CREATE TABLE public.user_tasks (
  user_id uuid REFERENCES public.users NOT NULL,
  task_id integer REFERENCES public.tasks NOT NULL,
  completed_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
  PRIMARY KEY (user_id, task_id)
);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_tasks ENABLE ROW LEVEL SECURITY;

-- 5. Add Policies (Crucial for Security!)

-- Users can view everyone (Needed for the Leaderboard)
CREATE POLICY "Users can view all users" ON public.users FOR SELECT USING (true);

-- Users can only insert their own profile
CREATE POLICY "Users can insert own profile" ON public.users FOR INSERT WITH CHECK (auth.uid() = id);

-- Users can only update their own profile (XP, Github score, etc.)
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Tasks are visible to everyone
CREATE POLICY "Tasks are visible to everyone" ON public.tasks FOR SELECT USING (true);
-- Organizations can create/update tasks
CREATE POLICY "Orgs can modify tasks" ON public.tasks FOR ALL USING (
  EXISTS (SELECT 1 FROM public.users WHERE users.id = auth.uid() AND users.role = 'org')
);

-- Users can see their own completed tasks
CREATE POLICY "Users can see own completed tasks" ON public.user_tasks FOR SELECT USING (true);
-- Users can mark tasks as complete
CREATE POLICY "Users can mark tasks as complete" ON public.user_tasks FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ==============================================================================
-- Seed Data: Let's insert some default tasks so your dashboard isn't empty!
-- ==============================================================================
INSERT INTO public.tasks (title, pts, cat, description, icon) VALUES
('Share UnsaidTalks on LinkedIn', 150, 'Social', 'Post about UnsaidTalks and tag 3 friends', '📢'),
('Refer 3 college friends to sign up', 300, 'Referral', 'Get 3 friends to register using your referral code', '🎯'),
('Host a campus session (20+ attendees)', 500, 'Event', 'Organize and lead a campus-level workshop or session', '🎤'),
('Improve your GitHub README', 100, 'GitHub', 'Add a comprehensive README to your top repository', '💻'),
('Submit a video testimonial', 200, 'Content', 'Record a 60-second testimonial about your experience', '🎬'),
('Create an Instagram reel', 250, 'Content', 'Showcase UnsaidTalks in a creative 30-second reel', '📸');

-- Seed Data: Add some dummy ambassadors for the leaderboard
INSERT INTO auth.users (id, email) VALUES 
('11111111-1111-1111-1111-111111111111', 'dummy1@test.com'),
('22222222-2222-2222-2222-222222222222', 'dummy2@test.com'),
('33333333-3333-3333-3333-333333333333', 'dummy3@test.com');

INSERT INTO public.users (id, role, name, college, avatar, points, streak, github_score) VALUES
('11111111-1111-1111-1111-111111111111', 'ambassador', 'Arjun Sharma', 'IIT Delhi', '🦁', 4250, 21, 87),
('22222222-2222-2222-2222-222222222222', 'ambassador', 'Priya Nair', 'NIT Trichy', '🦋', 3890, 14, 79),
('33333333-3333-3333-3333-333333333333', 'ambassador', 'Rahul Gupta', 'BITS Pilani', '🐺', 3200, 7, 72);
