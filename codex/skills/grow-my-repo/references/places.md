# Places to show a repository

Checked 2026-10-10. Awesome lists are covered by the submit-awesome skill.

## How to read this

- An entry reads: **name** `[verdict, who]`, what it fits, the route with the URL where one submits, the deciding
  rule in the place's own words, and the cost. Each group runs most useful first and ends with a closed list, kept
  so nobody rechecks those places.
- Verdict is `worth it` or `situational`. Who is `agent` when a pull request, a form or a publish command is enough,
  `owner` when the place needs the maintainer's own voice, identity, account or money, `automatic` when the place
  indexes repos by itself, and `someone else` when self-nomination is barred.
- Numbers (stars, members, prices) are as read on the check date. Floors move: recheck a floor before relying on it.

## GitHub itself

### On the repo and the profile

- **Repository topics** `[worth it, agent]` Any repo. Route: About box, gear icon, Topics. Rule: "Add no more than 20 topics." A topic page lists repos by stars, so a narrow topic is where a small repo shows; a topic no public repo uses has no page. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics
- **About box** `[worth it, agent]` Any repo. Route: the About box gear icon: description, topics, website. Rule: "only the repository name, description, and topics are searched" unless the searcher adds `in:readme`. The website link is `nofollow`: it sends visitors, not search ranking. https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories
- **Releases and the releases feed** `[worth it, agent]` Any repo that ships versions. Route: publish GitHub Releases with notes, not bare tags; each repo then serves `https://github.com/<owner>/<repo>/releases.atom`. Watchers can follow releases only. https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- **Social preview image** `[worth it, owner or agent with a browser]` Any public repo. Route: Settings, Social preview. Rule: "PNG, JPG, or GIF file under 1 MB", "1280 by 640 pixels for best display". Without one a shared link shows the owner's avatar. Private repos have no upload. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview
- **Profile README and pins** `[worth it, agent drafts, owner picks]` The whole portfolio. Route: a public repo named like the username with a root `README.md`; pins from the profile page. Rule: "Select up to six repositories and gists, combined." https://docs.github.com/en/account-and-profile/how-tos/profile-customization/pinning-items-to-your-profile
- **`good first issue` and the /contribute page** `[worth it, agent]` Repos that want contributors. Route: label real small issues `good first issue` and `help wanted`; they fill `github.com/<owner>/<repo>/contribute`. Rule: "Adding the good first issue label can increase the likelihood that your issues are surfaced." https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/encouraging-helpful-contributions-to-your-project-with-labels
- **Community Standards checklist** `[worth it, agent]` Every public repo. Route: `github.com/<owner>/<repo>/community`, add each missing file. Rule: issue templates count only with "valid `name:` and `about:` keys" (`.md`) or "valid `name:` and `description:` keys" (`.yml` forms). Several programmes read the same files. https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories
- **Default community health files** `[worth it, agent after the owner's yes]` Every repo of an account at once. Route: a public repo named `.github` with CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, SUPPORT, FUNDING.yml and issue templates. Rule: "The `.github` repository must be **public**."; "You cannot create a default license file." https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
- **SECURITY.md** `[worth it, agent]` Every public repo. Route: commit it to the root, `docs/` or `.github/`. Rule: it should hold "information about supported versions of your project and how to report a vulnerability." Scorecard, the Best Practices badge and some plugin lists check for it. https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository
- **GitHub Sponsors and FUNDING.yml** `[worth it, owner]` Any repo. Route: enrol in Sponsors, then `.github/FUNDING.yml`. Rule: personal sponsorships carry no GitHub fee; FUNDING.yml takes one username per platform and "up to four custom URLs". https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository
- **GitHub Pages docs site** `[worth it, agent]` Any repo with docs. Route: a Pages workflow, URL in the About box. Rule: Pages "is not intended for or allowed to be used as a free web-hosting service to run your online business". Limits: 1 GB site, 100 GB a month soft bandwidth. https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- **CITATION.cff** `[situational, agent]` Repos researchers or journalists might cite. Route: `CITATION.cff` at the root of the default branch. Rule: "a link is automatically added to the repository landing page in the right sidebar, with the label 'Cite this repository.'" Zenodo reads the same file. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files
- **Discussions** `[situational, agent]` Apps whose users ask questions. Route: Settings, Features. An empty forum helps nobody. https://docs.github.com/en/discussions/quickstart
- **"Open in Codespaces" badge** `[situational, agent]` Libraries, CLIs and dev tools a visitor can try in a browser. Route: `.devcontainer/devcontainer.json` and a badge linking `https://codespaces.new/<owner>/<repo>`. Rule: "Compute usage is charged to the account that owns the codespace", so it costs the maintainer nothing. https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/setting-up-your-repository/facilitating-quick-creation-and-resumption-of-codespaces
- **gh CLI extension** `[situational, agent]` Only a CLI shipped as a gh extension. Route: name the repo `gh-<name>` and add the topic `gh-extension`. https://docs.github.com/en/github-cli/github-cli/creating-github-cli-extensions
- **Template repository** `[situational, agent]` Only a real starter kit. Route: Settings, tick Template repository; searchers filter with `template:true`. There is no gallery. https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository

### Programmes run by GitHub

