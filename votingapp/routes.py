import secrets, io
from datetime import timedelta
from functools import wraps
from flask import Blueprint, request, session, jsonify, send_file, current_app
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from .models import db, Voter, Election, Category, Candidate, Vote, Audit, utcnow
from .core import is_eligible, normalize_phone, phone_hash, norm_matric
from .pdfgen import build_pdf

bp = Blueprint("api", __name__, url_prefix="/api")
def err(msg, code=400): return jsonify(error=msg), code
def ip(): return (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.remote_addr or "")[:64]
def audit(action, detail="", actor=None):
    db.session.add(Audit(action=action, detail=detail, actor=actor or session.get("matric"), ip=ip()))

@bp.before_request
def csrf_guard():
    if request.method in ("POST", "PUT", "DELETE") and request.endpoint != "api.login":
        if not session.get("csrf") or request.headers.get("X-CSRF-Token") != session["csrf"]:
            return err("Invalid request token.", 403)

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("voter_id"): return err("Please log in.", 401)
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    @login_required
    def w(*a, **k):  # re-verified server-side on every call
        if not session.get("admin") or session.get("matric") != norm_matric(current_app.config["ADMIN_MATRIC"]):
            return err("Forbidden.", 403)
        return f(*a, **k)
    return w

def current_election():
    e = Election.query.filter(Election.status != "cancelled").order_by(Election.id.desc()).first()
    if not e:
        e = Election(status="draft"); db.session.add(e); db.session.commit()
    return e

def toint(v):
    try: return int(v)
    except (TypeError, ValueError): return 0

def locked(eid): return db.session.query(Election).filter_by(id=eid).with_for_update().one()

@bp.get("/health")
def health():
    """Post-deploy check: open https://YOUR-SITE/api/health. Shows no secrets."""
    try:
        db.session.execute(text("select 1"))
        return jsonify(ok=True, db=True, admin_configured=bool(current_app.config["ADMIN_MATRIC"] and current_app.config["ADMIN_PHONE"] and current_app.config["ADMIN_PASSWORD_HASH"]))
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(ok=False, db=False), 503

# ---------- auth ----------
@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}; cfg = current_app.config
    if Audit.query.filter(Audit.action == "login_failed", Audit.ip == ip(), Audit.at > utcnow() - timedelta(minutes=10)).count() >= cfg["LOGIN_MAX_FAILS"]:
        return err("Too many attempts. Try again later.", 429)
    def fail():
        db.session.rollback(); audit("login_failed", actor="-"); db.session.commit()
        return err("Login failed. Check your details or contact the election committee.", 401)
    matric, phone = norm_matric(d.get("matric")), normalize_phone(d.get("phone"))
    if not matric or len(matric) > 40 or not phone or not is_eligible(matric): return fail()
    is_admin = bool(cfg["ADMIN_MATRIC"]) and matric == norm_matric(cfg["ADMIN_MATRIC"])
    if is_admin and (phone != normalize_phone(cfg["ADMIN_PHONE"]) or not cfg["ADMIN_PASSWORD_HASH"]
                     or not check_password_hash(cfg["ADMIN_PASSWORD_HASH"], str(d.get("admin_password") or ""))):
        return fail()
    ph = phone_hash(phone, cfg["PHONE_PEPPER"])
    v = Voter.query.filter_by(matric=matric).first()
    if v:
        if v.phone_hash != ph: return fail()
    else:
        if Voter.query.filter_by(phone_hash=ph).first(): return fail()
        v = Voter(matric=matric, phone_hash=ph); db.session.add(v)
        try: db.session.flush()
        except IntegrityError: return fail()
    audit("login_admin" if is_admin else "login", actor=matric); db.session.commit()
    session.clear(); session.permanent = True
    session.update(voter_id=v.id, matric=matric, admin=is_admin, csrf=secrets.token_hex(16))
    return jsonify(csrf=session["csrf"], admin=is_admin)

@bp.post("/logout")
def logout(): session.clear(); return jsonify(ok=True)

@bp.get("/me")
@login_required
def me(): return jsonify(matric=session["matric"], admin=session["admin"], csrf=session["csrf"])

# ---------- ballot / vote ----------
@bp.get("/ballot")
@login_required
def ballot():
    e = current_election()
    mine = {v.category_id: v.candidate_id for v in Vote.query.filter_by(election_id=e.id, voter_id=session["voter_id"])}
    cats = []
    for c in Category.query.filter_by(active=True).order_by(Category.position, Category.id):
        cs = Candidate.query.filter_by(category_id=c.id, active=True).order_by(Candidate.name).all()
        if cs: cats.append(dict(id=c.id, name=c.name, selected=mine.get(c.id), candidates=[
            dict(id=x.id, name=x.name, department=x.department, manifesto=x.manifesto, photo_url=x.photo_url) for x in cs]))
    return jsonify(status=e.status, election_id=e.id, categories=cats)

