#!/usr/bin/env bash
# Checks this machine has everything the repo needs. Safe to re-run.
# Prints PASS or FAIL (with the fix) per check, and exits 1 if anything failed.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

failed=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n      fix: %s\n' "$1" "$2"; failed=1; }
has() { command -v "$1" >/dev/null 2>&1; }

# GitHub: logged in, and allowed to push branches and create/edit PRs on this repo.
if ! has gh; then
  fail "gh installed" "brew install gh"
elif ! gh auth status >/dev/null 2>&1; then
  fail "gh logged in" "gh auth login --scopes repo,workflow"
else
  # Classic OAuth tokens list scopes; fine-grained tokens don't, so only check when listed.
  scopes=$(gh auth status 2>&1 | grep -i 'token scopes' || true)
  if [[ -n $scopes && ( $scopes != *"'repo'"* || $scopes != *"'workflow'"* ) ]]; then
    fail "gh token scopes (need repo, workflow)" "gh auth refresh --scopes repo,workflow"
  else
    pass "gh logged in as $(gh api user -q .login)"
  fi
  if ! git remote get-url origin >/dev/null 2>&1; then
    fail "origin remote" "git remote add origin https://github.com/OWNER/REPO.git"
  else
    perm=$(gh repo view --json viewerPermission -q .viewerPermission 2>/dev/null)
    case $perm in
      ADMIN | MAINTAIN | WRITE) pass "write access to repo ($perm)" ;;
      *) fail "write access to repo (have: ${perm:-none})" \
        "repo owner runs: gh api -X PUT repos/OWNER/REPO/collaborators/YOUR_LOGIN -f permission=push" ;;
    esac
  fi
fi

if [[ -n $(git config user.name) && -n $(git config user.email) ]]; then
  pass "git identity ($(git config user.name) <$(git config user.email)>)"
else
  fail "git identity" "git config --global user.name 'Your Name' && git config --global user.email you@example.com"
fi

if ! has uv; then
  fail "uv installed" "brew install uv"
elif uv python find '>=3.12' >/dev/null 2>&1; then
  pass "Python 3.12+ ($(uv python find '>=3.12'))"
else
  fail "Python 3.12+" "uv python install 3.12"
fi

if ! has aws; then
  fail "aws CLI installed" "brew install awscli"
elif ! arn=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null); then
  fail "AWS credentials" "aws configure sso && aws sso login, or export the sandbox credentials"
else
  pass "AWS credentials (${arn##*/})"
  region=${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null)}}
  if [[ -z $region ]]; then
    fail "AWS region" "aws configure set region us-east-1"
  elif aws bedrock list-foundation-models --region "$region" --query 'length(modelSummaries)' >/dev/null 2>&1; then
    pass "Bedrock reachable in $region"
  else
    fail "Bedrock reachable in $region" "check the sandbox IAM role allows bedrock:ListFoundationModels"
  fi
fi

if ! has pre-commit; then
  fail "pre-commit installed" "uv tool install pre-commit"
elif pre-commit install >/dev/null; then
  pass "pre-commit hooks installed"
else
  fail "pre-commit hooks" "pre-commit install"
fi

if [[ -f .claude/skills/setup/SKILL.md ]]; then
  pass "Claude skills linked to .agents/skills"
else
  fail "Claude skills link" "ln -sfn ../.agents/skills .claude/skills"
fi

exit $failed
