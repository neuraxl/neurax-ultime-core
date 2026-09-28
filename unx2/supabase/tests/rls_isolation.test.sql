begin;
select plan(8);

select tests.create_supabase_user('unx2-rls-a@example.com');
select tests.create_supabase_user('unx2-rls-b@example.com');

insert into public.organizations(name) values ('RLS Test Org A'),('RLS Test Org B');

insert into public.profiles(id,organization_id,role)
select u.id,o.id,'owner'
from auth.users u
join public.organizations o on o.name = case u.email
  when 'unx2-rls-a@example.com' then 'RLS Test Org A'
  when 'unx2-rls-b@example.com' then 'RLS Test Org B'
end
where u.email in ('unx2-rls-a@example.com','unx2-rls-b@example.com')
on conflict(id) do update set organization_id=excluded.organization_id;

insert into public.leads(organization_id,company_name,score)
select id,case name when 'RLS Test Org A' then 'Visible A' else 'Hidden B' end,90
from public.organizations where name in ('RLS Test Org A','RLS Test Org B');

select tests.authenticate_as('unx2-rls-a@example.com');
select is((select count(*)::int from public.leads where company_name='Visible A'),1,'A reads own tenant row');
select is((select count(*)::int from public.leads where company_name='Hidden B'),0,'A cannot read B');
select throws_ok($sql$insert into public.leads(organization_id,company_name) values ((select id from public.organizations where name='RLS Test Org B'),'Cross tenant')$sql$,'42501','A cannot write B');

select tests.authenticate_as('unx2-rls-b@example.com');
select is((select count(*)::int from public.leads where company_name='Hidden B'),1,'B reads own tenant row');
select is((select count(*)::int from public.leads where company_name='Visible A'),0,'B cannot read A');
select throws_ok($sql$insert into public.leads(organization_id,company_name) values ((select id from public.organizations where name='RLS Test Org A'),'Cross tenant')$sql$,'42501','B cannot write A');

select tests.authenticate_as('unx2-rls-a@example.com');
select is((select count(*)::int from public.organizations where public.is_org_member(id)),1,'A has one organization');
select is((select count(*)::int from public.organizations),1,'organization listing is isolated');

select * from finish();
rollback;