@bp.post("/vote")
@login_required
def vote():
    d = request.get_json(silent=True) or {}
    try: cid, kid = int(d.get("category_id")), int(d.get("candidate_id"))
    except (TypeError, ValueError): return err("Invalid selection.")
    e = locked(current_election().id)   # row lock: serialises against close/cancel
    if e.status != "open": db.session.rollback(); return err("Voting is not open.", 409)
    cand = db.session.get(Candidate, kid)
    cat = db.session.get(Category, cid)
    if not cand or not cat or not cat.active or not cand.active or cand.category_id != cid:
        db.session.rollback(); return err("Invalid selection.")
    for _ in range(2):
        v = Vote.query.filter_by(election_id=e.id, voter_id=session["voter_id"], category_id=cid).first()
        try:
            if v: v.candidate_id, v.updated_at = kid, utcnow()
            else: db.session.add(Vote(election_id=e.id, voter_id=session["voter_id"], category_id=cid, candidate_id=kid))
            replaced = bool(v); db.session.commit()
            return jsonify(ok=True, category_id=cid, candidate_id=kid, replaced=replaced)
        except IntegrityError: db.session.rollback(); e = locked(e.id)
    return err("Could not record vote. Retry.", 409)

# ---------- results ----------
def tally(e):
    out = []
    for c in Category.query.filter_by(active=True).order_by(Category.position, Category.id):
        counts = dict(db.session.query(Vote.candidate_id, func.count(Vote.id)).filter(Vote.election_id == e.id, Vote.category_id == c.id).group_by(Vote.candidate_id).all())
        cs = Candidate.query.filter_by(category_id=c.id, active=True).all()
        if not cs: continue
        total = sum(counts.values())
        rows = sorted([dict(id=x.id, name=x.name, department=x.department, votes=counts.get(x.id, 0),
                            pct=round(100 * counts.get(x.id, 0) / total, 1) if total else 0.0) for x in cs], key=lambda r: -r["votes"])
        top = rows[0]["votes"]; leaders = [r["name"] for r in rows if r["votes"] == top] if total else []
        status = "empty" if total == 0 else ("tie" if len(leaders) > 1 else "winner")
        out.append(dict(id=c.id, name=c.name, total=total, candidates=rows, leaders=leaders, status=status))
    return out

def stats(e):
    return dict(voters=Voter.query.count(), participants=db.session.query(func.count(func.distinct(Vote.voter_id))).filter(Vote.election_id == e.id).scalar())

@bp.get("/results")
@login_required
def results():
    e = current_election(); final = e.status == "closed"
    r = tally(e)
    if not final:   # winners only declared after close
        for c in r: c["leaders"], c["status"] = [], "provisional"
    return jsonify(status=e.status, label="FINAL" if final else "PROVISIONAL", categories=r, stats=stats(e))

# ---------- admin: election lifecycle ----------
def transition(frm, to, action, **extra):
    e = locked(current_election().id)
    if e.status not in frm: db.session.rollback(); return err(f"Not allowed while election is {e.status}.", 409)
    e.status = to
    for k, v in extra.items(): setattr(e, k, v)
    audit(action, f"election {e.id}" + (f": {extra.get('cancel_reason')}" if "cancel_reason" in extra else ""))
    db.session.commit(); return jsonify(ok=True, status=to)

@bp.post("/admin/election/start")
@admin_required
def e_start():
    if not Candidate.query.filter_by(active=True).count(): return err("Add candidates first.", 409)
    return transition(("draft",), "open", "election_start", opened_at=utcnow())

@bp.post("/admin/election/stop")
@admin_required
def e_stop(): return transition(("open",), "closed", "election_stop", closed_at=utcnow())

@bp.post("/admin/election/cancel")
@admin_required
def e_cancel():
    d = request.get_json(silent=True) or {}
    reason = (d.get("reason") or "").strip()
    if len(reason) < 5 or d.get("confirm") is not True: return err("A reason (5+ chars) and explicit confirmation are required.")
    return transition(("draft", "open", "closed"), "cancelled", "election_cancel", cancel_reason=reason, closed_at=utcnow())

@bp.post("/admin/election/new")
@admin_required
def e_new():
    if Election.query.filter(Election.status.in_(("draft", "open", "closed"))).count():
        return err("Cancel the current election before creating a replacement.", 409)
    e = Election(status="draft"); db.session.add(e); audit("election_new"); db.session.commit()
    return jsonify(ok=True, election_id=e.id)

@bp.get("/admin/overview")
@admin_required
def overview():
    e = current_election()
    iso = lambda t: t.isoformat() if t else None
    return jsonify(status=e.status, election_id=e.id, opened_at=iso(e.opened_at), closed_at=iso(e.closed_at), stats=stats(e), results=tally(e))

