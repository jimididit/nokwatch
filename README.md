# Nokwatch Documentation

You’re on the **docs** branch. This branch holds only the **documentation website** for [Nokwatch](https://github.com/jimididit/nokwatch) — the main app (Python, monitoring, etc.) is on the **main** branch.

The docs site is built with [Astro](https://astro.build) and [Tailwind CSS](https://tailwindcss.com). The published site is available at the project’s GitHub Pages URL (e.g. `https://<username>.github.io/<repo>/`).

## Running the docs site locally

```bash
cd docs
npm install
npm run dev
```

Then open [http://localhost:4321/nokwatch/](http://localhost:4321/nokwatch/) in your browser. The `/nokwatch` base path matches how the site is served on GitHub Pages.

## Building for production

```bash
cd docs
npm run build
```

The built output is in `docs/dist/`.

## Want the main app?

Switch to the default branch for the Nokwatch application (code, installation, and usage):

```bash
git checkout main
```

See the repository’s main [README on default branch](https://github.com/jimididit/nokwatch) for installation and usage.

## Publishing this site (maintainers)

To publish or redeploy the docs to GitHub Pages, see **[docs/GITHUB_PAGES.md](docs/GITHUB_PAGES.md)**.
