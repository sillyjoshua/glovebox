(() => {
  const $ = (id) => document.getElementById(id);
  const state = { tools: [], platform: "", selected: new Set(), cat: "All", q: "", busy: false };

  const STATUS_LABEL = {
    empty: "Not installed",
    queued: "Waiting for file",
    installed: "Installed",
    working: "Installing",
    failed: "Failed",
  };

  async function load() {
    const res = await fetch("/api/tools");
    const data = await res.json();
    state.tools = data.tools;
    state.platform = data.platform;
    const plat = { win: "Windows", mac: "macOS", linux: "Linux" }[data.platform];
    $("meta").textContent =
      `${plat} detected · ${data.free_mb.toLocaleString()} MB free on this drive · ` +
      `${state.tools.length} tools`;
    buildCats();
    render();
  }

  function buildCats() {
    const cats = ["All", ...new Set(state.tools.map((t) => t.category))];
    $("cats").replaceChildren(
      ...cats.map((c) => {
        const b = document.createElement("button");
        b.className = "cat";
        b.textContent = c;
        b.setAttribute("aria-pressed", String(c === state.cat));
        b.onclick = () => { state.cat = c; buildCats(); render(); };
        return b;
      })
    );
  }

  function visible() {
    const q = state.q.trim().toLowerCase();
    return state.tools.filter((t) =>
      (state.cat === "All" || t.category === state.cat) &&
      (!q || t.name.toLowerCase().includes(q) || t.blurb.toLowerCase().includes(q))
    );
  }

  function render() {
    const list = visible();
    $("empty").hidden = list.length > 0;
    $("rack").replaceChildren(...list.map(slot));
    updateTray();
  }

  function slot(t) {
    const el = document.createElement("button");
    el.className = "slot";
    el.type = "button";
    const status = t._status || t.status;
    el.dataset.status = status;
    el.dataset.unsupported = String(!t.supported);
    el.setAttribute("aria-pressed", String(state.selected.has(t.id)));
    el.disabled = !t.supported;

    const led = document.createElement("span");
    led.className = "led";

    const body = document.createElement("span");
    const h = document.createElement("h3");
    h.textContent = t.name;
    const p = document.createElement("p");
    p.textContent = t.supported ? t.blurb : `${t.blurb} (not available for this OS)`;
    body.append(h, p);

    const side = document.createElement("span");
    side.className = "side";
    const b = document.createElement("b");
    b.textContent = STATUS_LABEL[status];
    side.append(b, `${t.category} · ~${t.size_mb} MB`);

    if (status === "queued") {
      const done = document.createElement("span");
      done.className = "mark";
      done.textContent = "I've added the files";
      done.setAttribute("role", "button");
      done.tabIndex = 0;
      const mark = async (ev) => {
        ev.stopPropagation();
        await fetch("/api/mark-done", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: t.id }),
        });
        load();
      };
      done.onclick = mark;
      done.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); mark(ev); } };
      side.append(done);
    }

    el.append(led, body, side);
    el.onclick = () => {
      if (state.busy) return;
      state.selected.has(t.id) ? state.selected.delete(t.id) : state.selected.add(t.id);
      el.setAttribute("aria-pressed", String(state.selected.has(t.id)));
      updateTray();
    };
    return el;
  }

  function updateTray() {
    const n = state.selected.size;
    $("tray").hidden = n === 0 && !state.busy;
    $("count").textContent = n;
    $("install-sel").disabled = n === 0 || state.busy;
  }

  async function install(ids) {
    if (!ids.length || state.busy) return;
    state.busy = true;
    $("install-all").disabled = true;
    $("bar").hidden = false;
    $("bar-fill").style.width = "0%";
    $("tray").hidden = false;
    ids.forEach((id) => { const t = state.tools.find((x) => x.id === id); if (t) t._status = "working"; });
    render();

    const res = await fetch("/api/install", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });
    if (!res.ok) { finish([]); return; }

    const timer = setInterval(async () => {
      const p = await (await fetch("/api/progress")).json();
      $("bar-fill").style.width = `${(p.done / (p.total || 1)) * 100}%`;
      if (p.total && p.done >= p.total && !p.current) {
        clearInterval(timer);
        finish(p.log);
      }
    }, 500);
  }

  function finish(log) {
    state.busy = false;
    state.selected.clear();
    $("install-all").disabled = false;
    $("bar").hidden = true;
    state.tools.forEach((t) => delete t._status);

    $("log").hidden = log.length === 0;
    $("log-list").replaceChildren(
      ...log.map((e) => {
        const li = document.createElement("li");
        if (!e.ok) li.className = "bad";
        li.textContent = e.message;
        return li;
      })
    );
    load();
  }

  $("q").addEventListener("input", (e) => { state.q = e.target.value; render(); });
  $("clear").onclick = () => { state.selected.clear(); render(); };
  $("install-sel").onclick = () => install([...state.selected]);
  $("install-all").onclick = () => {
    const ids = state.tools.filter((t) => t.supported && t.status === "empty").map((t) => t.id);
    if (!ids.length) { alert("Everything for this computer is already installed or queued."); return; }
    if (confirm(`Install ${ids.length} tools? Some will open their official download pages in your browser.`)) {
      install(ids);
    }
  };

  load();
})();
