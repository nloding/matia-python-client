# Beyond the Sync: A Tour of the Matia API for Data Engineers

*Governance, masking, and compliance — via curl and our new Python client.*

If you've integrated with Matia before, you know the basic shape: point us at a source, point us at a destination, and we keep the data flowing. That part of the API — creating an integration, kicking off a sync, checking whether it succeeded — is exactly what you'd expect, and we cover it in the [full API reference](docs/reference/) if you want the details.

This post is about the parts of the API that get less attention but do a lot of the day-to-day work in a real data platform: controlling *what* actually gets replicated, tracking *who owns what*, and answering *who changed this* when something breaks at 2am. We'll walk through three capabilities in depth — schema/column config, tags, and audit logs — with both `curl` and our [Python client](https://github.com/nloding/matia-python-client) side by side. At the end, we'll round up everything else the API can do that we didn't have room for here.

This isn't a "getting started with REST APIs" post — we're assuming you've called an API before and can read a JSON payload. Let's get into it.

A quick note before we do: none of what follows requires touching the Matia UI. Everything is scriptable, which is the point. If your team already has an internal platform for provisioning data pipelines, enforcing PII policy, or shipping compliance reports, these endpoints are meant to be called *from* that platform, not to be a replacement for it.

## Setup

Every request needs an `x-api-key` header, and everything lives under `https://api.matia.io/v1`:

```bash
export MATIA_API_KEY="..."
curl https://api.matia.io/v1/integrations -H "x-api-key: $MATIA_API_KEY"
```

If you're in Python, our client wraps that once:

```python
from matia import MatiaClient

client = MatiaClient(api_key="...")
```

Everything below assumes one or the other is already set up.

## Controlling what actually syncs: schema and column config

Every integration replicates a source schema — but "replicate everything, as-is" is rarely what you actually want in production. Maybe there's an `internal_notes` table nobody downstream should see. Maybe there's an `email` column that needs to be hashed before it lands in your warehouse so it doesn't become a compliance headache. The schema config endpoints exist for exactly this: fine-grained, per-table and per-column control over what syncs and how.

Start by pulling the current config for an integration:

```bash
curl https://api.matia.io/v1/integrations/int_8f3a1b/schemas \
  -H "x-api-key: $MATIA_API_KEY"
```

```json
{
  "code": "OK",
  "data": {
    "schemas": {
      "public": {
        "enabled": true,
        "tables": {
          "customers": {
            "enabled": true,
            "syncMode": "incremental",
            "cursorField": "updated_at",
            "columns": {
              "id": { "enabled": true, "isPrimaryKey": true, "hashed": false },
              "email": { "enabled": true, "isPrimaryKey": false, "hashed": false }
            }
          },
          "internal_notes": { "enabled": true, "columns": {} }
        }
      }
    }
  }
}
```

Now let's disable that internal table entirely and hash the `email` column on the one we're keeping:

```bash
curl -X PATCH https://api.matia.io/v1/integrations/int_8f3a1b/schemas \
  -H "x-api-key: $MATIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schemas": {
      "public": {
        "enabled": true,
        "tables": {
          "customers": {
            "enabled": true,
            "columns": {
              "email": { "enabled": true, "hashed": true }
            }
          },
          "internal_notes": {
            "enabled": false,
            "columns": {}
          }
        }
      }
    }
  }'
```

In Python, this is the same two calls, but you get typed objects back instead of raw dicts — useful when you're writing a script that audits every integration's config, not just editing one by hand:

```python
integration = client.integrations.get("int_8f3a1b")
config = integration.get_schema_config()

customers = config.schemas["public"].tables["customers"]
print(customers.columns["email"].hashed)  # False, for now

integration.update_schema_config({
    "public": {
        "enabled": True,
        "tables": {
            "customers": {
                "enabled": True,
                "columns": {"email": {"enabled": True, "hashed": True}},
            },
            "internal_notes": {"enabled": False, "columns": {}},
        },
    },
})
```

Because this is a real API call and not a config file, it's easy to fold into a script that runs on a schedule — e.g., a nightly job that scans every Postgres integration for newly-added columns matching a PII naming pattern and hashes them automatically, instead of relying on someone remembering to do it in a UI.

It's also worth calling out what the `enabled` flag buys you beyond compliance: every disabled table or column is one the sync engine doesn't have to extract, transfer, or store at the destination. On a wide source table with a handful of columns anyone actually queries, that's a meaningful reduction in sync time and warehouse storage cost — not just a governance win, but an operational one.

## Tags: cataloging and governance that isn't a spreadsheet

Once you have more than a handful of integrations and assets, "who owns this, and why does it exist" stops being answerable from memory. Matia's tags let you attach arbitrary, structured metadata to any resource — an integration, a data asset, a monitor — and query by it later.

Creating a tag is a single call:

```bash
curl -X POST https://api.matia.io/v1/tags \
  -H "x-api-key: $MATIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pii",
    "owner": "usr_492",
    "description": "Resources that contain personally identifiable information"
  }'
```

```json
{ "code": "OK", "message": "Tag created", "data": { "id": "tag_c91f" } }
```

