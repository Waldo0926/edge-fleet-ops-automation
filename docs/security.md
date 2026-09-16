# Security notes

The production scripts contained operational details that should never be published. This showcase version deliberately changes the security model:

- **No shared plaintext SSH password.** SSH keys and the user's OpenSSH configuration are used instead.
- **No disabled host-key checking in examples.** Operators should manage known hosts normally.
- **No production API endpoints, node IDs, locations or internal addressing.** Examples use reserved/documentation values.
- **No automatic disk formatting.** Disk repair/formatting logic is intentionally excluded.
- **Cleanup is dry-run first.** Deletion requires an explicit apply mode and only targets configured log roots.
- **No secrets in Git.** `.env` and runtime state are ignored.

Before adapting the project to a real environment, review least-privilege access, SSH key rotation, network ACLs, log retention and secret-management requirements.
