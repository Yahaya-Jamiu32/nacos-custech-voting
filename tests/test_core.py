import pytest
from werkzeug.security import generate_password_hash
from votingapp import create_app
from votingapp.models import db, Category, Candidate
from votingapp.core import is_eligible, normalize_phone

ADM, ADMP, PW = "23L1CSS0055", "07036779507", "correct-horse-battery"
@pytest.fixture
def app():
    a = create_app(dict(SECRET_KEY="t", PHONE_PEPPER="p", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SESSION_COOKIE_SECURE=False, AUTO_INIT_DB=False,
                        ADMIN_MATRIC=ADM, ADMIN_PHONE=ADMP, ADMIN_PASSWORD_HASH=generate_password_hash(PW)))
    with a.app_context():
        db.create_all(); c = Category(name="Pres", position=1); db.session.add(c); db.session.flush()
        db.session.add_all([Candidate(category_id=c.id, name="A"), Candidate(category_id=c.id, name="B")]); db.session.commit()
        yield a
def login(a, m, p, **k):
    c = a.test_client(); return c, c.post("/api/login", json=dict(matric=m, phone=p, **k))
def H(r): return {"X-CSRF-Token": r.json["csrf"]}

def test_strict_roll_40_groups_x_300():
    from votingapp.core import ELIGIBLE, ELIGIBLE_L1, ELIGIBLE_L2
    assert len(ELIGIBLE_L1) == len(ELIGIBLE_L2) == 20 and len(set(ELIGIBLE)) == 40
    ok = [f"{p}{n:04d}" for p in ELIGIBLE for n in range(1, 301)]
    assert len(ok) == 12000 and all(is_eligible(m) for m in ok)
    assert is_eligible(" 23l2cs 0001 ") and is_eligible("26L2LI0300") and is_eligible("25L2SE0150")
    for bad in ["23L1CS0000", "23L1CS0301", "23L2CS0301", "23L2CS0000", "23L2CS001", "23L2CS0001X", "X23L2CS0001", "CUST/23L2CS/0001",
                "23L1CSS0055", "25LSE0001", "23L1SE0001", "23LSE0001x", "22L2CS0001", "23L3CS0001", "23L2CS000a", "23L1CS0001\u0663", "", None]:
        assert not is_eligible(bad), bad
    assert is_eligible("23L1CSS0055", "23L1CSS0055") and not is_eligible("23L1CSS0056", "23L1CSS0055")

def test_phone():
    assert normalize_phone("0703 677 9507") == normalize_phone("+2347036779507") == "+2347036779507"
    assert normalize_phone("123") is None
def test_login_and_identity_rules(app):
    assert login(app, "23L1CS0001", "08011111111")[1].status_code == 200
    assert login(app, "23L1CS0001", "08022222222")[1].status_code == 401
    assert login(app, "23L1CS0002", "08011111111")[1].status_code == 401
    assert login(app, "23L1CS0301", "08033333333")[1].status_code == 401
    assert login(app, "23L2CS0001", "08044444444")[1].status_code == 200 and login(app, "23L2CS0301", "08055555555")[1].status_code == 401
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
