# CyberSentinel DLP - Project Memory for Claude

> **Last updated**: 2026-03-27
> **Purpose**: Handoff document so a new Claude instance can resume work seamlessly.

---

## 1. Project Overview

**CyberSentinel DLP** is an enterprise Data Loss Prevention platform that monitors endpoints, cloud storage, and network activity for sensitive data exfiltration.

| Component | Tech | Location | Port |
|-----------|------|----------|------|
| API Server | FastAPI (Python) | `server/` | 55000 |
| Dashboard | React + Vite + TypeScript + Tailwind | `dashboard/` | 4000 |
| Windows Agent | C++ (compiled .exe) | `agents/endpoint/windows/` | - |
| Linux Agent | Python | `agents/endpoint/linux/` | - |
| PostgreSQL | 15-alpine | - | 5432 |
| MongoDB | 7 | - | 27017 |
| Redis | 7-alpine | - | 6379 |
| OpenSearch | 2.11 | - | 9200 |
| Celery Worker | Python (same image as server) | - | - |
| Celery Beat | Python (same image as server) | - | - |

**Docker Compose**: `docker-compose.yml` (dev), `docker-compose.prod.yml` (prod)
**Default Login**: `admin@cybersentinel.local` / `admin123`

---

## 2. Architecture Summary

```
Agents (Windows/Linux) --> POST /api/v1/events/ --> EventProcessor Pipeline:
  1. Validate
  2. Normalize
  3. Enrich
  4. Classify (ClassificationEngine - rule-based, 20 default rules)
  5. Evaluate Policies (DatabasePolicyEvaluator)
  6. Execute Actions (block, alert, quarantine, redact, encrypt, notify, etc.)
  --> Store in MongoDB (dlp_events collection)
  --> Dashboard queries via GET /api/v1/events/

Cloud Integrations:
  - Google Drive: OAuth + folder polling via Celery
  - OneDrive: Microsoft Graph + delta queries
```

### Classification Levels (by confidence score)
- **Public**: 0.0 - 0.3
- **Internal**: 0.3 - 0.6
- **Confidential**: 0.6 - 0.8
- **Restricted**: 0.8 - 1.0

### Databases
- **PostgreSQL**: Users, agents, policies, rules, alerts, cloud connections
- **MongoDB**: DLP events (`dlp_events` collection), audit logs
- **Redis**: Cache, sessions, OAuth state
- **OpenSearch**: Event search & analytics indexing

---

## 3. Key Files You'll Touch Most

| File | Purpose |
|------|---------|
| `server/app/api/v1/events.py` | Event CRUD endpoints, `EventCreate` & `DLPEvent` models, `_build_event_title()`, `_merge_processed_event()` |
| `server/app/services/event_processor.py` | 6-stage event processing pipeline, classification integration |
| `server/app/services/classification_engine.py` | Rule-based content classification with confidence scoring |
| `server/app/policies/database_policy_evaluator.py` | Policy condition evaluation against events |
| `server/app/actions/action_executor.py` | Execute policy actions (block, alert, quarantine, etc.) |
| `dashboard/src/pages/Events.tsx` | Main events page with list + detail modal (~1100 lines) |
| `dashboard/src/lib/api.ts` | API client, `Event` type definition, all API functions |
| `dashboard/src/pages/Dashboard.tsx` | Overview stats page |
| `dashboard/src/pages/Rules.tsx` | Classification rules management |
| `dashboard/src/pages/Policies.tsx` | Policy CRUD with condition builder |
| `agents/endpoint/windows/` | C++ Windows agent source |
| `agents/endpoint/linux/agent.py` | Python Linux agent |

---

