# Publishing the docs site on GitHub Pages

This guide explains how to publish the Nokwatch documentation site as a GitHub Pages site. The **docs** folder and the deploy workflow exist **only on the `docs` branch**; the main branch does not contain them.

## How it works

- **Source:** The Astro site lives in the `docs/` folder on the **docs** branch (main has no `docs/` folder).
- **Workflow:** `.github/workflows/deploy-docs.yml` also lives only on the **docs** branch. It runs when you push to **docs** or trigger it manually.
- **Build:** The workflow checks out the **docs** branch, runs `npm install` and `npm run build` in `docs/`, and publishes the built output to the **gh-pages** branch.
- **GitHub Pages:** You configure GitHub Pages to serve from the **gh-pages** branch so the site is available at `https://jimididit.github.io/<repo>/`.

## 1. Push the docs branch and run the workflow

1. Ensure all docs source and the workflow are on the **docs** branch (they are not on main).
2. Push the **docs** branch to GitHub:  
   `git push -u origin docs`
3. The "Deploy Docs" workflow will run on that push and create/update the **gh-pages** branch with the built site.
4. You can also run it manually: **Actions** → **Deploy Docs** → **Run workflow** (choose branch **docs**).

## 2. Configure GitHub Pages

1. Open your repo on GitHub.
2. Go to **Settings** → **Pages** (under "Code and automation").
3. Under **Build and deployment**:
   - **Source:** select **Deploy from a branch**.
   - **Branch:** choose **gh-pages** (the branch the workflow publishes to).
   - **Folder:** select **/ (root)**.
4. Click **Save**.

If **gh-pages** does not exist yet, run the "Deploy Docs" workflow once (push to **docs** or trigger it manually). After it completes, **gh-pages** will appear; then set **Branch** to **gh-pages** and **Folder** to **/ (root)**.

## 3. View the site

After the workflow has run and Pages is configured, the site will be available at your project Pages URL (e.g. `https://jimididit.github.io/<repo>/`). It may take a minute or two after the first deploy. Later pushes to the **docs** branch will redeploy automatically.

## 4. Optional: Add a `package-lock.json` in docs

For faster and more reliable CI installs, generate a lockfile in `docs/`:

```bash
cd docs
npm install
```

Commit `docs/package-lock.json`. The workflow will use `npm ci` when the lockfile is present.

## Troubleshooting

- **Site is 404:** Ensure **Settings → Pages** uses branch **gh-pages** and folder **/ (root)**. Wait a few minutes after the first deploy.
- **Workflow fails:** Check the "Deploy Docs" run in the **Actions** tab. Common issues: Node/npm version, or missing `docs/package.json` / build errors. Fix and push to **docs** again.
- **Wrong base path:** The site is built with `base: '/nokwatch'` in `docs/astro.config.mjs`. If your repo name or GitHub username changes, update `base` and redeploy.
