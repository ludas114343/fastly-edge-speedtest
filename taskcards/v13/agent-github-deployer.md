# Task Card: agent-github-deployer (V13)

- Role: agent-github-deployer
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - Synchronization of all 13 workflow files under .github/workflows/ to remote main:
    1. .github/workflows/deploy-supabase.yml
    2. .github/workflows/deploy-wasmer.yml
    3. .github/workflows/deploy-northflank.yml
    4. .github/workflows/deploy-cloudflare.yml
    5. .github/workflows/deploy-fastly.yml
    6. .github/workflows/deploy-netlify.yml
    7. .github/workflows/deploy-edgeone.yml
    8. .github/workflows/discover-candidates.yml
    9. .github/workflows/smoke-test.yml
    10. .github/workflows/optimize-three-carriers.yml
    11. .github/workflows/publish-subscriptions.yml
    12. .github/workflows/external-blackbox-audit.yml
    13. .github/workflows/watchdog.yml
  - Verification that workflows are active and committed to default branch (main).
  - Clean git commit and push to remote repository (https://github.com/ludas114343/fastly-edge-speedtest.git).

## Mandate & Scope
1. Verify syntax and configuration of all 13 GitHub Actions workflow files.
2. Avoid top-of-the-hour cron schedules (e.g. use non-round minutes like 23 */4 * * *).
3. Ensure workflow dispatch inputs and secret requirements are cleanly handled.
4. Push all changes to remote default branch so remote actions can run.
5. Record full 40-character remote commit SHA.
6. Zero em-dash (\u2014) and zero en-dash (\u2013).
