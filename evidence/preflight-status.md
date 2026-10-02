# Official-run preflight

## Completed

- Recovered the team Git history into the `result/` checkout, preserving teammate work.
- Committed and pushed the generic mandates with filenames matching the configured seats.
- Prepared the complete four-stage dispatch; no official implementation message has been sent.
- Verified the launch wrapper with shell syntax checking and BAND's runtime dry-run.
  The probe started, initialized, authenticated and stopped OpenCode successfully.
- Exclusivity, CPU affinity, niceness and startup memory checks are implemented in the wrapper.

## Runtime restoration history

BAND's bulk `detach` removed all local host-session records, including the parked
owned-runtime templates. The persistent remote identities and original room history
remain. The attempted non-mutating update of the coordinator's explicit `default`
template returned `parked owned-runtime template "default" not found`.

Automatic approval review rejected the requested `agent create` restoration because
it could create another persistent agent and specified the previous `approve-all`
policy. No restoration was performed by that rejected command. A subsequent dry-run
omitting approval changes passed, with `created: null`.

The owner subsequently explicitly approved restoration/recreation with the previous
automatic execution policy. BAND refused creation under the original local scopes.
The following distinct replacement owned runtimes were created successfully:

| Seat | Persistent ID | Mandate |
| --- | --- | --- |
| LEGION Lead | b4dcdced-cd0b-4c72-bdfa-290878f3d915 | legion-lead.md |
| LEGION Builder | de448aea-1817-4645-9660-64c68bee6c4b | legion-builder.md |
| LEGION Checker | deb77165-2402-464c-8684-ef4c11062720 | legion-checker.md |
| LEGION UX | 79e5da9b-dc9c-4e36-a716-78a69fad540f | legion-ux.md |

Each uses the low-resource wrapper, OpenCode ACP, `opencode/big-pickle`, inherited
authentication, the owner's approved automatic execution policy, and its linked
generic mandate. The fresh room ID is `ee44a58f-9400-44ac-bb1f-21570fbea358`.
The initial room creation reported an add-participant response decoding error;
recovery uses this same room rather than creating another.

## Product status

The Tablekeeper stage folders are placeholders. No completed product stage or official
room collaboration is claimed. The toy code and its earlier checks are separate practice
evidence and do not satisfy the Tablekeeper requirements.
