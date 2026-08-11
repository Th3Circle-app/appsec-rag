# Leaked Secrets and Broken Crypto — OWASP A02 / A07

## Hard-coded secrets
A secret committed to code (an AWS key, a Stripe live key, a database URL with an inline
password, a private-key block) is exposed to everyone with repository access and stays in
git history even after it is removed. The fix is to read secrets from the environment or a
secrets manager, never from source, and to add secret scanning to CI so a leaked key
fails the build. If a real secret was committed, rotate it immediately; removing it from
the latest commit does not undo the exposure.

## Detecting secrets without crying wolf
A secret scanner that fires on every string nobody trusts gets turned off. Precision
matters: skip parameterized values, environment reads, bcrypt/argon hashes, and obvious
placeholders, and stay quiet in test and fixture files where fake secrets are used on
purpose, while still catching a real key anywhere. Report a line that is too long to scan
rather than silently skipping it, so coverage is never quietly dropped.

## Broken crypto and transport
Disabling TLS certificate verification (`rejectUnauthorized: false`, `verify=False`,
`requests.get(url, verify=False)`) makes traffic trivially interceptable; never disable
it outside a controlled test. MD5 and SHA-1 are not safe for passwords or security
integrity; hash passwords with bcrypt, argon2, or scrypt, which are slow by design.
Generating a token, session id, or OTP with `Math.random()` or a non-cryptographic RNG is
predictable; use a cryptographically secure source such as `crypto.randomBytes` or
`secrets.token_hex`.
