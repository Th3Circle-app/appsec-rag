# Securing AI Agents and MCP Tools

## Why agent tools are a new attack surface
An MCP (Model Context Protocol) tool is a function an autonomous model can call with
arguments the model chose, sometimes while it is acting on untrusted content it just read
(a web page, an issue comment, a file). So every tool argument must be treated as
attacker-controlled, the same way you treat input at any other trust boundary. The
interesting question about an agent tool is not "what can it do" but "what happens when
someone points it somewhere it should not go."

## The trust boundaries to defend
1. Path confinement. A file tool must never read outside the workspace it was given.
   Reject `..` traversal, absolute paths, null bytes, and symlinks that escape the root,
   resolving the real path before the containment check so a symlink cannot bridge out.
2. Resource bounds. A single tool call must not be able to exhaust host memory or CPU;
   cap per-call input and refuse oversized calls in milliseconds, not after allocating.
3. No catastrophic backtracking. Any regex a tool runs on attacker input must be bounded
   so a crafted argument cannot hang the process (ReDoS).
4. Arguments are inert data. A malicious string passed to a tool is data to be processed,
   never executed.
5. Refusals do not leak. A rejected call returns a structured error, never a stack trace
   or a partial read.

## Deciding refusal in code, not in the prompt
The security decision must live in deterministic code, not in a prompt telling the model
what not to do. A prompt is a suggestion an attacker or the model itself can step over; a
path confined in code blocks an unknown payload the prompt never anticipated. Keep an
audit trail of every denied call so a caught attack becomes a permanent regression test,
but never let the audit corpus, rather than the code, be the thing that makes the call.

## Verifying it holds
Do not assume a control works because it looks right. Spawn the real agent server and
fire the attacks at it over the protocol, then triage each as held, breached, or
unverified, and treat "no answer" as unverified, never as secure.