- **Open Source Friday** `[worth it, owner]` Repos with 100+ stars that want contributors. Route: the guest invite issue at https://github.com/githubevents/open-source-friday/issues/new?template=osf-guest-invite.yml Rule: "Have a code of conduct, license and contributing guide in place."; "Have a minimum of 100 stars and be hosted on GitHub." The maintainer appears on the stream. https://raw.githubusercontent.com/githubevents/open-source-friday/main/admin/project-criteria.md
- **GitHub Trending** `[situational, nothing to submit]` Lists per period, per language (`/trending/go`) and per spoken language (`?spoken_language_code=es`). No formula is published. On small languages the daily floor is a handful of stars, so a launch whose stars land on one day can reach a list. Rule: the Acceptable Use Policies forbid "rank abuse, such as automated starring or following".
- **github/explore topics and collections** `[situational, agent for topics, someone else for collections]` Route: a PR adding `topics/<slug>/index.md` or a line in `collections/<name>/index.md` at https://github.com/github/explore Rule: "These should be of general community interest, not self promotion."; "Do not post AI-generated content verbatim". A bot flags a collection PR from the repo's own owner as possible self-submission. https://raw.githubusercontent.com/github/explore/main/CONTRIBUTING.md
- **GitHub Stars** `[situational, someone else]` The maintainer. Rule: "Anyone can nominate anyone, but you can't nominate yourself." https://stars.github.com/nominate/
- **Maintainer Month (May)** `[situational, owner]` A maintainer story or event, added by issue at https://github.com/github/maintainermonth

### Contributor aggregators

- **Up For Grabs** `[worth it, agent]` Repos with a curated label of small tasks. Route: PR to branch `gh-pages` adding `_data/projects/<project>.yml` at https://github.com/up-for-grabs/up-for-grabs.net No star minimum; an idle PR is closed after two weeks.
- **CodeTriage** `[situational, agent]` Repos with a backlog of open issues. Route: https://www.codetriage.com/repos/new Subscribers get one open issue a day, so a repo with no open issues gains nothing.
- **goodfirstissue.dev** `[situational, agent]` Repos with 10+ contributors. Rule: "At least 3 open issues with beginner-friendly labels", "At least 10 contributors". https://github.com/DeepSourceCorp/good-first-issue

### Indexes and badges fed by GitHub data

- **OpenSSF Scorecard** `[worth it, agent]` Any public repo. Route: `ossf/scorecard-action` with `publish_results: true`, then the badge `https://api.scorecard.dev/projects/github.com/<owner>/<repo>/badge`. Rule: "The job should run on one of the Ubuntu hosted runners." The public weekly scan covers only the most critical projects, so a small repo gets a score page only by publishing its own. https://github.com/ossf/scorecard-action
- **OpenSSF Best Practices badge** `[worth it for flagships, agent]` Repos with tests and a security policy. Route: sign in with GitHub at https://www.bestpractices.dev/en Rule: projects "voluntarily self-certify, at no cost". A trust signal more than a traffic source.
- **Star History** `[situational, agent]` Any repo: the README chart is free at https://www.star-history.com/
- **OSS Insight collections** `[situational, agent]` PR editing `configs/collections/<id>.<name>.yml` at https://github.com/pingcap/ossinsight The existing collections hold large, well-known projects.
- **Trendshift** `[situational, automatic]` It records Trending daily, so a repo that reaches any Trending list gets a permanent page. https://trendshift.io/

### Closed

- GitHub Release Radar: archived 2025-03-26.
- Hacktoberfest: "Pull requests and merge requests will no longer count toward Hacktoberfest rewards", so the topic brings nobody.
- GitHub wiki: "Search engines will only index wikis with 500 or more stars that you configure to prevent public editing." A Pages site is the indexed route.
- GitHub Community discussions: "don't post unsolicited links to your own projects or sites on other user's threads."
- Ecosyste.ms, deps.dev, Libraries.io, generated per-language rankings: automatic, nothing to submit.

## Registries and stores

Here publishing is the listing. Floors are noted per place; recheck them each quarter.

### Containers and charts

- **Docker Hub repository page** `[worth it, agent]` Every image. Route: description, up to three categories and the overview on the repository's General page; sync the overview from the README in CI with `peter-evans/dockerhub-description`. Rule: "The description can be a maximum of 100 characters." README sync is limited to 25,000 bytes. https://docs.docker.com/docker-hub/repos/manage/information/
- **GitHub Container Registry** `[worth it, agent]` Any repo that ships an image. Route: push from the release workflow with labels `org.opencontainers.image.source`, `.description` (max 512 characters) and `.licenses`, then set the package public once. Rule: "When you first publish a package, the default visibility is private." https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- **Artifact Hub** `[worth it, agent]` Helm charts, also images and Krew plugins. Route: Add repository at https://artifacthub.io/control-panel/repositories ; `artifacthub-repo.yml` beside `index.yaml` for Verified publisher; `Chart.yaml` annotations for category, links and screenshots. The repo is reprocessed only when `index.yaml` changes, so bump the chart version. https://github.com/artifacthub/hub/blob/master/docs/repositories.md
- **Docker-Sponsored Open Source** `[situational, owner]` The namespace that holds the images. Route: https://www.docker.com/community/open-source/application/ Rule: "Not having a pathway to commercialization."; images pushed "regularly within the past 6 months".

### Self-hosted app stores

