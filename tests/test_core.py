import pytest
from werkzeug.security import generate_password_hash
from votingapp import create_app
from votingapp.models import db, Category, Candidate
from votingapp.core import is_eligible, normalize_phone

ADM, ADMP, PW = "23L1CSS0055", "07036779507", "correct-horse-battery"
@pytest.fixture
def app():
    a = create_app(dict(SECRET_KEY="t", PHONE_PEPPER="p", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SESSION_COOKIE_SECURE=False, AUTO_INIT_DB=False, FACE_ENABLED=False,
                        ADMIN_MATRIC=ADM, ADMIN_PHONE=ADMP, ADMIN_PASSWORD_HASH=generate_password_hash(PW)))
    with a.app_context():
        db.create_all(); c = Category(name="Pres", position=1); db.session.add(c); db.session.flush()
        db.session.add_all([Candidate(category_id=c.id, name="A"), Candidate(category_id=c.id, name="B")]); db.session.commit()
        yield a
def login(a, m, p, **k):
    c = a.test_client(); return c, c.post("/api/login", json=dict(matric=m, phone=p, **k))
def H(r): return {"X-CSRF-Token": r.json["csrf"]}

def test_strict_roll_40_groups_any_4_digit_serial():
    from votingapp.core import ELIGIBLE, ELIGIBLE_L1, ELIGIBLE_L2
    assert len(ELIGIBLE_L1) == len(ELIGIBLE_L2) == 20 and len(set(ELIGIBLE)) == 40
    ok = [f"{p}{n:04d}" for p in ELIGIBLE for n in (1, 2, 300, 301, 999, 1000, 4567, 9999)]
    assert all(is_eligible(m) for m in ok)
    assert is_eligible(" 23l2cs 0301 ") and is_eligible("26L2LI9999") and is_eligible("25L2SE0450") and is_eligible("23L1CS0999")
    assert is_eligible("23L1CS100") and is_eligible("23l2cs001") and is_eligible("25L1SE999") and is_eligible("24LSE8602") and is_eligible("26L2FT8602")
    for bad in ["23L1CS0000", "23L2CS0000", "23L1CS000", "23L2CS000", "23L1CS01", "23L1CS1", "23L1CS10000", "23L2CS00001", "23L1CS", "23L1CSabc", "23L2CS0001X", "X23L2CS0001",
                "CUST/23L2CS/0001", "23L1CS-0001", "23L1CSS0055", "25LSE0001", "23L1SE0001", "23LSE0001x", "22L2CS0001", "23L3CS0001", "23L2CS000a",
                "23L1CS0001\u0663", "", None]:
        assert not is_eligible(bad), bad
    assert is_eligible("23L1CSS0055", "23L1CSS0055") and not is_eligible("23L1CSS0056", "23L1CSS0055")

def test_phone():
    assert normalize_phone("0703 677 9507") == normalize_phone("+2347036779507") == "+2347036779507"
    assert normalize_phone("123") is None
def test_login_and_identity_rules(app):
    assert login(app, "23L1CS0001", "08011111111")[1].status_code == 200
    assert login(app, "23L1CS0001", "08022222222")[1].status_code == 401
    assert login(app, "23L1CS0002", "08011111111")[1].status_code == 401
    assert login(app, "23L1CS0000", "08033333333")[1].status_code == 401
    assert login(app, "23L2CS0001", "08044444444")[1].status_code == 200 and login(app, "23L2CS0301", "08055555555")[1].status_code == 200
def test_admin_needs_password(app):
    assert login(app, ADM, ADMP)[1].status_code == 401
    assert login(app, ADM, ADMP, admin_password="wrong")[1].status_code == 401
    assert login(app, ADM, ADMP, admin_password=PW)[1].json["admin"]
def test_non_admin_forbidden_and_csrf(app):
    c, r = login(app, "23L1CS0001", "08011111111")
    assert c.get("/api/admin/overview").status_code == 403
    assert c.post("/api/admin/election/start", json={}).status_code == 403
