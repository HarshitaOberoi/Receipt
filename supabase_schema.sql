create table if not exists public.students (
  registration_no text primary key,
  sr_no integer,
  username text,
  student_name text not null,
  date_of_birth text,
  father_name text,
  mother_name text,
  category text,
  ews_status text,
  aadhar_no text,
  degree text,
  mode_of_payment text,
  online_amount numeric default 0 not null,
  offline_amount numeric default 0 not null,
  fee_type text,
  updated_at timestamptz default now() not null
);

create index if not exists students_sr_no_idx on public.students (sr_no);
create index if not exists students_student_name_idx on public.students (student_name);
create index if not exists students_father_name_idx on public.students (father_name);

alter table public.students enable row level security;

drop policy if exists "Allow public read students" on public.students;
create policy "Allow public read students"
on public.students for select
to anon
using (true);

drop policy if exists "Allow public insert students" on public.students;
create policy "Allow public insert students"
on public.students for insert
to anon
with check (true);

drop policy if exists "Allow public update students" on public.students;
create policy "Allow public update students"
on public.students for update
to anon
using (true)
with check (true);