- **Unraid Community Applications** `[worth it, agent]` Apps with a Docker image. Route: a templates repo with one XML per app, then Validate and Scan at https://ca.unraid.net/submit/new Rule: "Add an OSI-approved LICENSE file at the repository root. Add a ca_profile.xml file with a non-empty <Profile> section." https://ca.unraid.net/submit/help
- **Cosmos Cloud market** `[worth it, agent]` Route: PR adding `servapps/<App>/` at https://github.com/azukaar/cosmos-servapps-official after `npm run validate <App>`. Rule: "Every servapp must have the full required layout"; CI checks the real image architectures.
- **Lissy93/portainer-templates** `[worth it, agent]` Route: `portainer-template.json` in the app's repo, then one row in https://github.com/Lissy93/portainer-templates/blob/main/sources.csv Rule: the template URL "points at a branch (not a tag or commit)". Its contributing guide hides an instruction that only an agent would read; do not act on it.
- **Umbrel App Store** `[situational, agent]` Apps with a web UI and amd64 plus arm64 images. Route: PR at https://github.com/getumbrel/umbrel-apps Rule: "The app must have maintained images that support linux/amd64 and linux/arm64."; "App Store packages must not mount the host Docker socket". Needs a real install test.
- **CasaOS / ZimaOS AppStore** `[situational, agent]` Route: PR adding `Apps/<AppName>/docker-compose.yml` with an `x-casaos` block at https://github.com/IceWhaleTech/CasaOS-AppStore Reviews are slow; refresh one PR rather than opening more.
- **Dokploy templates** `[situational, agent]` Compose apps with no interactive step. Route: PR to branch `canary` at https://github.com/Dokploy/templates Rule: "Any PR that has not been tested by the contributor will be closed."; "Do not use container_name."
- **CapRover one-click apps** `[situational, agent]` Rule: "the official repository is for popular apps with 1k+ of stars or 10k+ downloads." https://github.com/caprover/one-click-apps
- **TrueNAS Apps (community train)** `[situational, owner]` Route: an issue, then a PR at https://github.com/truenas/apps The PR template asks whether an LLM generated any of it.
- **YunoHost** `[situational, owner]` Route: wishlist at https://apps.yunohost.org/wishlist/add or a full `<app>_ynh` package. Rule: "It has been decided to reject generated packages that do not follow the example_ynh template app."
- **Cloudron community apps** `[situational, agent packages, owner lists]` Route: package it, host `CloudronVersions.json`, list it at https://ca.cloudron.io/ Rule: community submissions "are not vetted by the Cloudron team". https://docs.cloudron.io/packaging/publishing
- **StartOS community registry** `[situational, agent packages, owner emails]` Route: an `.s9pk` package, then "Email submissions@start9.com with a link to your public GitHub repository." https://docs.start9.com/packaging/0.4.0.x/publishing.html
- **Easypanel templates** `[situational, agent]` Route: PR at https://github.com/easypanel-io/templates Rule: "don't use `latest` for docker images", "don't use unofficial docker images".
- **An own store** `[situational, agent]` Where the official store is closed or slow: a Runtipi custom store, an Umbrel community store or a ZimaOS third-party store, with its add-URL printed in the README. None gives discovery by itself.

### Managed hosting and deploy buttons

- **Railway templates** `[worth it, agent prepares, owner publishes]` Web apps with an image. Route: publish from a Railway workspace, add the Deploy on Railway button. Rule: "Templates receive a 15% kickback of the usage costs incurred by users deploying your template". https://docs.railway.com/templates/kickbacks.md
- **PikaPods** `[situational, agent]` Single-port web apps with an official image. Route: suggest at https://feedback.pikapods.com/ Rule: "Be a web application and use one HTTPS port only". The home page offers a revenue share with project authors.
- **Deploy to Render button** `[situational, agent]` Route: a `render.yaml` Blueprint and a button linking `https://render.com/deploy?repo=<repo URL>`. A button, no listing. https://render.com/docs/deploy-to-render

### Package managers and language registries

- **An own Homebrew tap** `[worth it, agent]` CLIs, macOS apps. Route: a public repo `homebrew-<name>`; goreleaser can push the formula on each release. No gate, no discovery by itself. https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap
- **npm** `[worth it, agent]` Route: a trusted publisher, then `npm publish` from GitHub Actions with `id-token: write`. Rule: "Trusted publishing requires npm CLI version 11.5.1 or later and Node version 22.14.0 or higher". https://docs.npmjs.com/trusted-publishers
- **PyPI** `[worth it, agent after the owner adds the publisher]` Route: a Trusted Publisher at https://pypi.org/manage/account/publishing/ then `pypa/gh-action-pypi-publish`. https://docs.pypi.org/trusted-publishers/
- **pkg.go.dev** `[worth it, automatic]` Tag a version and fetch it once through `proxy.golang.org`, or press Request on the module page. https://pkg.go.dev/about
- **AUR** `[worth it, agent]` CLIs and Linux desktop apps. Route: push `PKGBUILD` and `.SRCINFO` to `ssh://aur@aur.archlinux.org/<pkgbase>.git`; prebuilt binaries use the `-bin` suffix. Rule: "Please do not just submit and forget about packages!" Wire the version bump into the release workflow. https://wiki.archlinux.org/title/AUR_submission_guidelines
- **crates.io** `[situational, agent]` Rule: "a publish is generally permanent." https://doc.rust-lang.org/cargo/reference/publishing.html
- **Homebrew core and cask** `[situational, owner]` Rule: "at least 90 forks, 90 watchers or 225 stars for a self-submission by the repository owner"; repo at least 30 days old. AI: "You must answer all maintainer questions and pull request review comments yourself, without using AI/LLM."; AI use is disclosed in the PR. https://github.com/Homebrew/brew/blob/main/docs/Package-Acceptance-Policy.md
- **Scoop** `[situational, agent]` Main needs "at least 500 stars and 150 forks"; Extras takes GUI apps; an own bucket has no gate. https://github.com/ScoopInstaller/Scoop/wiki/Criteria-for-including-apps-in-the-main-bucket
- **winget** `[situational, owner]` Rule: "Packages submitted to the community repository must install without requiring user interaction." Needs the Microsoft CLA.
- **nixpkgs** `[situational, owner]` Rule: "Consider waiting for another user of your project to submit it instead." AI-assisted commits carry a mandatory `Assisted-by:` trailer.
- **Swift Package Index** `[situational, agent]` Swift repos with a root `Package.swift` and a semver tag. Route: the Add Package issue form. Rule: "There's also no quality threshold." https://swiftpackageindex.com/add-a-package
- **MacPorts, Krew, Ansible Galaxy, Terraform and OpenTofu registries, JSR, conda-forge** `[situational]` Each fits one kind of project only; read the route on the registry's own guide. OpenTofu takes providers only through its issue form UI.