## 4. API Endpoints Quick Reference

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/v1/events/` | None | Agent submits events |
| GET | `/api/v1/events/` | JWT | Query events (pagination, filters) |
| GET | `/api/v1/events/{id}` | JWT | Single event |
| DELETE | `/api/v1/events/clear` | Admin | Clear all events |
| POST | `/api/v1/agents/register` | None | Agent self-registration |
| GET | `/api/v1/agents/{id}/policy` | None | Agent fetches policy bundle |
| POST | `/api/v1/classification/classify` | JWT | Manual content classification |
| CRUD | `/api/v1/rules/` | JWT | Classification rules |
| POST | `/api/v1/rules/test` | JWT | Test content against rules |
| CRUD | `/api/v1/policies/` | JWT | DLP policies |
| GET | `/api/v1/alerts/` | JWT | List alerts |
| POST | `/api/v1/auth/login` | None | Login |

---

## 5. Current State of Uncommitted Work (as of 2026-03-27)

### What was being worked on
Enhancement to support **classification metadata display** in the dashboard and **event titles**.

### Modified files and what changed

#### `server/app/api/v1/events.py`
- **DLPEvent model**: Added fields: `title`, `classification_level`, `classification` (list), `classification_metadata` (dict). Changed `classification_score` and `classification_labels` to `Optional`.
- **create_event()**: Now stores `classification_level` from agent input in `event_doc` (was missing before - bug fix).
- **_merge_processed_event()**: Now merges `classification_metadata` from the event processor output AND overrides `classification_level` from it (bug fix - processor's classification_level was being lost).

#### `dashboard/src/pages/Events.tsx`
- **Event detail modal**: Added "Classification Result" card showing `classification_level` (color-coded badge: Restricted=red, Confidential=orange, Internal=yellow, Public=green) and `classification_score` as percentage. Only shows when score > 0.
- **Event list**: Added `event.title` display as an `<h4>` above the existing event info row.

#### `dashboard/src/lib/api.ts`
- **Event type**: Added `title?`, `classification_level?`, `classification?`, `classification_metadata?` fields.

### Bug fixes included in uncommitted changes
1. **`classification_level` was never persisted to MongoDB** - `create_event()` built `event_doc` without it. Fixed by adding `"classification_level": event.classification_level` to the doc.
2. **`classification_metadata` from processor was discarded** - `_merge_processed_event()` didn't handle it. Fixed by adding merge logic that also overrides `classification_level` from processor output.
3. **Confidence score showed "0%"** - Frontend condition `event.classification_score !== undefined && !== null` would show 0%. Fixed to `event.classification_score != null && event.classification_score > 0`.

### What's NOT yet done
- These changes are **not committed** yet. They've been reviewed and the dashboard builds cleanly.
- The docker containers (manager, dashboard) have **not been rebuilt** with these changes. To apply:
  ```bash
  docker compose build manager dashboard
  docker compose up -d manager dashboard
  ```

---

## 6. Recent Commit History & Trajectory

The project has been actively evolving toward **classification-aware blocking**:

```
519d0b2 fix: add AddDouble method to JsonBuilder for classification_score
a892a97 feat: agent sends classification data with USB transfer events
e16de53 feat: add alerts persistence, event titles, and classification data support
0b60bac fix: remove duplicate /api/v1 prefix in classification API call
622972c fix: remove PowerShell backtick causing syntax error
3d16570 fix: make ExtractJsonValue public for classification API access
93677d6 feat: add real-time classification-based blocking and fix USB alert bug
b7dae61 feat: Add classification-aware policy support to dashboard
8bcca70 feat: Add production-grade classification system with dynamic rules and policy integration
```

**Direction**: Making the Windows C++ agent classify files before USB transfers, send classification data to the server, and have the server's policy engine decide whether to block/alert/quarantine in real-time.

---

## 7. Docker Commands Reference

```bash
# View running containers
docker ps

# Rebuild and restart specific services
docker compose build manager dashboard
docker compose up -d manager dashboard

# View logs
docker logs cybersentinel-manager --tail 100 -f
docker logs cybersentinel-dashboard --tail 100 -f
docker logs cybersentinel-celery-worker --tail 50

# Services in docker-compose.yml:
# postgres, mongodb, redis, opensearch, manager, celery-worker, celery-beat, dashboard
```

---

## 8. Build & Dev Commands

```bash
# Dashboard
cd dashboard && npm install && npm run build   # Production build
cd dashboard && npm run dev                     # Dev server

# Server (Python)
cd server && pip install -r requirements.txt
cd server && uvicorn app.main:app --host 0.0.0.0 --port 55000

# Python syntax check
python3 -c "import py_compile; py_compile.compile('server/app/api/v1/events.py', doraise=True)"
```

---

## 9. Conventions & Patterns

- **Event creation flow**: Agent POSTs to `/api/v1/events/` with `EventCreate` model -> `event_processor.process_event()` runs the 6-stage pipeline -> result merged into `event_doc` -> stored in MongoDB `dlp_events`.
- **DLPEvent model** (`events.py:46`): The response model for GET endpoints. Has `class Config: extra = "allow"` so extra MongoDB fields pass through.
- **Frontend types**: `Event` type in `dashboard/src/lib/api.ts` must match `DLPEvent` fields.
- **Classification data flows two ways**:
  1. **Agent-provided**: `EventCreate.classification_level`, `classification_score`, `classification_labels` (agent already classified locally)
  2. **Server-classified**: `event_processor.py` runs `ClassificationEngine` and sets `classification_metadata` on processed event, which `_merge_processed_event()` copies to `event_doc`
- **Policy bundle**: Agents fetch policies via `GET /api/v1/agents/{id}/policy` and enforce locally (blocking) + report back.
- **Tailwind classes**: Dashboard uses gradient backgrounds for sections (purple-50/indigo-50 for classification, gray-50 for labels).
- **Commit style**: `feat:`, `fix:`, `docs:` prefixes. Short imperative descriptions.

---

## 10. Known Issues & Watch-outs

- **Celery worker** shows as `unhealthy` in docker ps - may need investigation if background tasks (Google Drive polling) aren't running.
- **`datetime.utcnow()`** is used in `create_event()` (line 124) - this is deprecated in Python 3.12+, should eventually be `datetime.now(timezone.utc)`.
- **Event deduplication** is by `event.event_id` - agents must generate unique IDs.
- **MongoDB `_id` field** is stripped when returning events (line 419) but not when returning single events via `get_event()` (line 500-501) - the `DLPEvent` model's `extra = "allow"` handles it but it's inconsistent.
- **Large Events.tsx** (~1100 lines) - the page handles endpoint, OneDrive, and Google Drive events with different display logic.
