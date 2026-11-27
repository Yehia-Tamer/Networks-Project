# Report sections: Eyad

## 1. Extra feature: registration and stored history

**What it does.** A user creates an account once (username, email, display name,
password) and can then log in from any phone. Every account and every message is
stored in PostgreSQL, so the full chat history loads on any device, even after a
server restart.

**How it works.**
- `POST /auth/register` hashes the password with bcrypt; only the hash is stored.
- `POST /auth/login` checks the password and returns a JWT signed with HS256.
- The React `AuthContext` keeps the token in `localStorage` and sends it as
  `Authorization: Bearer <token>` on every REST call. The WebSocket and SSE
  connections carry it as `?token=` because browsers cannot set headers on a
  WebSocket.
- `GET /users/me`, `GET /users?search=` and `GET /users/{id}` return `UserOut`,
  which never includes the password hash.
- History: messages live in the `messages` table with an increasing
  `message_id`. After login, a phone loads its chats through REST (`/groups`,
  `/groups/{id}/messages`) and then syncs anything newer over the live
  connection, so the same history appears on every device.
- `last_seen` in `users` is updated when a socket disconnects, so others can see
  when someone was last online.

**Why this design.** Database-backed accounts give persistence across devices;
JWT lets the server verify a request without a database lookup each time; the
repository layer keeps all SQL out of the routers.

## 2. Real-time metrics

**What it does.** `GET /metrics` returns live counters from the server and a
React page (`/metrics`) refreshes them every 2 seconds.

| Metric | Meaning |
|---|---|
| active_connections | open sockets right now |
| messages_in / messages_out | total messages received from and sent to phones |
| bytes_in / bytes_out | total bytes received and sent |
| messages_per_second, bytes_per_second | rate over the last ~5 seconds |
| uptime_seconds | time since the server started |

**How it works.** `ConnectionManager` increments its counters on every connect,
disconnect, receive and send. The metrics router reads them, keeps a short list of
recent samples, and computes the per-second rates from the difference between
the newest sample and one about 5 seconds older.

**Why.** The rates show how load changes as 1 to 4 phones connect, which also
feeds Maryam's performance evaluation.