### Mobile and desktop stores

- **Apple App Store** `[worth it, owner]` iOS and macOS apps. Route: App Store Connect and App Review. The developer programme is a yearly fee.
- **TestFlight public link** `[worth it, owner]` An iOS app before or beside its release. Rule: "you can invite up to 10,000 external testers per app". https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers/
- **App Store featuring nominations** `[worth it, owner]` Every app on the App Store, at launch or a significant update. Route: App Store Connect, Featuring, Nominations. Rule: "All apps and games are eligible for featuring consideration."; plan three weeks of lead time. https://developer.apple.com/app-store/getting-featured/
- **F-Droid** `[situational, owner]` Fully FLOSS Android apps that build from source. Rule: "All applications in the repository must be Free, Libre and Open Source Software". https://f-droid.org/docs/Inclusion_Policy/
- **Google Play** `[situational, owner]` Rule: new personal accounts "must run a closed test for their app with a minimum of 12 testers who have been opted in continuously for at least 14 days." One-time fee. https://support.google.com/googleplay/android-developer/answer/14151465
- **Obtainium app configs** `[situational, agent]` Android APKs released on GitHub. Rule: the source repo needs "at least 35" stars and "must be at least 4 months old". https://github.com/ImranR98/apps.obtainium.imranr.dev
- **Microsoft Store** `[situational, owner]` Windows apps with a signed offline installer. Rule: "silent install is required"; identity verification with "a government-issued ID and selfie".

### Ecosystem catalogues

- **HACS default repositories** `[worth it, agent from the owner's fork]` Home Assistant integrations, cards, themes. Rule: "Only the owner or a major contributor of a repository can submit"; the HACS action "must pass without any errors or ignores". The queue is months long. https://github.com/hacs/documentation/blob/main/source/docs/publish/include.md
- **Jellyfin plugin repositories** `[worth it, owner writes the PR text]` Plugins with their own `manifest.json`. Rule: "LLM output is expressly prohibited for any direct communication, including the following: issues or comments, feature requests or comments, pull request bodies or comments"; "Any primarily-LLM-developed projects should be clearly marked as such." https://jellyfin.org/docs/general/contributing/llm-policies
- **GitHub Marketplace (Actions)** `[worth it, owner ticks the box]` Route: Draft a release, tick "Publish this Action to the GitHub Marketplace". Rule: "Actions are published to GitHub Marketplace immediately and aren't reviewed by GitHub". https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace
- **VS Code Marketplace and Open VSX** `[worth it, agent after the owner signs once]` Route: `vsce publish` and `npx ovsx publish`. Open VSX reaches Cursor, Windsurf and VSCodium. Rule: "On December 1, 2026, global Personal Access Tokens (PATs) in Azure DevOps are retired."
- **Grafana community dashboards** `[worth it, owner]` Exporters and apps with Prometheus metrics. Rule: "you must export it using the Classic model."
- **Prometheus exporters page** `[situational, owner]` Route: reserve a port on the default port allocations wiki, then one line in the exporters doc. Rule: commits signed off under the DCO.
- **Home Assistant blueprints exchange** `[situational, owner]` Rule: "Each blueprint should be shared in its own topic in the forums." https://community.home-assistant.io/t/about-blueprints/253788
- **Node-RED, Raycast, Obsidian, Homebridge, Dev Container collections** `[situational]` Each fits only its own plugin type. Raycast: "Ensure you use `MIT` in the `license` field". Obsidian: submit through community.obsidian.md. Homebridge verification: "must not contain any analytics or calls that enable you to track the user."

### MCP registries

- **Official MCP Registry** `[worth it, agent]` Every MCP server, first of all. Route: `server.json`, then `mcp-publisher login github-oidc` and `mcp-publisher publish` from Actions. Rule: "With GitHub auth, your server name must start with io.github.your-username/". Several directories read from it. https://github.com/modelcontextprotocol/registry
- **Glama** `[worth it, agent]` Route: `glama.json` at the root, Add Server at https://glama.ai/mcp/servers The server must answer `initialize` and `tools/list` without real credentials.
- **mcpservers.org** `[worth it, agent]` Route: https://mcpservers.org/submit Rule: "Listings on mcpservers.org are free." "Review within 2 weeks."
- **MCP Market** `[worth it, agent]` Route: https://mcpmarket.com/submit, free queue. Rule: "Avg. 4-6 week listing time".
- **MCP.Directory** `[worth it, agent]` Route: https://mcp.directory/submit Rule: "We'll auto-pull metadata from GitHub and publish within 24 hours."
- **Docker MCP Catalog** `[situational, agent]` Servers with a Dockerfile and a permissive licence. Rule: "MIT or Apache 2 are great, GPL is not". https://github.com/docker/mcp-registry
- **GitHub MCP Registry** `[situational, owner emails]` After the Official Registry: "email partnerships@github.com and request for your server to be included." https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/
- **Smithery, ToolSDK, LobeHub** `[situational]` Read each guide; ToolSDK's asks the agent to star its repo, which is not done.

### Closed

- Coolify one-click services: "The service repository must have at least 1,000 GitHub stars".
- Runtipi official store: "no new applications will be accepted."
- Flathub: "Console softwares will not be accepted." and "AI tools or agents must not open or automate Flathub submission pull requests".
- IzzyOnDroid: "Vibe-coded apps will be rejected."
- PulseMCP: not accepting submissions; it reads the Official MCP Registry. mcp.so: paid only.
- Homepage (gethomepage) widgets: "homepage does not accept "AI-generated" PRs".
- Proxmox VE community scripts: "The official source repository must have at least 1,000 stars."
- Cloud vendor marketplaces (DigitalOcean, Vultr, Akamai, Hetzner, Scaleway, OVHcloud): vendor programmes for little discovery.

