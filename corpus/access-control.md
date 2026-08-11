# Broken Access Control — OWASP A01

## What it is
Broken access control is when a user can act outside their intended permissions:
read or change another tenant's records, escalate their own role or plan, or reach an
admin function without being an admin. Broken Object Level Authorization (BOLA / IDOR)
is the most common form: the app trusts an object id from the request (like
/orders/1043) and returns it without checking that the object belongs to the caller.

## Multi-tenant isolation and the row-vs-column gap
In a multi-tenant system, PostgreSQL row-level security (RLS) is the strongest place to
enforce isolation because it lives in the database, below the application. But RLS is
row-shaped: a policy can say "you may see this row" and cannot say "you may see this row
but not the plan column." So `UPDATE profiles SET plan = 'pro' WHERE id = :me` passes the
row policy and upgrades the user for free. Closing that needs three layers: revised RLS
policies, an API-level allowlist of writable columns, and a database trigger that blocks
writes to privileged columns. Verify each control by deleting it and watching an
integration test catch the escalation.

## How to fix it
1. Enforce authorization in the database (row-level security) rather than only in
   application code, so a missed check in one handler does not expose data.
2. Deny by default. Every object access checks ownership or tenant scope on the server,
   never trusting an id supplied by the client.
3. Never expose privileged fields (role, plan, is_admin) to mass-assignment; allowlist
   the fields a request may write.
4. Write integration tests that perform the escalation attack against a real database
   and assert it is refused.
