(() => {
  const $ = (id) => document.getElementById(id);

  const REPO = "sillyjoshua/glovebox";
  const RELEASE_API = `https://api.github.com/repos/${REPO}/releases/latest`;

  /* ---------- download tabs ---------- */
  function initDownloadTabs() {
    const tabs = document.querySelectorAll(".dl-tabs [role=tab]");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
        document.querySelectorAll(".dl-panel").forEach((p) => {
          p.hidden = p.id !== `panel-${tab.dataset.os}`;
        });
      });
    });
  }

  // Confirm a release actually exists and show its version/size instead of
  // a link that might 404 on a repo with no releases yet.
  async function checkRelease() {
    const meta = $("file-meta");
    try {
      const res = await fetch(RELEASE_API, { headers: { Accept: "application/vnd.github+json" } });
      if (!res.ok) throw new Error("no release yet");
      const data = await res.json();
      const asset = (data.assets || []).find((a) => a.name === "glovebox.zip");
      if (!asset) throw new Error("asset missing");
      const mb = (asset.size / (1024 * 1024)).toFixed(1);
      meta.textContent = `${data.tag_name} · ${mb} MB · same file for every system`;
    } catch {
      meta.textContent =
        "No release is published yet. Push a tag (e.g. v1.0.0) to the repo to build glovebox.zip.";
      document.querySelectorAll("#dl-win, #dl-mac, #dl-linux").forEach((a) => {
        a.setAttribute("aria-disabled", "true");
        a.classList.add("disabled");
      });
    }
  }

  /* ---------- tool rack (read-only preview of the catalog) ---------- */
  let tools = [];
  let cat = "All";
  let q = "";

  async function loadCatalog() {
    try {
      const res = await fetch("catalog.json");
      const data = await res.json();
      tools = data.tools;
      $("tools-sub").textContent =
        `${tools.length} tools. Most open their official download page inside the app; a few download straight in.`;
      buildCats();
      renderRack();
    } catch {
      $("tools-sub").textContent = "Couldn't load the tool list right now.";
    }
  }

  function buildCats() {
    const cats = ["All", ...new Set(tools.map((t) => t.category))];
    $("cats").replaceChildren(
      ...cats.map((c) => {
        const b = document.createElement("button");
        b.className = "cat";
        b.textContent = c;
        b.setAttribute("aria-pressed", String(c === cat));
        b.onclick = () => { cat = c; buildCats(); renderRack(); };
        return b;
      })
    );
  }

  function renderRack() {
    const query = q.trim().toLowerCase();
    const list = tools.filter((t) =>
      (cat === "All" || t.category === cat) &&
      (!query || t.name.toLowerCase().includes(query) || t.blurb.toLowerCase().includes(query))
    );
    $("empty").hidden = list.length > 0;
    $("rack").replaceChildren(...list.map(slot));
  }

  function slot(t) {
    const li = document.createElement("li");
    li.className = "slot";

    const led = document.createElement("span");
    led.className = "led" + (t.kind === "page" ? " page" : "");
    led.title = t.kind === "page" ? "Opens the official download page" : "Downloads directly";

    const body = document.createElement("span");
    const h = document.createElement("h3");
    h.textContent = t.name;
    const p = document.createElement("p");
    p.textContent = t.blurb;
    body.append(h, p);

    const side = document.createElement("span");
    side.className = "side";
    const b = document.createElement("b");
    b.textContent = t.platforms.map((p) => ({ win: "Windows", mac: "macOS", linux: "Linux" }[p])).join(" / ");
    side.append(b, `${t.category} · ~${t.size_mb} MB`);

    li.append(led, body, side);
    return li;
  }

  $("q").addEventListener("input", (e) => { q = e.target.value; renderRack(); });

  initDownloadTabs();
  checkRelease();
  loadCatalog();
})();