## Knowledge bases and indexes

They bring trust, citations and long-tail search more than launch traffic.

- **Zenodo** `[worth it, owner enables once, then automatic]` Repos someone might cite. Route: link GitHub at https://zenodo.org/account/settings/github/ toggle the repo on, publish a release. Rule: "Zenodo archives your repository and issues a new DOI each time you create a new GitHub release."; "If your repository also contains a .zenodo.json file, Zenodo will only use the .zenodo.json metadata and ignore the CITATION.cff entirely."
- **Software Heritage** `[worth it, agent in a browser]` Every public repo. Route: https://archive.softwareheritage.org/save/ or a webhook on releases. Gives a citable SWHID.
- **tldr-pages** `[situational, owner reviews]` CLIs maintained for a year. Rule: "Please ensure that the project has been maintained for at least a year"; "Pull requests suspected of being made in whole or in part through generative AI or machine translation software without human-review will be closed." Needs the CLA. https://github.com/tldr-pages/tldr/blob/main/CONTRIBUTING.md
- **Domain registries** `[worth it where they fit]` bio.tools and WorkflowHub for bioinformatics, Hugging Face datasets and Kaggle for data, Google Dataset Search through schema.org `Dataset` markup on a public page.
- **Context7 and DeepWiki** `[worth it, agent]` Repos with docs people code against. Context7: https://context7.com/add-library ("Anyone can add a public library"). DeepWiki: submit the repo URL on https://deepwiki.com/

### Closed

- Wikipedia: "Most topics need significant coverage in multiple reliable, independent, secondary sources." Editors with a conflict of interest are "strongly discouraged from editing affected articles directly".
- Wikidata: "Creating an item about yourself, your organisation, or your work is a form of self-promotion and is strongly discouraged."
- Codeberg mirrors: its terms bar "projects that mostly consist of code written by 'generative AI'-tools".

## Directories and launch sites

Free queues run for months, so join them the day a repo goes public. A pricing page that leads with a backlink or a domain-rating number marks a site nobody browses.

### Self-hosted and alternatives directories

- **selfh.st directory and Self-Host Weekly** `[worth it, agent prepares, owner answers the AI question]` Self-hosted apps. Route: https://selfh.st/submit/ Rule: "Newly launched projects will not be considered for the directory. Consider submitting them to be featured as a 'Project Launch' in Self-Host Weekly instead." The form requires an answer to "Does the project leverage AI to assist with development?". One curator reads every form.
- **AlternativeTo** `[worth it, agent on the owner's account]` Released apps with a known proprietary counterpart. Route: "Suggest new application". Rule: "Using user profiles to advertise products or software is not allowed."; no closed betas. The free queue is long; a small fee buys a review in days. https://alternativeto.net/faq/
- **LibHunt** `[worth it, agent]` Route: https://www.libhunt.com/repo/submit and https://selfhosted.libhunt.com/contribute Rule: "It monitors everything that's posted on Reddit, HackerNews & Dev.to", so ranking follows mentions.
- **selfh.st icons** `[worth it, agent]` Any self-hosted app with an official logo. Route: a "New Icon Request" discussion at https://github.com/selfhst/icons/discussions
- **opensourcealternative.to** `[situational, agent]` Route: https://opensourcealternative.to/submit with the proprietary rival named. Free waitlist of months, or a fee for 48 hours.
- **OpenAlternative** `[situational, agent]` Full applications with their own domain. Rule: "50+ stars on the repository", "250+ stars if the repository is less than 6 months old", "3 months at most since the last commit"; no CLIs, libraries, plugins or "GitHub-only projects". https://openalternative.co/submit
- **SaaSHub** `[situational, agent]` Products on their own domain with named competitors. Rule: rejects "Products using free subdomains". https://www.saashub.com/services/submit
- **SourceForge, FSF Free Software Directory, opensource.builders, selfhostyourself.com, nologin.tools** `[situational, agent]` Smaller catalogues; read each form before sending.

### Mac and terminal directories

- **MacUpdate** `[worth it, agent on a member account]` Signed, notarized macOS apps. Rule: "Do not include version numbers, subtitles, or promotional text." https://www.macupdate.com/help/submit-app
- **Mac Apps Library** `[worth it, agent]` Route: https://macappslibrary.com/submit Rule: "A standard listing is always free."
- **MacMenuBar.com** `[worth it, agent]` Menu bar apps only. https://macmenubar.com/submit-your-menu-bar-app/
- **MacNative** `[worth it, owner signs in]` Native macOS apps. Rejected: "Low-effort AI-generated apps." https://macnative.io/guidelines
- **Terminal Trove** `[worth it, agent]` CLI and TUI tools. Rule: "Please make sure the tool exists in the package repositories." https://terminaltrove.com/post/

### Launch boards

- **DevHunt** `[worth it, agent signed in with GitHub]` Developer tools. Rule: "Tools that are not for developers, NSFW tools, and services that sell fake engagement are not accepted." Free launches wait in a queue. https://devhunt.org/faq
- **Product Hunt** `[situational, owner]` One or two flagship launches a year with a visual demo. Rule: "you cannot ask people directly to upvote your product. Instead, ask them to visit and comment". https://www.producthunt.com/launch
- **Peerlist Launchpad** `[situational, owner]` Rule: "only individual profiles with a valid name and profile picture are allowed to launch projects."

### Maps of more places

- DevHunt "Where to promote", https://devhunt.org/promote, with route, catch and cost per entry.
- https://github.com/mmccaff/PlacesToPostYourStartup, the largest raw list, no rules per entry.

### Closed

- BetaList: "All submissions are paid."
- Free launch boards whose free tier requires a backlink, a badge or a months-long wait behind paid users, and sites that sell "dofollow" links: no measured benefit for an open-source repo.

