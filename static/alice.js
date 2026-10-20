const toast = (msg) => {
  const el = document.getElementById("toast");
  el.hidden = false;
  el.textContent = msg;
  clearTimeout(window.__aliceToast);
  window.__aliceToast = setTimeout(() => {
    el.hidden = true;
  }, 2400);
};

const post = async (url, body) => {
  const res = await fetch(url, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.reason || res.statusText);
  return data;
};

const saveDraft = async (jacket) => {
  const id = jacket.dataset.id;
  const subject = jacket.querySelector(".subject")?.value || "";
  const body_text = jacket.querySelector(".body")?.value || "";
  if (!jacket.querySelector(".subject")) return;
  await post(`/api/jobs/${id}/draft`, { subject, body_text });
};

document.getElementById("run-pipeline")?.addEventListener("click", async (ev) => {
  ev.target.disabled = true;
  try {
    await post("/api/pipeline/run");
    toast("Pipeline started. Refresh in a minute.");
  } catch (err) {
    toast(String(err.message || err));
    ev.target.disabled = false;
  }
});

document.getElementById("live-crawl")?.addEventListener("change", async (ev) => {
  const enabled = ev.target.checked;
  try {
    await post("/api/settings/live-crawl", { enabled });
    location.reload();
  } catch (err) {
    ev.target.checked = !enabled;
    toast(String(err.message || err));
  }
});

document.getElementById("seed-demo")?.addEventListener("click", async (ev) => {
  ev.target.disabled = true;
  try {
    const data = await post("/api/demo/seed");
    toast(`Sample deck ready · ${data.count} cards`);
    location.href = "/";
  } catch (err) {
    toast(String(err.message || err));
    ev.target.disabled = false;
  }
});

document.querySelectorAll(".jacket").forEach((jacket) => {
  jacket.querySelector(".apply")?.addEventListener("click", async () => {
    const url = jacket.dataset.apply;
    await post(`/api/jobs/${jacket.dataset.id}/apply`);
    if (url) window.open(url, "_blank", "noopener");
    toast("Apply opened. You submit the form.");
  });

  jacket.querySelector(".send")?.addEventListener("click", async () => {
    if (jacket.dataset.email !== "1") return;
    await saveDraft(jacket);
    await post(`/api/jobs/${jacket.dataset.id}/send`);
    toast("Draft sent.");
    location.reload();
  });

  jacket.querySelector(".skip")?.addEventListener("click", async () => {
    await post(`/api/jobs/${jacket.dataset.id}/skip`);
    jacket.remove();
  });

  jacket.querySelector(".promote")?.addEventListener("click", async () => {
    const data = await post(`/api/jobs/${jacket.dataset.id}/promote`);
    toast(`Promoted to ${data.status}`);
    location.reload();
  });
});
