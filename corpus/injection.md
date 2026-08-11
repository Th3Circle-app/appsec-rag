# Injection — OWASP A03 (SQL, Command, XSS)

## SQL injection
SQL injection happens when user input is concatenated or interpolated into a SQL string,
letting an attacker change the query. `db.query("SELECT * FROM users WHERE name = '" +
name + "'")` is injectable. The fix is parameterized queries (prepared statements):
`db.query("SELECT * FROM users WHERE name = $1", [name])`. The parameter is sent
separately from the query text, so input can never become SQL. Never build SQL by string
concatenation or template interpolation, and do not rely on escaping as the primary
defense.

## Command injection
Command injection happens when user input is placed into a shell command built by string
interpolation, such as `exec("ping " + host)` or `os.system(f"curl {url}")`. An attacker
supplies `; rm -rf /` or backticks to run their own commands. The fix is to avoid the
shell entirely: pass the command and its arguments as a list to an exec API that does not
invoke a shell (`subprocess.run(["ping", host])`, not `shell=True`). If a shell is truly
required, strictly validate input against an allowlist.

## Cross-site scripting (XSS)
XSS happens when untrusted data is written into a page as HTML, so it executes as script
in another user's browser. `element.innerHTML = userData` and
`dangerouslySetInnerHTML` are the usual sinks. The fix is to treat data as text, not
markup: use `textContent` instead of `innerHTML`, let the framework escape by default,
and apply a Content-Security-Policy so injected script cannot run.

## The common thread
Every injection is the same root cause: data crossing into a code context (SQL, shell,
HTML) without a boundary. Keep data as data. Use the API that separates the two.