## AI and agent tooling

- **Own Claude Code marketplace file** `[worth it, agent]` Repos with skills, an MCP server, hooks or commands. Route: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, `claude plugin validate .`, push. Rule: "Once the file is in the repository, the plugin is published, with no submission form". https://code.claude.com/docs/en/plugins/publish
- **skills.sh** `[worth it, agent]` Repos with `skills/<name>/SKILL.md`. Route: print `npx skills add <owner>/<repo>` in the README. Rule: "Skills appear on the leaderboard automatically through anonymous telemetry when users run npx skills add <owner/repo>." https://skills.sh/docs/faq
- **cursor.directory** `[worth it, agent signed in]` MCP servers, rules, skills, agents. Route: https://cursor.directory/plugins/new Rule: "Submitted plugins are auto-reviewed by a Cursor SDK agent".
- **Gemini CLI extensions gallery** `[worth it, agent]` Route: `gemini-extension.json` at the repo root and the topic `gemini-cli-extension`. Rule: "Our crawler uses this topic to find new extensions." https://geminicli.com/docs/extensions/releasing/
- **Anthropic directory** `[worth it, owner]` Plugin bundles and MCP connectors. Route: https://claude.ai/directory/manage Rule: "Free accounts can't submit". Check the pre-submission list first: a README of at least 40 words, a licence, pinned launchers, no binaries. https://claude.com/docs/plugins/pre-submission-checklist
- **github/awesome-copilot external plugins** `[situational, agent]` Route: the external plugin issue form with a release tag and a full commit SHA. Rule: "Do not open a pull request that directly adds a third-party plugin to plugins/external.json." https://github.com/github/awesome-copilot/blob/main/CONTRIBUTING.md
- **OpenAI plugin directory** `[situational, owner]` Rule: "Complete individual or business verification in organization settings to publish under your name or a company name." https://developers.openai.com/plugins/deploy/submission
- **Catalogues that copy the file into their own repo** `[situational, agent]` They suit one skill or one config. When the goal is traffic to the repo, prefer places that link out.
- **wshobson/agents** `[situational, agent]` Rule: "Plugin content must not funnel users to paid products, affiliate programs, or revenue-sharing services."
- **Framework catalogues** `[situational]` n8n community nodes ("you must publish **ALL** community nodes using a GitHub action and include a provenance statement"), LangChain integrations (issue form, no manual docs PR), Ollama community integrations, OpenRouter app rankings (attribution headers).

### Closed

- anthropics/claude-plugins-official: partner only. anthropics/claude-plugins-community: a mirror; direct PRs close automatically.
- General AI tool directories charge to list; FutureTools is the free exception.

## Media

A pitch is two or three sentences, written by the owner, with the project link and the install path, sent once.

### Newsletters

- **Console.dev** `[worth it, owner sends]` Developer tools; pre-1.0 fits its Betas list. Route: "Email hello@console.dev with the details". Criteria: "Is the primary user a developer?", "Is it being actively maintained", "Does it have good documentation?". https://console.dev/selection-criteria
- **Changelog News** `[worth it, owner's account]` Rule: "Submitting your own work is also encouraged." Not wanted: "Commercial products/services." https://changelog.com/news/submit
- **PyCoder's Weekly** `[worth it, agent]` Python only. https://pycoders.com/submissions
- **iOS Dev Weekly** `[worth it, agent]` iOS and macOS apps and Swift libraries. Route: https://suggest.iosdevweekly.com/ For libraries it asks for the Swift Package Index listing first.
- **Cooperpress weeklies** `[worth it, owner sends]` Go, Node, JavaScript and others: editor@cooperpress.com naming the newsletter.
- **It's FOSS, Noted, LinuxLinks** `[worth it]` Linux and self-hosted tools. LinuxLinks: "Anyone submitting a project to LinuxLinks must disclose material use of generative AI". Noted invites developers to write the article themselves.
- **HelloGitHub, ruanyf/weekly** `[situational, agent]` Chinese-language audiences, by issue form.

### Blogs, news sites and contributed articles

- **Hackaday** `[situational, owner]` Rule: "Don't send us press releases." https://hackaday.com/submit-a-tip/
- **OMG! Ubuntu, MacStories, XDA, How-To Geek, MakeUseOf** `[situational, owner]` Editorial inboxes on their contact pages. MacStories: "only write about apps if we have personally tested them."
- **Contributed articles** `[situational, owner writes]` InfoQ ("We reject primarily AI-generated work."), DZone ("We do not accept articles that have been partially or fully generated by AI."), freeCodeCamp ("we forbid any sort of ghost writing"), OpenSource.net (not "to promote a product"). The repo is the context of the story, never its subject.

### Podcasts and video

- Changelog, FLOSS Weekly, Python Bytes, and ecosystem shows take guest requests or listener tips. A guest slot is the owner speaking.
- An own 1 to 3 minute demo video, linked from the README and embedded inline in it.

### Closed

- TLDR, Hacker Newsletter, Changelog Nightly: no submission route; they follow what does well elsewhere.

## Communities

The owner types every post and every reply. The agent prepares facts, links and the place's checklist. Reread the live rules before posting; the rules below are as read on the check date.

### Hacker News and aggregators

- **Show HN** `[worth it, owner]` Anything a reader can run at once. Route: https://news.ycombinator.com/submit with a title starting "Show HN", then a first comment with the backstory, and stay to answer. Rule: "Please don't put generated text in HN posts. Write your text yourself"; "Please don't ask friends to upvote or comment." Not for point releases. https://news.ycombinator.com/showhn.html
- **Ask HN: What are you working on?** `[worth it, owner]` A monthly thread; one comment.
- **Lobsters** `[situational, owner]` By invitation. Rule: "self-promo should be less than a quarter of one's stories and comments." https://lobste.rs/about

