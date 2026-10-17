# Import the bootstrap into the blank GitHub repository

The archive contains source files only. It does **not** include `.git` metadata,
commits, an authentication token or changes pushed to your GitHub account.

The destination repository is:

https://github.com/zackboll/ada-gnatdoc-enhancer

Because the destination was empty when the archive was produced, you can choose
between a direct bootstrap commit and the established feature-branch/PR model.

## One initial main commit

Extract the archive, enter the extracted directory, then:

```sh
git init -b main
git remote add origin https://github.com/zackboll/ada-gnatdoc-enhancer.git
git add -A
git commit -m "GDE-001: bootstrap source-verified GNATdoc enhancer"
git push -u origin main
```

Review the changes before pushing. If GitHub main has acquired a commit, fetch
and reconcile rather than force-pushing over it.

## Feature-branch PR instead

To preserve an independent PR review of the substantive bootstrap:

```sh
git init -b main
git remote add origin https://github.com/zackboll/ada-gnatdoc-enhancer.git
git add LICENSE .gitignore .gitattributes
git commit -m "chore: seed empty repository"
git push -u origin main
git switch -c feature/001-bootstrap-enhancer
git add -A
git commit -m "GDE-001: bootstrap reusable GNATdoc enhancer toolkit"
git push -u origin feature/001-bootstrap-enhancer
gh pr create --base main --head feature/001-bootstrap-enhancer \
  --title "GDE-001: Bootstrap reusable GNATdoc enhancement toolkit" \
  --body "Offline CLI, four synthetic reference profiles, source-backed enhancements, mutation tests and packaging. Consumer migrations and full-site parity are deferred."
```

Do not run both sequences. Neither sequence is executed by the ZIP creation.
Do not reinitialize or replace a repository that is no longer empty.
