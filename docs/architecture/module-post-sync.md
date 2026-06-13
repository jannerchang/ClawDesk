# Module post sync

ClawDesk modules can be bound to external posts so each module can update its own status thread/card independently.

This is useful when the workspace has multiple long-running modules, for example:

```text
Mattermost / Discord forum or channel
  ├── ClawDesk overview post
  ├── Mattermost deployment post
  ├── Hermes bridge post
  ├── LocalAgent bridge post
  └── Apple client post
```

Each module owns one or more external posts. When its status changes, it updates only the corresponding post instead of dumping all progress into one global channel.

## Data model

```text
module_post_bindings
  module_key
  module_label
  platform
  external_channel_id
  external_post_id
  sync_mode
  last_payload
  last_synced_at
```

`module_key` is stable and code-friendly, such as:

```text
mattermost-server
hermes-bridge
local-agent-bridge
apple-client
backend-api
```

`module_label` is display-friendly.

`sync_mode`:

```text
manual     → update only when explicitly triggered
on_change  → update when module state changes
scheduled  → update from periodic summary job
```

## API

Create a binding:

```http
POST /module-post-bindings
```

```json
{
  "module_key": "local-agent-bridge",
  "module_label": "LocalAgent Bridge",
  "platform": "mattermost",
  "external_channel_id": "channel-id",
  "external_post_id": "post-id",
  "sync_mode": "manual"
}
```

List bindings:

```http
GET /module-post-bindings
GET /module-post-bindings?module_key=local-agent-bridge
GET /module-post-bindings?platform=mattermost
```

Update binding metadata:

```http
PATCH /module-post-bindings/{binding_id}
```

```json
{
  "module_label": "LocalAgent Bridge v1",
  "sync_mode": "on_change"
}
```

Record a sync payload:

```http
POST /module-post-bindings/{binding_id}/sync
```

```json
{
  "title": "LocalAgent Bridge",
  "status": "green",
  "summary": "Bridge script and tests are passing.",
  "details": {
    "tests": "passed",
    "commit": "..."
  }
}
```

Delete binding:

```http
DELETE /module-post-bindings/{binding_id}
```

## Bridge behavior

This first version records the intended sync payload in ClawDesk. A later platform-specific bridge can read `last_payload` and update the external Mattermost/Discord post through the relevant API.

That separation is intentional:

```text
module code → ClawDesk binding/sync API → platform updater bridge → external post
```

The module only knows “my status changed”; the platform updater knows how to edit Mattermost or Discord posts.
