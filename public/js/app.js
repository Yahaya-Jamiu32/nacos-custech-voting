const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const A = $("#app"), S = {csrf: sessionStorage.getItem("csrf"), admin: sessionStorage.getItem("admin") === "1", matric: sessionStorage.getItem("matric") || ""};
let timer = null, vi = 0, li = 0;
const WM = '<footer class="wm">Designed by DeNoble (Yahaya Jamiu)</footer>';
const LBL = {draft: "NOT STARTED", open: "VOTING IN PROGRESS", closed: "VOTING CLOSED", cancelled: "CANCELLED"};
const fmt = t => t ? new Date(t + "Z").toLocaleString() : "Not set";
const bar = p => `<div class="bar"><i style="width:${p}%"></i></div>`;
const note = (t, ok) => { const o = $("#o"); if (o) { o.className = "msg " + (ok ? "ok" : "err"); o.textContent = t; } };
function fb(img) { const s = document.createElement("span"); s.className = "lg"; s.textContent = img.dataset.l; img.replaceWith(s); }
const logos = () => `<div class="logos"><img class="lgi" src="/images/custech.png" data-l="CUSTECH" alt="CUSTECH logo" onerror="fb(this)"><img class="lgi" src="/images/nacos.png" data-l="NACOS" alt="NACOS logo" onerror="fb(this)"></div>`;

async function api(path, method = "GET", body) {
  const h = {"Content-Type": "application/json"}; if (S.csrf) h["X-CSRF-Token"] = S.csrf;
  let r; try { r = await fetch("/api" + path, {method, headers: h, credentials: "same-origin", body: body ? JSON.stringify(body) : undefined}); }
  catch { throw new Error("Network error. Check your connection."); }
  const j = await r.json().catch(() => ({}));
  if (r.status === 401 && !path.startsWith("/login")) { sessionStorage.clear(); S.csrf = null; location.hash = "login"; throw new Error("Please log in."); }
  if (r.status === 403 && j.code === "face_required") { location.hash = "face"; throw new Error("Face check required."); }
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
}
function page(title, body, back, sub) {
  A.className = ""; clearInterval(timer);
  A.innerHTML = `<header class="top">${back ? `<button class="ic" aria-label="Back" data-go="${back}">&#8592;</button>` : ""}<h1>${esc(title)}${sub ? `<small>${esc(sub)}</small>` : ""}</h1></header><main class="card main">${body}</main>${WM}`;
}
const go = h => `data-go="${h}"`;