### Reddit

Every route needs the owner's account; several require karma earned in that subreddit first.

| Subreddit | Fits | Rule that decides |
|---|---|---|
| r/selfhosted | self-hosted apps | projects under three months old go in the weekly New Project Megathread with an "AI Involvement" field |
| r/homelab | home-lab tools | flair says how much AI was used; "at least one month of commit history and screenshots" |
| r/opensource | any OSI-licensed repo | "All AI-generated content is low-effort and ban worthy." |
| r/coolgithubprojects | any GitHub repo | own projects welcome |
| r/ClaudeAI, r/ClaudeCode | things built with or for Claude | weekly showcase thread; free to try; no referral links |
| r/mcp | MCP servers | `showcase` tag; "Self-promotion is allowed with proper disclosure." |
| r/macapps, r/MacOS | macOS apps | local karma, monthly limits; r/MacOS self-promotion on Saturdays (UTC) only |
| r/homeassistant | integrations and cards | personal projects allowed, ads not |
| r/golang, r/Python, r/webdev, r/devops, r/sysadmin | language and role communities | weekly or monthly showcase threads only |
| r/commandline | CLIs | no projects under a month old; "Post text or titles generated with AI are strictly prohibited" |

Closed: r/programming ("No Product Promotion"), r/LocalLLaMA, r/DataHoarder, r/androidapps, r/fossdroid.

### Fediverse and social

- **Lemmy** `[worth it, owner]` selfhosted@lemmy.world wants titles tagged [CBH] (code by human) or [AIP] (AI project) with a disclosure; opensource@lemmy.ml takes link posts.
- **Mastodon** `[worth it, owner]` One post per release with a few hashtags and alt text on screenshots. mastodon.social's rules say "use of generative AI must be disclosed".
- **Bluesky, LinkedIn, X** `[situational, owner]` The owner's own audience; keyword feeds on Bluesky pick up posts by their words.

### Project forums

