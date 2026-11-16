# {{AGENT_NAME}} — rollout and operations

> Created {{DATE}} by agent-forge. Remove every `TODO(forge)` marker when complete.

## Staged rollout

| Stage | What happens | Exit criteria | Owner |
|---|---|---|---|
| 1. Shadow | runs on real inputs; nobody acts on its output | TODO(forge) | |
| 2. Assistive | a human approves every action | | |
| 3. Partial autonomy | low-risk actions run alone | | |
| 4. Wider rollout | more users or action types | | |

## Testing changes before release

TODO(forge): how changes are tested against cases built from real usage before they ship.

## Operating loop

TODO(forge): how often traces are sampled and labelled; how failures become eval cases; what
happens on a model or provider change; cost and latency review cadence; who owns this.

## Runbook

### Disable the agent

TODO(forge): the kill switch and how to use it.

### Roll back a prompt, model or tool change

TODO(forge)

### Rotate credentials

TODO(forge)

### Incident response

TODO(forge): who is told, what is logged, how affected users are handled.
