# Glovebox site

The public website for Glovebox, plus the workflow that builds the downloadable zip.

## Layout

```
public/            the site itself — deploy this folder to Vercel
  index.html
  site.css
  site.js
  catalog.json     copy of the tool list, shown read-only on the site
glovebox-src/       the actual Glovebox app (launchers, installer, local UI)
.github/workflows/release.yml   builds glovebox.zip and attaches it to a GitHub Release
```

## How the download works

The site never hosts the zip itself. The download buttons point at:

```
https://github.com/sillyjoshua/glovebox/releases/latest/download/glovebox.zip
```

GitHub always resolves `latest` to the newest release, so the link never needs to change. `site.js` also calls the GitHub API to show the current version and file size, and to grey out the buttons if no release exists yet.

## Publishing a new version

1. Make your changes inside `glovebox-src/`.
2. Commit and push.
3. Tag the commit and push the tag:
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. GitHub Actions zips `glovebox-src/` and attaches it to a new Release as `glovebox.zip`. Nothing on the site needs to change.

You can also trigger the workflow manually from the Actions tab (`workflow_dispatch`) if you want to rebuild without a new tag.

## Deploying the site to Vercel

1. Push this repo to GitHub.
2. In Vercel, "Add New Project" → import the repo.
3. Leave the settings on their defaults — `vercel.json` already tells Vercel to serve the `public/` folder with no build step.
4. Deploy. Vercel serves the static files directly; there's no server involved.

## Before you publish

- `sillyjoshua/glovebox` is hardcoded in `public/index.html` (download links) and `public/site.js` (`REPO` constant). Update both if you rename the repo or move it to another account.
- Push at least one `vX.Y.Z` tag before sharing the site, or the download buttons will show as unavailable.
