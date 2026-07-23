# Production Runbook v1.0

## A. New project
1. Create project identity and immutable intake snapshot.
2. Register every file; deduplicate by hash; assign disposition and review-depth status.
3. Create scope Questions, Evidence Register, critical gates and blocked-output list.
4. Build workpapers from high-materiality evidence first.
5. Produce specialist reports only where the workpaper supports a professional conclusion.
6. Produce the integrated report from specialist parents, not directly from loose files.
7. Produce the IC memo from the integrated report.
8. Separate Reader and Control packages.
9. Run publication, non-regression and clean-room portability acceptance.

## B. Incremental evidence
1. Register only new or changed sources.
2. Update affected Evidence, Questions, workpapers and reports through an impact map.
3. Do not regenerate unaffected products.
4. Promote a restricted output only when its explicit evidence gate passes.
5. Archive the previous Current package and update Last-success.

## C. Formal issue
Named product owner and relevant finance, engineering/HSE and legal reviewers must sign the applicable products. AI generation and system QA do not replace professional reliance.

## Contract validation

```bash
intellidue validate-state current_project_state.json
intellidue validate-lock release_lock.json
intellidue validate-validation package_validation.json
intellidue validate-contract \
  --state current_project_state.json \
  --lock release_lock.json \
  --validation package_validation.json
```

A non-zero exit code means at least one typed validation issue was returned. Do not promote or publish a package when any contract issue remains.
