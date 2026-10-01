# Official-run preflight

## Completed

- Recovered the team Git history into the `result/` checkout, preserving teammate work.
- Committed and pushed the generic mandates with filenames matching the configured seats.
- Prepared the complete four-stage dispatch; no official implementation message has been sent.
- Verified the launch wrapper with shell syntax checking and BAND's runtime dry-run.
  The probe started, initialized, authenticated and stopped OpenCode successfully.
- Exclusivity, CPU affinity, niceness and startup memory checks are implemented in the wrapper.

## Runtime restoration blocker

BAND's bulk `detach` removed all local host-session records, including the parked
owned-runtime templates. The persistent remote identities and original room history
remain. The attempted non-mutating update of the coordinator's explicit `default`
template returned `parked owned-runtime template "default" not found`.

Automatic approval review rejected the requested `agent create` restoration because
it could create another persistent agent and specified the previous `approve-all`
policy. No restoration was performed by that rejected command. A subsequent dry-run
omitting approval changes passed, with `created: null`.

Before official dispatch, restore/recreate the four owned runtimes using an explicitly
approved policy, verify their identities and generic mandate links, and create the
fresh official room. If replacement identities are necessary, update mandate names
and roster documentation to match them before dispatch. Never represent a replacement
identity as the original.

## Product status

The Tablekeeper stage folders are placeholders. No completed product stage or official
room collaboration is claimed. The toy code and its earlier checks are separate practice
evidence and do not satisfy the Tablekeeper requirements.
