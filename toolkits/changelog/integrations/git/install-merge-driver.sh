#!/usr/bin/env bash
set -euo pipefail

echo "EXPERIMENTAL: this source-only incubator script changes local Git configuration." >&2
echo "Review the driver command and repository profile before continuing." >&2

profile=${1:-photon-circus}
case "$profile" in
  *[!A-Za-z0-9._/-]*)
    echo "Profile references may contain only letters, digits, '.', '_', '/', and '-'." >&2
    exit 2
    ;;
esac

git rev-parse --show-toplevel >/dev/null
git config merge.ph-changelog.name "ph-changelog semantic CHANGELOG merge"
git config merge.ph-changelog.driver \
  "uv run --locked ph-changelog --profile $profile merge %O %A %B --output %A"

echo "Configured unsupported experimental merge driver 'ph-changelog' with profile '$profile'."
echo "Commit: CHANGELOG.md merge=ph-changelog"