- **The upstream project's own forum** `[worth it, owner]` The Home Assistant community, the Jellyfin forum, the Unraid support threads, Privacy Guides' showcase, Kubernetes Discuss announcements: one topic per project that becomes its support thread. Most bar AI-written posts and answers.
- **Software Recommendations Stack Exchange** `[situational, owner]` Answers to existing questions, with "you must disclose your affiliation in your post."
- **Blogging platforms** `[situational, owner]` DEV (#showdev; AI-assisted posts must disclose it), Hashnode, Habr, Qiita, Zenn: a real article in the owner's voice.

### Closed

- Stack Overflow: generative AI content is banned.
- Kubernetes Slack: posting personal projects "in order to drive traffic is considered spam".

## Funding programmes and events

- **NLnet** `[worth it, owner writes]` A concrete technical work plan. Route: https://nlnet.nl/propose/ First grants of 5,000 to 50,000 EUR; individuals may apply. Its generative-AI policy requires disclosing and logging any AI-drafted part. https://nlnet.nl/foundation/policies/generativeAI/
- **Open Source Endowment** `[worth it, agent]` Independent tools with dependents. Rule: "self-nominations are welcome too!"; "no corporate or VC-funded projects". https://endowment.dev/funding
- **FUTO microgrants** `[worth it, owner emails]` Apps that replace a big-tech service: "one-time microgrants of $1,000–$5,000". Email grantapps@futo.org.
- **thanks.dev, ecosyste.ms Funds** `[situational]` Money split over dependency trees; keep FUNDING.yml present.
- **FLOSS/fund** `[situational, agent]` Route: a `funding.json` submitted at https://dir.floss.fund/submit Rule: "Very new projects or projects with minimal usage are not considered for the time being."
- **GitHub Secure Open Source Fund** `[situational, owner]` Flagship repos with real usage; rolling applications.
- **Open Collective** `[situational, owner]` An independent collective holds money in the owner's own account; fiscal hosts require an organisation-owned repo.
- **Free tiers for open source** `[situational]` SignPath (Windows code signing), JetBrains licences, Crowdin or Weblate (translators), SonarQube Cloud, Algolia DocSearch, Claude for Open Source, Codex for Open Source. Each states its own eligibility test; several exclude projects with a commercial side or require a permissive licence.
- **Awards** `[situational]` European Open Source Awards (self-nominations encouraged), FSF and SFS awards (someone else nominates).
- **Events** `[worth it, owner]` Talks and stands: FOSDEM, Config Management Camp, FOSS Backstage, KubeCon, language conferences. A talk is about an idea, not the product. Find current calls on https://confs.tech/cfp and https://foss.events/

## Europe

Grants and conferences in Europe are in the section above.

### Directories of European and ethical alternatives

- **European Alternatives** `[worth it, agent on the owner's account]` Self-hosted apps that are easy to host. Rule: "European Alternatives also lists open source projects that can be self-hosted. ... However, it should be relatively easy to host the product itself." https://european-alternatives.eu/about
- **EuroStack Directory** `[worth it, agent]` Open source made in Europe; company fields optional. https://euro-stack.com/submit/solution
- **European OpenSource catalog** `[worth it, agent]` Any repo from a European country. Route: the project issue form at https://github.com/European-OpenSource/awesome-european-opensource
- **Framalibre** `[worth it, agent]` End-user apps under a free licence; the entry is written in French. Contributions are CC BY-SA 4.0. https://framalibre.org/contribuer
- **Go European, switching.software, Le Alternative** `[situational, agent]` Consumer apps that replace a named product.

### Public-sector catalogues

- **Interoperable Europe Portal** `[situational, owner]` Rule: "The solution MUST be, or be planned to be used by at least one public administration."; an English description is required. https://interoperable-europe.ec.europa.eu/joinup/eligibility-criteria
- **Digital Public Goods Registry** `[situational, owner]` Open-data and civic tools with a link to a UN Sustainable Development Goal.
- **publiccode.yml** Only for repos with a real public-sector angle. National catalogues (Italy, France, Germany, the Netherlands, Sweden, Finland) crawl or accept only software published or used by public bodies, so the file alone lists nothing.

### Media and communities in other languages

- A translation opens a venue: French (LinuxFr, Journal du hacker, Belginux, Framalibre), German (GNU/Linux.ch, LinuxNews.de, heise, Caschys Blog), Italian (Le Alternative, Punto Informatico), Dutch (iCulture). LinuxFr: "les communiqués de presse copiés-collés rapidement dans le formulaire ne doivent pas être approuvés."
- The Kuketz blog and forum refuse press releases and AI text.

## A national layer: Spain as the worked example

Every country has the same three layers. Find them for the maintainer's country by searching for its national open-data portal's "applications" or "reuse" page, its regional portals, and its tech press contact pages.

- **Open-data application catalogues** `[worth it, agent with the owner's consent]` Tools that use the country's public open data. Spain: https://datos.gob.es/es/aplicaciones/crear-aplicacion asks for "Enlaces a los orígenes de datos" and the owner's contact details. Regional portals (Madrid, Castilla y León, Andalucía, Galicia, Aragón, Zaragoza) run their own forms for apps on their data.
- **Language and regional catalogues** `[situational, agent]` Softcatalà lists apps with a Catalan translation and asks for a Catalan screenshot.
- **Tech press in the language** `[worth it, owner sends]` Spain: Genbeta, Microsiervos, MuyLinux, atareao, NASeros, the Xataka family. Pitches in Spanish, sent once.
- **Communities in the language** `[situational, owner]` Menéame: own links only from an account with karma 7 or more whose previous five submissions come from other sources; "Nuestras conversaciones son humanas y entre personas humanas." r/spain: promotion "deberán ser aprobados por los moderadores antes de publicarse". Finance forums accept free tools with no payments, ads or referral links, after moderator approval.
- **Events in the language** `[situational, owner]` esLibre, T3chFest, OpenSouthCode, PyConES, local DevFests.
- Closed in Spain: Rankia and HelpMyCash forums (no project posts), ElOtroLado and BandaAncha (no self-promotion), the Spanish Wikipedia under conflict of interest.

## What to do on the repo first

Each practice carries its source. "Measured" means a number was read; "no evidence" means nobody showed one.

### Be findable

- Put the words people type in the name, description or topics; README text is not searched by default. https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories
- Search engines and AI assistants are the standing referrers of small repos; in the referrer lists we read, no launch directory appeared. Read your own with `gh api repos/<owner>/<repo>/traffic/popular/referrers`.
- GitHub keeps traffic for 14 days only, so snapshot views, clones and referrers on a schedule. https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository
- README images, lists, outbound links, a licence and contribution guidelines separate popular from unpopular repos in two studies; a correlation, not a proven cause. https://arxiv.org/abs/2206.10772 and https://arxiv.org/abs/2010.02472
- Track clones, installs and issues beside stars: 73% of 791 surveyed developers look at stars before using a project, so stars are a signal others read, not the goal. https://arxiv.org/abs/1811.07643

### Readiness

- "If your work isn't ready for users to try out, please don't do a Show HN." https://news.ycombinator.com/showhn.html
- Alternatives sites ask for the proprietary rival as a form field, and several subreddits require a comparison in the post. https://opensourcealternative.to/submit
- selfh.st, r/selfhosted, r/homelab, selfhosted@lemmy.world, LinuxLinks and Jellyfin ask how AI was used. Keep the answer in the README and link it. https://jellyfin.org/docs/general/contributing/llm-policies/
- Ages matter: 30 days for Homebrew and r/commandline, a month of commits for r/homelab, three months to leave the r/selfhosted megathread, four months for Obtainium.
- For self-hosted apps, every store template is cut from the README's compose example. https://github.com/Dokploy/templates/blob/canary/CONTRIBUTING.md
- European directories admit an individual under their open-source criteria, never under their company criteria, so say where the maintainer is based. https://european-alternatives.eu/about

### Launch timing and measurement

- A Hacker News post can roughly double short-term star gain, but about one post in ten gets attention. Measured on 3,019 posts: a median 74 stars in the three days before against 138 after. https://arxiv.org/abs/1908.04219
- Posting between 12:00 and 17:00 UTC did better; weekday against weekend made no difference, and the "Show HN" prefix brought no extra stars by itself. Observational, 138 repos. https://arxiv.org/abs/2511.04453
- For self-hosted apps, post to the self-hosting communities first and use the replies to fix the pitch before Hacker News. Self-reported cases. https://rybbit.com/blog/5k-stars
- Pay only where a fee buys review speed on a site people actually search.
- Keep one row per channel and post: date, source, URL, views, stars, clones, read at 24 hours, 72 hours and 7 days, each labelled verified, self-reported or inferred. https://github.com/Gingiris-1031/gingiris-skills/blob/main/skills/github-stars-playbook/SKILL.md
- Pick the few communities that would use the repo and take part there before posting. https://opensource.guide/finding-users/

### No evidence, do not treat as measured

- Launch directories and backlink campaigns bringing users to an open-source repo. The public skill that recommends them calls indie launch sites "worth an afternoon, not a strategy". https://github.com/coreyhaines31/marketingskills/blob/main/skills/directory-submissions/SKILL.md
- What one awesome-list entry or newsletter mention brings. Log the publication date and compare the 14-day traffic before and after.
- GitHub Trending thresholds and star call-to-action loops.
- Mass-distribution routines (old high-karma accounts, recruited upvotes, AI auto-comments, paid submission agencies): no measured breakdown, and they break the Hacker News and GitHub rules quoted above.
