#!/bin/bash
# S8 boot gate: verify the model digest before llama-server ever loads it.
set -eu
: "${ZONE3_MODEL_PATH:?ZONE3_MODEL_PATH must be set}"
: "${ZONE3_MODEL_MD5:?ZONE3_MODEL_MD5 must be set}"

actual="$(md5sum "$ZONE3_MODEL_PATH" | cut -d' ' -f1)"
if [ "$actual" != "$ZONE3_MODEL_MD5" ]; then
  echo "P3_ZONE3_BOOT_FAIL md5 mismatch: got $actual expected $ZONE3_MODEL_MD5" >&2
  exit 1
fi
echo "P3_ZONE3_BOOT_OK md5 $actual matches published digest"
exec "$@"