Attaching it to a resource is a second call, to the tag's `relation` endpoint:

```bash
curl -X POST https://api.matia.io/v1/tags/tag_c91f/relation \
  -H "x-api-key: $MATIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceId": "int_8f3a1b",
    "resourceType": "Integration",
    "taggedBy": "usr_492"
  }'
```

The Python client makes this feel like what it conceptually is — labeling something you already have a handle on:

```python
pii_tag = client.tags.create(
    "pii",
    "usr_492",
    description="Resources that contain personally identifiable information",
)

pii_tag.assign(resource_id="int_8f3a1b", resource_type="Integration", tagged_by="usr_492")
```

A pattern we like: pair this with the schema config workflow above. When your PII-scanning job hashes a column, have it also tag the integration `pii` and assign a `data-owner:<team>` tag pulled from your internal service catalog. Now "which integrations touch PII, and who's accountable for them" is a query against the API instead of a wiki page that's six months stale.

## Audit logs: answering "who did that" without digging through Slack

This one's currently in beta, but it's worth knowing about now if you're building anything compliance-adjacent: `GET /audit-logs` gives you a paginated, filterable feed of every meaningful action taken against your Matia account — who paused an integration, who edited a tag, who logged in and from where.

```bash
curl -G https://api.matia.io/v1/audit-logs \
  -H "x-api-key: $MATIA_API_KEY" \
  --data-urlencode "limit=50" \
  --data-urlencode "sortOrder=asc" \
  --data-urlencode "startAt=2026-07-01T00:00:00Z"
```

```json
{
  "code": "OK",
  "data": {
    "totalItems": 214,
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-07-14T16:20:00Z",
        "event": "Integration paused",
        "actor": { "type": "user", "email": "nloding@matia.io" },
        "context": {
          "ipAddress": "192.168.1.1",
          "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
        }
      }
    ]
  }
}
```

`limit`/`offset` handle pagination, `sortBy`/`sortOrder` control ordering (currently just by `timestamp`), and `startAt`/`endAt` let you window a query — handy for "give me everything since our last export" jobs. In Python, you get a page object directly, or a generator that walks every page for you:

```python
# One page
page = client.audit_logs.list(limit=50, sort_order="asc", start_at="2026-07-01T00:00:00Z")
for log in page.items:
    print(log.timestamp, log.event, log.actor.email)

# Every event since a checkpoint, regardless of how many pages that is
for log in client.audit_logs.iter_all(start_at=last_export_timestamp):
    ship_to_siem(log)
```

That second pattern is the one worth stealing: run it on a cron, track the last `timestamp` you saw, and you've got a lightweight compliance export pipeline without polling a UI or asking anyone for a CSV.

The `actor` and `context` on each event are what make this useful for more than record-keeping. `actor.type` distinguishes a human (`user`) from an automated action (`system`), and `actor.email` plus `context.ipAddress`/`userAgent` give you enough to answer "was this a person on our network, or something else" without opening a support ticket. If you're already forwarding logs from other systems into Splunk, Datadog, or a plain S3 bucket, treat this endpoint the same way: poll it on an interval, normalize the shape, and drop it in the same pipeline as everything else.

Because it's beta, expect the shape to evolve — right now you can only sort by `timestamp`, and there's no webhook/streaming variant yet, so polling is the only option. If you're building on it, loosely couple your integration to the exact field set so a future addition doesn't break you.

## The rest of the API, briefly

We picked three capabilities to go deep on because they come up constantly in day-to-day data engineering work and don't get as much attention as "connect a source." But they're not the whole API. Here's what else is available, covered in full in the [reference docs](docs/reference/) rather than here:

- **Assets** (`POST /assets`, `PATCH /assets/{id}`) — register and update metadata for a source or destination asset.
- **Integrations** (`GET /integrations`, `POST /integrations`, `GET`/`PATCH`/`DELETE /integrations/{id}`) — the core CRUD for integrations, including our chainable connector builder for Postgres and Google Analytics 4 sources (`client.integrations.postgres()...create()`).
- **Sync runs** (`POST /integrations/{id}/run`, `GET /integrations/{id}/runs/{runId}`) — trigger a sync on demand and check its status, useful for wiring Matia into an existing orchestrator (Airflow, Dagster, or even just cron) as a downstream or upstream step.
- **Table columns** (`GET /integrations/{id}/schemas/{schema}/tables/{table}/columns`) — introspect a single table's column-level config without pulling the entire schema tree.
- **Users** (`GET /users`) — list users, handy for resolving the `owner`/`taggedBy` IDs you'll see throughout the tags and audit log examples above.

## Try it

Everything in this post works identically whether you're hitting the API directly with `curl` or through our client:

```bash
pip install matia-client
# or
poetry add matia-client
```

```python
from matia import MatiaClient
client = MatiaClient(api_key="...")
```

Because it's just Python, it drops into whatever's already orchestrating your pipelines — no new infrastructure, no separate service to run. If you build something interesting with the governance or compliance endpoints above, we'd like to hear about it.
