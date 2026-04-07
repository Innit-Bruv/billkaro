create table seller_profiles (
  session_id text primary key,
  name text default '',
  gstin text default '',
  created_at timestamptz default now()
);
