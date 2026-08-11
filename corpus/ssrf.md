# Server-Side Request Forgery (SSRF) — CWE-918

## What it is
SSRF happens when an application takes a user-controlled URL or host and makes a
server-side network request to it without restricting the destination. Because the
request originates from the server, it can reach places the attacker cannot reach
directly: loopback (127.0.0.1), private ranges (10.0.0.0/8, 172.16.0.0/12,
192.168.0.0/16), link-local, and the cloud metadata endpoint at 169.254.169.254.

## Why it is dangerous
On a cloud host, the metadata endpoint can hand back IAM credentials and instance
secrets. Even without cloud metadata, SSRF lets an attacker port-scan and fingerprint
the internal network, and reach internal-only services (admin panels, databases,
dashboards) that were never exposed to the internet. If the response body is returned
to the caller, the vulnerability is "response-disclosure" SSRF and leaks internal
content directly; if not, it is "blind" SSRF and is exploited through timing and side
effects.

## How to fix it
Defense in depth, because a single control usually leaves a gap:

1. Resolve the destination host and reject private, loopback, link-local, and reserved
   IP ranges before every outbound fetch. Do this on the resolved IP, not just the
   hostname string, so a DNS name that points at 127.0.0.1 is also blocked.
2. Prefer an explicit allowlist of permitted hosts over a denylist of bad ones.
3. Require authentication and authorization on any endpoint that performs a
   user-directed fetch, so the fetch surface is not reachable anonymously.
4. Pin the connection to the resolved public IP to close the DNS-rebinding (TOCTOU)
   window, where the name resolves to a safe IP during validation and a private IP at
   connect time.

## What does NOT fix it
Only checking the URL scheme (http/https) does not stop SSRF; the host is still
unrestricted. Blocklisting the literal string "localhost" is trivially bypassed with
127.0.0.1, 0.0.0.0, decimal/hex IP encodings, or a DNS name that resolves internally.