def editable(): return current_election().status == "draft"
LOCKED = "Structure can only be edited before voting starts."

# ---------- admin: categories / candidates ----------
@bp.get("/admin/categories")
@admin_required
def cat_list():
    return jsonify([dict(id=c.id, name=c.name, active=c.active, position=c.position) for c in Category.query.order_by(Category.position, Category.id)])

@bp.post("/admin/categories")
@admin_required
def cat_add():
    if not editable(): return err(LOCKED, 409)
    n = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not n or len(n) > 120: return err("Name required.")
    if Category.query.filter_by(name=n).first(): return err("Category exists.", 409)
    c = Category(name=n, position=(db.session.query(func.max(Category.position)).scalar() or 0) + 1); db.session.add(c)
    audit("category_add", n); db.session.commit(); return jsonify(id=c.id), 201

@bp.put("/admin/categories/<int:i>")
@admin_required
def cat_edit(i):
    if not editable(): return err(LOCKED, 409)
    c = db.get_or_404(Category, i); d = request.get_json(silent=True) or {}
    if str(d.get("name") or "").strip(): c.name = str(d["name"]).strip()[:120]
    if "active" in d: c.active = bool(d["active"])
    audit("category_edit", str(i))
    try: db.session.commit()
    except IntegrityError: db.session.rollback(); return err("Name already used.", 409)
    return jsonify(ok=True)

@bp.delete("/admin/categories/<int:i>")
@admin_required
def cat_del(i):
    if not editable(): return err(LOCKED, 409)
    c = db.get_or_404(Category, i); c.active = False; audit("category_remove", f"{i} (soft)"); db.session.commit()
    return jsonify(ok=True)

@bp.get("/admin/candidates")
@admin_required
def cand_list():
    return jsonify([dict(id=c.id, name=c.name, category_id=c.category_id, department=c.department, matric=c.matric,
                         manifesto=c.manifesto, photo_url=c.photo_url, active=c.active) for c in Candidate.query.order_by(Candidate.category_id, Candidate.name)])

def _cand_fields(c, d):
    for k, mx in (("name", 120), ("department", 120), ("matric", 40), ("manifesto", 2000), ("photo_url", 500)):
        if k in d: setattr(c, k, (str(d[k]).strip()[:mx] or None))
    if c.photo_url and not c.photo_url.startswith("https://"): return "Photo URL must be https."
    if not c.name: return "Name required."

@bp.post("/admin/candidates")
@admin_required
def cand_add():
    if not editable(): return err(LOCKED, 409)
    d = request.get_json(silent=True) or {}; cat = db.session.get(Category, toint(d.get("category_id")))
    if not cat or not cat.active: return err("Invalid category.")
    c = Candidate(category_id=cat.id); m = _cand_fields(c, d)
    if m: return err(m)
    db.session.add(c); audit("candidate_add", c.name); db.session.commit(); return jsonify(id=c.id), 201

@bp.put("/admin/candidates/<int:i>")
@admin_required
def cand_edit(i):
    if not editable(): return err(LOCKED, 409)
    c = db.get_or_404(Candidate, i); d = request.get_json(silent=True) or {}
    if "category_id" in d:
        cat = db.session.get(Category, toint(d["category_id"]))
        if not cat or not cat.active: return err("Invalid category.")
        c.category_id = cat.id
    m = _cand_fields(c, d)
    if m: db.session.rollback(); return err(m)
    audit("candidate_edit", str(i)); db.session.commit(); return jsonify(ok=True)

@bp.delete("/admin/candidates/<int:i>")
@admin_required
def cand_del(i):
    if not editable(): return err(LOCKED, 409)
    c = db.get_or_404(Candidate, i); c.active = False; audit("candidate_remove", f"{i} (soft)"); db.session.commit()
    return jsonify(ok=True)

@bp.get("/admin/audit")
@admin_required
def audit_view():
    return jsonify([dict(at=a.at.isoformat(), action=a.action, actor=a.actor, detail=a.detail, ip=a.ip)
                    for a in Audit.query.order_by(Audit.id.desc()).limit(200)])

@bp.get("/admin/results.pdf")
@admin_required
def pdf():
    e = current_election()
    if e.status != "closed": return err("PDF is available only after voting has closed.", 409)
    try:
        data = build_pdf(e, tally(e), stats(e), utcnow().strftime("%Y-%m-%d %H:%M"))
    except Exception:
        current_app.logger.exception("PDF failure"); return err("PDF generation failed. Try again.", 500)
    audit("pdf_download", f"election {e.id}"); db.session.commit()
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=f"nacos-custech-results-{e.id}.pdf")