const IC = {
  box: '<svg viewBox="0 0 48 48" fill="currentColor" aria-hidden="true"><path d="M7 22h34v19a3 3 0 0 1-3 3H10a3 3 0 0 1-3-3z"/><rect x="15" y="27" width="18" height="4" rx="2" fill="#fff"/><rect x="17" y="3" width="15" height="17" rx="1.5" transform="rotate(14 24 12)"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="11" opacity=".35"/><circle cx="12" cy="9" r="4"/><path d="M4.500 19c1.500-3 4.500-4.500 7.500-4.500s6 1.500 7.500 4.500a10 10 0 0 1-15 0z"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l8 3v6c0 5-3.400 9.400-8 11-4.600-1.600-8-6-8-11V5z"/><path d="M12 2v20c4.600-1.600 8-6 8-11V5z" fill="#fff" opacity=".35"/></svg>',
  eye: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 5C6.500 5 2.700 9 1 12c1.700 3 5.500 7 11 7s9.300-4 11-7c-1.700-3-5.500-7-11-7z"/><circle cx="12" cy="12" r="4.500" fill="#fff"/><circle cx="12" cy="12" r="2.500"/></svg>',
  phone: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2.500"/><rect x="8" y="5" width="8" height="12" rx="1" fill="#fff"/><circle cx="12" cy="19.500" r="1" fill="#fff"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M7 12.500l3.500 3.500L17 9" stroke="#fff" stroke-width="2.200" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
};
function splash() {
  const f = [["shield", "Secure", "Your vote is protected with security-focused design."], ["eye", "Transparent", "Follow election results with greater visibility."], ["phone", "Convenient", "Access the voting platform from your device."], ["check", "Fair", "Support fair participation in student elections."]];
  A.className = "landing"; clearInterval(timer);
  A.innerHTML = `<header class="lh"><span class="ib2">${IC.box}</span><img class="lhl" src="/images/custech.png" alt="CUSTECH logo" onerror="this.remove()"><div class="lht"><b>NACOS CUSTECH</b><small>Electronic Voting System</small></div>
<button class="hb" id="hb" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button></header>
<nav class="mn" id="mn" hidden><button data-go="login">Login to Vote</button><button id="lm2">Learn More</button></nav>
<section class="hero2"><div class="hov"><span class="chip">NACOS CUSTECH</span><h1>Electronic Voting System</h1><h2>Your Voice Matters. Vote with Confidence.</h2>
<p>Participate in NACOS CUSTECH elections through a secure, transparent, and convenient online voting platform.</p>
<button class="lbtn" data-go="login"><span class="ico">${IC.user}</span>Login to Vote</button><button class="lbtn out" id="lm">Learn More</button></div></section>
<section class="rv"><span class="bx">${IC.box}</span><h3>Ready to Vote?</h3><p>Log in with your student credentials to access the current elections.</p><button class="lbtn solid" data-go="login">Login Now &#8594;</button></section>
<section class="why" id="why"><h3>Why Vote Online?</h3><i class="ul"></i>${f.map(x => `<div class="ft"><span class="fi">${IC[x[0]]}</span><div><b>${x[1]}</b><p>${x[2]}</p></div></div>`).join("")}</section>
<footer class="lf"><b>NACOS CUSTECH</b><b>Electronic Voting System</b><p>&copy; ${new Date().getFullYear()}. All Rights Reserved.</p><p class="dz">Designed by DeNoble (Yahaya Jamiu)</p></footer>`;
  const why = () => $("#why").scrollIntoView({behavior: "smooth"});
  $("#lm").onclick = why; $("#lm2").onclick = () => { $("#mn").hidden = true; why(); };
  $("#hb").onclick = () => { const m = $("#mn"); m.hidden = !m.hidden; $("#hb").setAttribute("aria-expanded", String(!m.hidden)); };
}
function login() {
  A.className = "light"; A.innerHTML = `<div class="hero" style="justify-content:flex-start">${logos()}<h1 style="color:var(--dark)">NACOS CUSTECH<span>Electronic Voting System</span></h1>
<div class="card" style="text-align:left"><b>Login to your account</b><label for="m">Matric Number</label><input id="m" autocomplete="off" autocapitalize="characters" placeholder="e.g. 23L1CS0001">
<label for="p">Phone Number</label><input id="p" inputmode="tel" placeholder="e.g. 08012345678"><div id="ad" hidden><label for="a">Administrator password</label><input id="a" type="password" autocomplete="current-password"></div>
<button class="btn" id="go">Login</button><div id="o" role="alert"></div><small style="text-align:center">Having trouble? Contact the election committee.</small>
<small style="text-align:center"><a href="#" id="sa" style="color:var(--dark)">Administrator login</a></small></div></div>${WM}`;
  $("#sa").onclick = e => { e.preventDefault(); $("#ad").hidden = false; };
  $("#go").onclick = async () => { const b = $("#go"); b.disabled = true; b.textContent = "Checking...";
    try { const r = await api("/login", "POST", {matric: $("#m").value, phone: $("#p").value, admin_password: $("#a").value});
      S.csrf = r.csrf; S.admin = r.admin; S.matric = $("#m").value.trim().toUpperCase();
      sessionStorage.setItem("csrf", S.csrf); sessionStorage.setItem("admin", r.admin ? "1" : ""); sessionStorage.setItem("matric", S.matric);
      location.hash = r.admin ? "admin" : r.face_required ? "face" : "home"; } catch (e) { note(e.message); }
    b.disabled = false; b.textContent = "Login"; };
}
/* ---------- face check (runs in the browser; only a 128-number template is sent, never a photo) ---------- */
const FACE_CDN = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12", FACE_LOCAL = "/models";   // to self-host, put face-api.js in public/js and the model files in public/models
let camStream = null, faceReady = null;
function stopCam() { if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; } }
const addScript = src => new Promise((ok, no) => { const e = document.createElement("script"); e.src = src; e.onload = ok; e.onerror = () => no(new Error("load " + src)); document.head.appendChild(e); });
function loadFace() {
  if (faceReady) return faceReady;
  faceReady = (async () => {
    try { await addScript("/js/face-api.js"); } catch { await addScript(FACE_CDN + "/dist/face-api.js"); }
    const base = await fetch(FACE_LOCAL + "/tiny_face_detector_model-weights_manifest.json").then(r => r.ok ? FACE_LOCAL : FACE_CDN + "/model").catch(() => FACE_CDN + "/model");
    await Promise.all([faceapi.nets.tinyFaceDetector.loadFromUri(base), faceapi.nets.faceLandmark68Net.loadFromUri(base), faceapi.nets.faceRecognitionNet.loadFromUri(base)]);
  })().catch(e => { faceReady = null; throw new Error("Could not load the face scanner. Check your internet connection and try again."); });
  return faceReady;
}
async function face() {
  page("Face Check", `<p class="sub">To keep the vote fair, each person may register one face. Your face is turned into a short list of numbers on your phone. <b>No photo is saved or sent.</b> The numbers are used only to stop one person voting with several accounts, and are deleted after the election.</p>
<label style="display:flex;gap:8px;align-items:flex-start;margin:.6rem 0"><input type="checkbox" id="fc" style="width:auto;margin-top:3px"><span>I agree that my face template is stored for this election, as described above.</span></label>
<video id="vid" playsinline muted style="width:100%;max-height:340px;border-radius:12px;background:#000;transform:scaleX(-1);display:none"></video>
<button class="btn" id="fs">Start camera and scan</button><div id="o" role="alert"></div>
<small>Face the camera in good light, remove cap or glasses if possible, and keep only one face in view.</small>`);
  const btn = $("#fs"), vid = $("#vid");
  btn.onclick = async () => {
    if (!$("#fc").checked) return note("Please tick the consent box first.");
    btn.disabled = true; btn.textContent = "Preparing...";
    try {
      await loadFace();
      stopCam(); camStream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "user", width: {ideal: 640}}, audio: false});
      vid.srcObject = camStream; vid.style.display = "block"; await vid.play(); btn.textContent = "Hold still...";
      const opt = new faceapi.TinyFaceDetectorOptions({inputSize: 320, scoreThreshold: 0.6}), got = []; let tries = 0;
      while (got.length < 3 && tries++ < 40) {
        const all = await faceapi.detectAllFaces(vid, opt).withFaceLandmarks().withFaceDescriptors();
        if (all.length > 1) note("More than one face is visible. Only you should be in view.");
        else if (all.length === 1) { got.push(Array.from(all[0].descriptor)); note("Scanning " + got.length + "/3..."); }
        else note("No face found. Move closer and face the camera.");
        await new Promise(r => setTimeout(r, 400));
      }
      if (got.length < 3) throw new Error("Could not get a clear scan. Try again in better light.");
      const mean = got[0].map((_, i) => got.reduce((t, g) => t + g[i], 0) / got.length);
      const r = await api("/face", "POST", {descriptor: mean, consent: true});
      stopCam(); note(r.enrolled ? "Face registered." : "Face verified.", 1); setTimeout(() => location.hash = "home", 700);
    } catch (e) {
      stopCam(); vid.style.display = "none";
      note(e.name === "NotAllowedError" ? "Camera permission was denied. Allow the camera in your browser settings and try again." : e.message);
      btn.disabled = false; btn.textContent = "Try again";
    }
  };
}
async function home() {
  const b = await api("/ballot"), n = b.categories.length, k = b.categories.reduce((s, c) => s + c.candidates.length, 0), m = b.categories.filter(c => c.selected).length;
  page("Election Dashboard", `<h2>Hello, ${esc(S.matric)}!</h2><p class="sub">Welcome to your election dashboard.</p>
<div class="box"><b>Voting Status</b><div style="margin-top:6px"><span class="pill ${b.status}">${LBL[b.status] || b.status}</span></div></div>
<div class="tiles"><div class="tile"><small>Total Categories</small><b>${n}</b></div><div class="tile"><small>Total Contestants</small><b>${k}</b></div><div class="tile"><small>Your Votes</small><b>${m}/${n}</b></div></div>
<h3>Quick Actions</h3><button class="btn" ${go("vote")}>Cast Your Vote</button><button class="btn alt" ${go("live")}>View Live Results</button>
${S.admin ? `<button class="btn alt" ${go("admin")}>Admin Panel</button>` : ""}<div class="info"><b>Your vote matters!</b><br>Together we build a better NACOS.</div><button class="btn alt" id="lo">Logout</button>`);
  $("#lo").onclick = async () => { try { await api("/logout", "POST"); } catch {} sessionStorage.clear(); S.csrf = null; location.hash = "login"; };
}
async function vote() {
  const b = await api("/ballot"), cs = b.categories;
  if (!cs.length) return page("Cast Your Vote", '<p class="sub">No ballot has been set up yet.</p>', "home");
  vi = Math.min(vi, cs.length - 1); const c = cs[vi];
  page("Cast Your Vote", `<p class="sub">Category ${vi + 1} of ${cs.length}</p><select id="cs" aria-label="Category">${cs.map((x, i) => `<option value="${i}" ${i === vi ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select>
<div id="o" role="status">${b.status !== "open" ? '<div class="msg warn">Voting is not open right now.</div>' : ""}</div>
${c.candidates.map(k => `<div class="cand ${c.selected === k.id ? "sel" : ""}" tabindex="0" role="radio" aria-checked="${c.selected === k.id}" data-k="${k.id}">${k.photo_url ? `<img class="av" alt="${esc(k.name)}" src="${esc(k.photo_url)}">` : '<span class="av"></span>'}<div><b>${esc(k.name)}</b><small>Department: ${esc(k.department)}</small><small>${esc(k.manifesto)}</small></div><span class="radio">${c.selected === k.id ? "&#9679;" : "&#9675;"}</span></div>`).join("")}
<button class="btn" id="nx">${vi < cs.length - 1 ? "Next Category &#8594;" : "Finish"}</button>`, "home");
  $("#cs").onchange = e => { vi = +e.target.value; vote(); };
  $("#nx").onclick = () => { if (vi < cs.length - 1) { vi++; vote(); } else location.hash = "home"; };
  document.querySelectorAll(".cand").forEach(d => { const pick = async () => {
    if (b.status !== "open") return note("Voting is not open.");
    if (!confirm(`Confirm your vote for ${d.querySelector("b").textContent}?`)) return;
    try { const r = await api("/vote", "POST", {category_id: c.id, candidate_id: +d.dataset.k}); await vote(); note((r.replaced ? "Vote changed" : "Vote recorded") + ". Confirmed by the server.", 1); }
    catch (e) { note(e.message); } };
    d.onclick = pick; d.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } }; });
}
async function live() {
  page("Live Vote Counts", `<select id="cs" aria-label="Category"></select><div style="margin:10px 0"><span class="pill prov" id="pl">...</span></div><div id="lv">Loading...</div><small id="ps"></small><small>Live results update automatically.</small>`, "home");
  let d; const draw = () => { if (!d) return; const cs = d.categories; $("#pl").textContent = d.label === "FINAL" ? "FINAL RESULTS" : "PROVISIONAL - VOTING " + (d.status === "open" ? "IN PROGRESS" : "NOT OPEN");
    $("#ps").textContent = `Participants: ${d.stats.participants} of ${d.stats.voters} voter identities`;
    if (!cs.length) return $("#lv").textContent = "No results yet."; li = Math.min(li, cs.length - 1); const c = cs[li];
    $("#lv").innerHTML = `<table><tr><th>Contestant</th><th class="n">Votes</th><th class="n">%</th></tr>${c.candidates.map(k => `<tr><td>${esc(k.name)}${bar(k.pct)}</td><td class="n">${k.votes}</td><td class="n">${k.pct}%</td></tr>`).join("")}<tr><td><b>Total Votes</b></td><td class="n"><b>${c.total}</b></td><td class="n">100%</td></tr></table>`; };
  const load = async () => { d = await api("/results"); const s = $("#cs"); s.innerHTML = d.categories.map((x, i) => `<option value="${i}" ${i === li ? "selected" : ""}>${esc(x.name)}</option>`).join(""); draw(); };
  $("#cs").onchange = e => { li = +e.target.value; draw(); };
  await load(); timer = setInterval(() => load().catch(() => {}), 10000);
}
async function results() {
  const d = await api("/results");
  if (d.label !== "FINAL") return page("Election Results", `<span class="pill ${d.status}">${LBL[d.status]}</span><div class="msg warn" style="margin-top:12px">Final results appear here after voting closes.</div><button class="btn alt" ${go("live")}>View provisional results</button>`, S.admin ? "admin" : "home");
  page("Election Results", `<span class="pill closed">VOTING CLOSED</span>${d.categories.map(c => `<div class="box"><h3 style="display:flex;justify-content:space-between;margin:0 0 8px">${esc(c.name)}${c.status === "winner" ? '<span class="crown">WINNER</span>' : ""}</h3>
${c.status === "winner" ? `<p><b>${esc(c.leaders[0])}</b><br><small>${c.candidates[0].votes} votes (${c.candidates[0].pct}%)</small></p>` : c.status === "tie" ? `<div class="msg err">TIE: ${esc(c.leaders.join(", "))}. Resolution required.</div>` : '<div class="msg warn">No votes recorded.</div>'}
<table>${c.candidates.map((k, i) => `<tr class="${c.status === "winner" && i === 0 ? "win" : ""}"><td>${i + 1}</td><td>${esc(k.name)}</td><td class="n">${k.votes}</td><td class="n">${k.pct}%</td></tr>`).join("")}</table></div>`).join("")}`, S.admin ? "admin" : "home");
}
async function admin() {
  const [o, k] = await Promise.all([api("/admin/overview"), api("/admin/candidates")]);
  page("Admin Panel", `<h2>Welcome, Admin</h2><p class="sub">Manage the election and monitor activities.</p>
<div class="tiles two"><button class="tile" ${go("cats")}><small>Categories</small><b>${o.results.length}</b></button><button class="tile" ${go("cands")}><small>Contestants</small><b>${k.filter(x => x.active).length}</b></button>
<button class="tile" ${go("live")}><small>Live Results</small><b>&#128202;</b></button><button class="tile" ${go("control")}><small>Election Control</small><b>${LBL[o.status] ? "&#9881;" : ""}</b></button>
<button class="tile" ${go("pdf")}><small>Reports</small><b>&#128196;</b></button><button class="tile" ${go("audit")}><small>Audit Log</small><b>&#128274;</b></button></div>
<span class="pill ${o.status}">${LBL[o.status]}</span> <small style="display:inline">Participated: ${o.stats.participants} of ${o.stats.voters}</small>
<div class="row" style="margin-top:12px"><button class="btn green" data-act="start">Start Voting</button><button class="btn red" data-act="stop">Stop Voting</button><button class="btn warn" data-act="cancel">Cancel Election</button><button class="btn purple" data-act="restart">Restart Election</button></div><div id="o" role="alert"></div>
<button class="btn alt" ${go("home")}>Voter view (I can vote too)</button>`);
}
async function cats() {
  const [c, k] = await Promise.all([api("/admin/categories"), api("/admin/candidates")]);
  page("Category Management", `<button class="btn sm" style="float:right" ${go("catform")}>+ Add Category</button><div style="clear:both"></div><div id="o" role="alert"></div><table><tr><th>#</th><th>Category Name</th><th>Contestants</th><th></th></tr>
${c.map((x, i) => `<tr><td>${i + 1}</td><td>${esc(x.name)}${x.active ? "" : " <small>(inactive)</small>"}</td><td>${k.filter(y => y.active && y.category_id === x.id).length}</td><td><button class="ib" aria-label="Edit" ${go("catform/" + x.id)}>&#9998;</button><button class="ib del" aria-label="Remove" data-del="categories/${x.id}">&#128465;</button></td></tr>`).join("")}</table>`, "admin");
}
async function catform(id) {
  const x = id ? (await api("/admin/categories")).find(y => y.id == id) : null;
  page(x ? "Edit Category" : "Add Category", `<label for="n">Category Name *</label><input id="n" maxlength="120" placeholder="e.g. Director of Technology" value="${esc(x?.name)}">
<label>Status</label><label style="font-weight:400"><input type="radio" name="st" value="1" style="width:auto" ${!x || x.active ? "checked" : ""}> Active</label><label style="font-weight:400"><input type="radio" name="st" value="0" style="width:auto" ${x && !x.active ? "checked" : ""}> Inactive</label>
<button class="btn" id="sv">Save Category</button><div id="o" role="alert"></div>`, "cats");
  $("#sv").onclick = async () => { try { const b = {name: $("#n").value, active: $('input[name=st]:checked').value === "1"}; x ? await api("/admin/categories/" + x.id, "PUT", b) : await api("/admin/categories", "POST", b); location.hash = "cats"; } catch (e) { note(e.message); } };
}
async function cands() {
  const [c, k] = await Promise.all([api("/admin/categories"), api("/admin/candidates")]), nm = Object.fromEntries(c.map(x => [x.id, x.name]));
  page("Contestant Management", `<div style="display:flex;gap:8px"><input id="q" placeholder="Search contestants..." aria-label="Search"><button class="btn sm" ${go("candform")}>+ Add</button></div><div id="o" role="alert"></div><table id="t"></table>`, "admin");
  const draw = () => { const q = $("#q").value.toLowerCase(); $("#t").innerHTML = '<tr><th>Name</th><th>Category</th><th></th></tr>' + k.filter(x => x.active && x.name.toLowerCase().includes(q)).map(x => `<tr><td>${esc(x.name)}</td><td>${esc(nm[x.category_id])}</td><td><button class="ib" aria-label="Edit" ${go("candform/" + x.id)}>&#9998;</button><button class="ib del" aria-label="Remove" data-del="candidates/${x.id}">&#128465;</button></td></tr>`).join(""); };
  $("#q").oninput = draw; draw();
}
async function candform(id) {
  const [c, k] = await Promise.all([api("/admin/categories"), api("/admin/candidates")]), x = id ? k.find(y => y.id == id) : null;
  page(x ? "Edit Contestant" : "Add Contestant", `<label for="kc">Category</label><select id="kc">${c.filter(y => y.active).map(y => `<option value="${y.id}" ${x?.category_id === y.id ? "selected" : ""}>${esc(y.name)}</option>`).join("")}</select>
<label for="kn">Full name *</label><input id="kn" maxlength="120" value="${esc(x?.name)}"><label for="kd">Department</label><input id="kd" maxlength="120" value="${esc(x?.department)}">
<label for="km">Matric number</label><input id="km" maxlength="40" value="${esc(x?.matric)}"><label for="kp">Photo URL (https)</label><input id="kp" inputmode="url" value="${esc(x?.photo_url)}">
<label for="kt">Manifesto (optional)</label><textarea id="kt" rows="4" maxlength="2000">${esc(x?.manifesto)}</textarea><button class="btn" id="sv">Save Contestant</button><div id="o" role="alert"></div>`, "cands");
  $("#sv").onclick = async () => { try { const b = {category_id: +$("#kc").value, name: $("#kn").value, department: $("#kd").value, matric: $("#km").value, photo_url: $("#kp").value, manifesto: $("#kt").value}; x ? await api("/admin/candidates/" + x.id, "PUT", b) : await api("/admin/candidates", "POST", b); location.hash = "cands"; } catch (e) { note(e.message); } };
}
async function control() {
  const o = await api("/admin/overview");
  page("Election Control", `<div class="box"><b>Election Status</b><div style="margin:6px 0"><span class="pill ${o.status}">${LBL[o.status]}</span></div><small>Start: ${fmt(o.opened_at)}</small><small>End: ${fmt(o.closed_at)}</small><small>Session #${o.election_id}</small></div>
<div class="row"><button class="btn green" data-act="start">Start Voting</button><button class="btn red" data-act="stop">Stop Voting</button></div><div class="row" style="margin-top:10px"><button class="btn warn" data-act="cancel">Cancel Election</button><button class="btn purple" data-act="restart">Restart Election</button></div><div id="o" role="alert"></div>
<div class="box" style="margin-top:12px"><b>Face data</b><small>Committee override if a real student was wrongly blocked.</small><label for="fm">Matric number to reset</label><input id="fm" autocapitalize="characters" placeholder="e.g. 23L1CS0001"><button class="btn alt" data-act="facereset">Reset this voter's face</button><button class="btn red" data-act="facepurge">Delete ALL face data</button></div>
<div class="msg warn"><b>Warning</b><br>Cancelling the election invalidates all current votes. A fresh election starts with zero votes and a new session.</div>`, "admin");
}
async function pdf() {
  page("Official Results PDF", `<p class="sub">Generate the official results report (available only after voting has closed).</p><button class="btn" id="dl">Download Results PDF</button><div id="o" role="alert"></div>
<div class="box"><b>Report Includes:</b><ul class="check"><li>All categories and contestants</li><li>Final vote counts and percentages</li><li>Winners and tie notices</li><li>Total participation statistics</li><li>Election dates and report generation time</li></ul></div>`, "admin");
  $("#dl").onclick = async () => { try { const r = await fetch("/api/admin/results.pdf", {credentials: "same-origin"}); if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "PDF failed");
    const u = URL.createObjectURL(await r.blob()), a = document.createElement("a"); a.href = u; a.download = "nacos-custech-results.pdf"; a.click(); URL.revokeObjectURL(u); note("PDF downloaded.", 1); } catch (e) { note(e.message); } };
}
async function audit() {
  const a = await api("/admin/audit");
  page("Audit Log", `<div style="overflow-x:auto"><table><tr><th>Time (UTC)</th><th>Action</th><th>Actor</th><th>Detail</th></tr>${a.map(x => `<tr><td>${esc(x.at.slice(0, 16).replace("T", " "))}</td><td>${esc(x.action)}</td><td>${esc(x.actor)}</td><td>${esc(x.detail)}</td></tr>`).join("")}</table></div>`, "admin");
}
async function act(a) {
  const run = async f => { try { await f(); await route(); setTimeout(() => note("Done.", 1), 0); } catch (e) { note(e.message); } };
  if (a === "start") { if (confirm("Start voting now?")) run(() => api("/admin/election/start", "POST", {})); }
  else if (a === "stop") { if (confirm("Stop voting? Voters will no longer be able to vote.")) run(() => api("/admin/election/stop", "POST", {})); }
  else if (a === "facereset") { const m = $("#fm").value.trim(); if (m && confirm("Remove the stored face for " + m + "? They must register a face again.")) run(() => api("/admin/face/reset", "POST", {matric: m})); }
  else if (a === "facepurge") { if (confirm("Delete ALL stored face data? Do this only after the election. Voters would have to register faces again.") && confirm("Really delete all face data? This cannot be undone.")) run(() => api("/admin/face/purge", "POST", {confirm: true})); }
  else { const r = prompt(a === "cancel" ? "Reason for cancelling (required):" : "Reason for restarting (required). This cancels the current election and starts a new one:");
    if (r && confirm("This cannot be undone. All votes in the current session will be excluded. Continue?")) run(async () => { await api("/admin/election/cancel", "POST", {reason: r, confirm: true}); if (a === "restart") await api("/admin/election/new", "POST", {}); }); }
}
document.addEventListener("click", async e => {
  const g = e.target.closest("[data-go]"); if (g) { location.hash = g.dataset.go; return; }
  const a = e.target.closest("[data-act]"); if (a) return act(a.dataset.act);
  const d = e.target.closest("[data-del]"); if (d && confirm("Remove this item? Records are kept for audit.")) { try { await api("/admin/" + d.dataset.del, "DELETE"); route(); } catch (er) { note(er.message); } }
});
const R = {splash, login, face, home, vote, live, results, admin, cats, catform, cands, candform, control, pdf, audit}, ADMIN = ["admin", "cats", "catform", "cands", "candform", "control", "pdf", "audit"];
async function route() {
  clearInterval(timer); stopCam(); const [n, arg] = (location.hash.slice(1) || "splash").split("/");
  if (!["splash", "login"].includes(n) && !S.csrf) { location.hash = "login"; return; }
  if (ADMIN.includes(n) && !S.admin) { location.hash = "home"; return; }
  try { await (R[n] || splash)(arg); window.scrollTo(0, 0); } catch (e) { if (S.csrf) page("Something went wrong", `<div class="msg err">${esc(e.message)}</div><button class="btn" data-go="${S.admin ? "admin" : "home"}">Back</button>`); }
}
addEventListener("hashchange", route); route();