def test_full_lifecycle(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    v, rv = login(app, "24L1FT0007", "09012345678"); hv = H(rv)
    b = v.get("/api/ballot").json["categories"][0]; cat, cands = b["id"], b["candidates"]
    vote = lambda i: v.post("/api/vote", json=dict(category_id=cat, candidate_id=cands[i]["id"]), headers=hv).status_code
    assert vote(0) == 409 and a.get("/api/admin/results.pdf").status_code == 409
    assert a.post("/api/admin/election/start", json={}, headers=ha).status_code == 200
    assert a.post("/api/admin/categories", json=dict(name="X"), headers=ha).status_code == 409
    assert (vote(0), vote(0), vote(1)) == (200, 200, 200)
    r = v.get("/api/results").json
    assert r["label"] == "PROVISIONAL" and r["categories"][0]["total"] == 1
    assert sorted(x["votes"] for x in r["categories"][0]["candidates"]) == [0, 1]
    assert v.get("/api/admin/audit").status_code == 403
    assert a.post("/api/admin/election/stop", json={}, headers=ha).status_code == 200
    assert vote(0) == 409
    r = v.get("/api/results").json; assert r["label"] == "FINAL" and r["categories"][0]["status"] == "winner"
    p = a.get("/api/admin/results.pdf"); assert p.status_code == 200 and p.data[:4] == b"%PDF"
    assert v.get("/api/admin/results.pdf").status_code == 403
    assert a.post("/api/admin/election/cancel", json=dict(reason="x", confirm=True), headers=ha).status_code == 400
    assert a.post("/api/admin/election/cancel", json=dict(reason="Disputed roll", confirm=True), headers=ha).status_code == 200
    assert a.post("/api/admin/election/new", json={}, headers=ha).status_code == 200
    assert v.get("/api/results").json["categories"][0]["total"] == 0
    assert "election_cancel" in [x["action"] for x in a.get("/api/admin/audit").json]
def test_tie(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    a.post("/api/admin/election/start", json={}, headers=ha)
    cs = a.get("/api/ballot").json["categories"][0]
    for i, m in enumerate(("24L1CS1", "24L1CS2")):
        c, r = login(app, m, f"0801000000{i}"); c.post("/api/vote", json=dict(category_id=cs["id"], candidate_id=cs["candidates"][i]["id"]), headers=H(r))
    a.post("/api/admin/election/stop", json={}, headers=ha)
    assert a.get("/api/admin/overview", ).json["results"][0]["status"] == "tie"

def test_health(app):
    j = app.test_client().get("/api/health").json; assert j["ok"] and j["db"] and j["admin_configured"]


# ---------- face check ----------
@pytest.fixture
def face_app(app):
    app.config.update(FACE_ENABLED=True); return app
def vec(base, jitter=0.0): return [base + (jitter if i % 2 else -jitter) for i in range(128)]
def face(c, r, v, consent=True): return c.post("/api/face", json=dict(descriptor=v, consent=consent), headers=H(r))

def test_face_required_before_ballot_and_vote(face_app):
    c, r = login(face_app, "23L1CS0001", "08011111111"); assert r.json["face_required"] is True
    b = c.get("/api/ballot"); assert b.status_code == 403 and b.json["code"] == "face_required"
    assert c.post("/api/vote", json=dict(category_id=1, candidate_id=1), headers=H(r)).status_code == 403
    assert face(c, r, vec(0.1)).json["enrolled"] is True
    assert c.get("/api/ballot").status_code == 200
def test_same_face_cannot_be_reused_for_another_matric(face_app):
    c1, r1 = login(face_app, "23L1CS0001", "08011111111"); assert face(c1, r1, vec(0.1)).status_code == 200
    c2, r2 = login(face_app, "23L1CS0002", "08022222222")
    assert face(c2, r2, vec(0.1, 0.002)).status_code == 409                        # same person, slightly different scan
    assert c2.get("/api/ballot").status_code == 403
    assert face(c2, r2, vec(0.3)).status_code == 200                               # a different person is fine
def test_returning_voter_must_match_own_face(face_app):
    c, r = login(face_app, "23L1CS0001", "08011111111"); face(c, r, vec(0.1))
    c, r = login(face_app, "23L1CS0001", "08011111111"); assert r.json["face_required"] is True
    assert face(c, r, vec(0.3)).status_code == 403 and c.get("/api/ballot").status_code == 403
    assert face(c, r, vec(0.1, 0.002)).json["enrolled"] is False and c.get("/api/ballot").status_code == 200
def test_face_rejects_bad_input_and_needs_consent(face_app):
    c, r = login(face_app, "23L1CS0001", "08011111111")
    assert face(c, r, vec(0.1), consent=False).status_code == 400
    for bad in [[0.1] * 127, [0.1] * 129, ["a"] * 128, [float("inf")] * 128, [0.0] * 128, [5.0] * 128, None, "x"]:
        assert c.post("/api/face", json=dict(descriptor=bad, consent=True), headers=H(r)).status_code == 400
def test_face_admin_exempt_reset_and_purge(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); ha = H(ra)
    assert ra.json["face_required"] is False and a.get("/api/ballot").status_code == 200
    c, r = login(face_app, "23L1CS0001", "08011111111"); face(c, r, vec(0.1))
    assert c.post("/api/admin/face/reset", json=dict(matric="23L1CS0001"), headers=H(r)).status_code == 403        # voters cannot reset
    assert a.post("/api/admin/face/reset", json=dict(matric="23L1CS0001"), headers=ha).json["removed"] == 1
    c2, r2 = login(face_app, "23L1CS0002", "08022222222"); assert face(c2, r2, vec(0.1)).status_code == 200         # face is free again
    assert a.post("/api/admin/face/purge", json={}, headers=ha).status_code == 400
    assert a.post("/api/admin/face/purge", json=dict(confirm=True), headers=ha).json["removed"] == 1
def test_face_can_be_switched_off(app):
    c, r = login(app, "23L1CS0001", "08011111111"); assert r.json["face_required"] is False and c.get("/api/ballot").status_code == 200
