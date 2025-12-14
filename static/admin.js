function $(id){ return document.getElementById(id); }

function safeText(el, text){
  el.textContent = text ?? "";
}

function fmtDate(s){
  if(!s) return "";
  try{
    const d = new Date(s);
    if(Number.isNaN(d.getTime())) return s;
    return d.toLocaleString();
  }catch{
    return s;
  }
}

// LOGIN
async function handleLogin(){
  const u = $("username").value.trim();
  const p = $("password").value;
  const remember = $("remember").checked;

  const flash = $("flash");
  flash.style.display = "none";

  if(remember) localStorage.setItem("admin_username", u);
  else localStorage.removeItem("admin_username");

  try{
    const res = await fetch("/api/admin/login", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      credentials: "include",
      body: JSON.stringify({username: u, password: p})
    });
    const data = await res.json().catch(() => ({}));

    if(res.ok && data.success){
      window.location.href = "/admin";
      return;
    }
    flash.style.display = "block";
    safeText(flash, data.message || "Login failed. (wrong creds or server said no)");
  }catch(err){
    flash.style.display = "block";
    safeText(flash, "Network/Server error. Is Flask running on :5001?");
  }
}

function initLogin(){
  const saved = localStorage.getItem("admin_username");
  if(saved){
    $("username").value = saved;
    $("remember").checked = true;
  }
  $("loginBtn").addEventListener("click", (e) => { e.preventDefault(); handleLogin(); });
  $("password").addEventListener("keydown", (e) => { if(e.key === "Enter") handleLogin(); });
}

// DASHBOARD
let ALL = [];

function renderRows(list){
  const tbody = $("tbody");
  tbody.innerHTML = "";

  for(const idea of list){
    const tr = document.createElement("tr");

    const tdId = document.createElement("td");
    safeText(tdId, String(idea.id ?? ""));
    tr.appendChild(tdId);

    const tdText = document.createElement("td");
    // IMPORTANT: use textContent so an “idea” can’t inject HTML
    safeText(tdText, idea.idea_text ?? "");
    tr.appendChild(tdText);

    const tdAt = document.createElement("td");
    tdAt.className = "small";
    safeText(tdAt, fmtDate(idea.created_at));
    tr.appendChild(tdAt);

    tbody.appendChild(tr);
  }
}

function applyFilter(){
  const q = $("q").value.trim().toLowerCase();
  const filtered = !q ? ALL : ALL.filter(x => (x.idea_text || "").toLowerCase().includes(q));
  renderRows(filtered);
  safeText($("count"), String(filtered.length));
}

async function fetchIdeas(){
  const status = $("status");
  safeText(status, "syncing…");
  status.classList.add("flicker");

  try{
    const res = await fetch("/api/admin/ideas", { credentials: "include" });
    if(res.status === 401 || res.status === 403){
      window.location.href = "/admin/login";
      return;
    }
    const data = await res.json();
    ALL = data.ideas || [];
    applyFilter();

    safeText($("total"), String(data.total ?? ALL.length));
    safeText($("updated"), new Date().toLocaleTimeString());
    safeText(status, "online");
  }catch{
    safeText($("status"), "offline");
  }finally{
    status.classList.remove("flicker");
  }
}

async function doLogout(){
  // clean logout: try API, fallback to web route
  try{
    await fetch("/api/admin/logout", {
      method: "POST",
      credentials: "include"
    });
  }catch(e){
    // ignore
  }
  window.location.href = "/admin/logout";
}

function initDashboard(){
  $("q").addEventListener("input", applyFilter);
  $("refreshBtn").addEventListener("click", fetchIdeas);

  const logoutBtn = $("logoutBtn");
  if(logoutBtn){
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      doLogout();
    });
  }

  fetchIdeas();
  setInterval(fetchIdeas, 10000);
}
