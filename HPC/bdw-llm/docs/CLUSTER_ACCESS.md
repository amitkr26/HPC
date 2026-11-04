# PARAM Rudra — cluster access from any machine

**Connection:** `paramrudra.cdacdelhi.in` port **4422** (SSH), user
**`3ioip3lt`**, SLURM account `tutor`. Login node has internet; compute nodes
do not. Wall limit for jobs: 15 min (see `PHASE2_7B_BLUEPRINT.md` §2).

## Quick start: passwordless via SSH key (recommended)

The cluster already has an ed25519 **public** key installed in
`~/.ssh/authorized_keys`; its private counterpart lives with the automation
workstation (and in the `paramrudra-access/` folder delivered to the
student). Once the private key + config are on your machine:

```bash
ssh paramrudra "echo OK; hostname"    # no password, no captcha
scp file.txt paramrudra:~/            # port comes from the config alias
```

### `~/.ssh/config` block

```ssh-config
Host paramrudra
    HostName paramrudra.cdacdelhi.in
    Port 4422
    User 3ioip3lt
    IdentityFile ~/.ssh/pr_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
```

### Install steps

**Windows (PowerShell):**

```powershell
mkdir $env:USERPROFILE\.ssh -Force
# copy pr_ed25519 and pr_ed25519.pub from the access package into $env:USERPROFILE\.ssh\
notepad $env:USERPROFILE\.ssh\config         # paste/merge the block above
type known_hosts >> $env:USERPROFILE\.ssh\known_hosts   # optional: pins host keys
icacls $env:USERPROFILE\.ssh\pr_ed25519 /inheritance:r /grant "$env:USERNAME`:R"
ssh paramrudra "echo OK; hostname"
```

**macOS / Linux:**

```bash
mkdir -p ~/.ssh
cp pr_ed25519 pr_ed25519.pub ~/.ssh/
cat config >> ~/.ssh/config                  # or merge manually
cat known_hosts >> ~/.ssh/known_hosts
chmod 700 ~/.ssh && chmod 600 ~/.ssh/pr_ed25519 ~/.ssh/config ~/.ssh/known_hosts
ssh paramrudra "echo OK; hostname"
```

Notes:

- Windows OpenSSH refuses private keys with loose ACLs — the `icacls` line
  is mandatory; on macOS/Linux `chmod 600` is mandatory.
- Pinned host keys (`known_hosts`): RSA `SHA256:n8Dz5bW5BNZ5xrcO9V7hLwtP7iZPtwE/3K1hy99RPaQ`,
  ECDSA `SHA256:Dz1vskzdMU5xAw0XfrwTdxw8cpDWHhRjdH2nNtcnxrw`,
  ED25519 `SHA256:6/nnQHtZ1iCueshcaCdbRwlxoOQKUTEfjIJ0f5GeXhA`.

### Optional: add your own laptop key

```bash
ssh-keygen -t ed25519 -f ~/.ssh/my_paramrudra -C "my-laptop"
ssh paramrudra "cat ~/.ssh/my_paramrudra.pub >> ~/.ssh/authorized_keys"
```

Add without removing the existing key (the workstation automation depends
on it); remove old keys only when you are sure nothing uses them.

## Fallback: password + captcha login

Without a key, SSH uses keyboard-interactive:

```bash
ssh -p 4422 3ioip3lt@paramrudra.cdacdelhi.in
```

1. **Captcha** — ASCII-art prompt like `( A | B | C )`: type only the
   letters/digits shown between the pipes (e.g. `ABC`).
2. **Password** — your PARAM Rudra password.
3. **OTP** — only if a code is requested (Google Authenticator or one of
   the saved emergency scratch codes).

The automation helper (`pr_session.py`) implements exactly this flow and
always tries key auth first.

## After login

```bash
cd ~/bdw-llm
source venv/bin/activate          # Phase-1 venv
# or for Phase-2 work:
source venv_p2/bin/activate
squeue -u 3ioip3lt                # job status
```

Key locations: workspace `~/bdw-llm`, dataset `data/bdw_sft.jsonl`,
final Phase-2 adapter `lora_snap/final`, logs `~/bdw-llm-*.out`,
secrets `secrets/supabase.env` (chmod 600 — never commit).

## Security

- The private key grants passwordless access — never commit it, never
  paste it into git-hosted files, share only via a secure channel.
- Host keys are pinned above; if SSH reports a changed host key, do NOT
  blindly accept — verify with the fingerprint table first.
