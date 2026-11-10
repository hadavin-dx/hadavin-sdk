#!/bin/bash
# runs "$@" with every cloud env var removed (prefixes AWS_ ANTHROPIC_ AZURE_ GOOGLE_ GCP_ VAULT_ OPENAI_ GEMINI_ CLOUDSDK_)
args=()
for v in $(env | cut -d= -f1 | grep -E '^(AWS_|ANTHROPIC_|AZURE_|GOOGLE_|GCP_|VAULT_|OPENAI_|GEMINI_|CLOUDSDK_)'); do args+=(-u "$v"); done
exec env "${args[@]}" "$@"
