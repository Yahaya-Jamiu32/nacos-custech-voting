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
    for i, m in enumerate(("24L1CS0001", "24L1CS0002")):
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
def test_face_duplicate_limit_is_stricter_than_own_face_check(face_app):
    c1, r1 = login(face_app, "23L1CS0001", "08011111111"); assert face(c1, r1, vec(0.1)).status_code == 200
    c2, r2 = login(face_app, "23L1CS0002", "08022222222")
    assert face(c2, r2, vec(0.1265)).status_code == 409    # distance 0.30 from the stored face: clearly the same face
    assert face(c2, r2, vec(0.1398)).status_code == 200    # distance 0.45: a different person (the old single 0.55 limit wrongly blocked this)

def test_face_rejects_bad_input_and_needs_consent(face_app):
    c, r = login(face_app, "23L1CS0001", "08011111111")
    assert face(c, r, vec(0.1), consent=False).status_code == 400
    for bad in [[0.1] * 127, [0.1] * 129, ["a"] * 128, [float("inf")] * 128, [0.0] * 128, [5.0] * 128, [10 ** 400] * 128, None, "x"]:
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


# ---------- special (bad camera) logins ----------
import re as _re
def issue(a, h, note="Ada"): return a.post("/api/admin/special", json=dict(note=note), headers=h).json["codes"][0]
def special_login(a, m, p):
    c = a.test_client(); return c, c.post("/api/login", json=dict(matric=m, phone=p, bad_camera=True))

def test_special_code_format_only_admin_can_issue(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); ha = H(ra)
    code = issue(a, ha); assert _re.fullmatch(r"30L1PC[A-Z0-9]{4}", code)
    c, r = login(face_app, "23L1CS0001", "08011111111")
    assert c.post("/api/admin/special", json={}, headers=H(r)).status_code == 403 and c.get("/api/admin/special").status_code == 403
def test_special_login_skips_face_but_only_for_issued_codes(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); code = issue(a, H(ra))
    c, r = special_login(face_app, code, "08011111111")
    assert r.status_code == 200 and r.json["face_required"] is False and c.get("/api/ballot").status_code == 200   # no face scan needed
    assert special_login(face_app, "30L1PCZZZZ", "08022222222")[1].status_code == 401          # right pattern, never issued
    assert login(face_app, code, "08033333333")[1].status_code == 401                          # a special code cannot use the normal login
    assert special_login(face_app, "23L1CS0001", "08044444444")[1].status_code == 401          # a student matric cannot use the bad-camera login
    assert special_login(face_app, ADM, ADMP)[1].status_code == 401                            # nor can the admin matric
def test_special_code_binds_to_first_phone_and_phone_not_shared(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); ha = H(ra); c1, c2 = issue(a, ha), issue(a, ha, "Bola")
    assert special_login(face_app, c1, "08011111111")[1].status_code == 200
    assert special_login(face_app, c1, "08099999999")[1].status_code == 401                    # someone else with the leaked code
    assert special_login(face_app, c2, "08011111111")[1].status_code == 401                    # phone already used by another matric
def test_special_revoke_blocks_login_and_ends_session(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); ha = H(ra); code = issue(a, ha)
    c, r = special_login(face_app, code, "08011111111"); assert c.get("/api/ballot").status_code == 200
    assert a.post("/api/admin/special/revoke", json=dict(matric=code), headers=ha).status_code == 200
    assert c.get("/api/ballot").status_code == 401 and special_login(face_app, code, "08011111111")[1].status_code == 401
    row = a.get("/api/admin/special").json[0]; assert row["matric"] == code and row["revoked"] is True and row["used"] is True

def test_special_session_never_enrols_a_face(face_app):
    a, ra = login(face_app, ADM, ADMP, admin_password=PW); code = issue(a, H(ra))
    c, r = special_login(face_app, code, "08011111111")
    assert c.post("/api/face", json=dict(descriptor=vec(0.1), consent=True), headers=H(r)).status_code == 200
    c2, r2 = login(face_app, "23L1CS0001", "08022222222")
    assert face(c2, r2, vec(0.1)).json["enrolled"] is True                                  # the special user did not use up this face
def test_repeated_duplicate_scans_are_locked_out(face_app):
    c1, r1 = login(face_app, "23L1CS0001", "08011111111"); face(c1, r1, vec(0.1))
    c2, r2 = login(face_app, "23L1CS0002", "08022222222")
    codes = [face(c2, r2, vec(0.1)).status_code for _ in range(11)]
    assert codes[:10] == [409] * 10 and codes[10] == 429


# ---------- voting timer ----------
def test_timer_stops_voting_automatically(app):
    from datetime import timedelta
    from votingapp.models import Election, utcnow
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    v, rv = login(app, "24L1FT0007", "09012345678"); hv = H(rv)
    start = lambda **k: a.post("/api/admin/election/start", json=k, headers=ha).status_code
    assert start(minutes=0) == 400 and start(minutes="abc") == 400 and start(minutes=10081) == 400 and start(minutes=True) == 400
    assert start(minutes=30) == 200
    j = v.get("/api/ballot").json; cat, cands = j["categories"][0]["id"], j["categories"][0]["candidates"]
    assert j["status"] == "open" and 1790 <= j["seconds_left"] <= 1800 and 1790 <= v.get("/api/results").json["seconds_left"] <= 1800
    vote = lambda: v.post("/api/vote", json=dict(category_id=cat, candidate_id=cands[0]["id"]), headers=hv).status_code
    assert vote() == 200
    e = Election.query.order_by(Election.id.desc()).first(); e.closes_at = utcnow() - timedelta(seconds=1); db.session.commit()   # time runs out
    assert vote() == 409
    j = v.get("/api/ballot").json; assert j["status"] == "closed" and j["seconds_left"] is None
    assert v.get("/api/results").json["label"] == "FINAL"
    assert "election_auto_stop" in [x["action"] for x in a.get("/api/admin/audit").json]

def test_no_timer_when_minutes_not_given(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    assert a.post("/api/admin/election/start", json={}, headers=ha).status_code == 200
    assert a.get("/api/ballot").json["seconds_left"] is None


# ---------- admin: clear stored voter logins ----------
def test_admin_clears_one_voter_and_their_vote(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    v, rv = login(app, "24L1FT0007", "09011111111"); hv = H(rv)   # first login used a wrong phone number by mistake
    a.post("/api/admin/election/start", json={}, headers=ha)
    b = v.get("/api/ballot").json["categories"][0]
    cast = lambda c, h: c.post("/api/vote", json=dict(category_id=b["id"], candidate_id=b["candidates"][0]["id"]), headers=h).status_code
    total = lambda: a.get("/api/results").json["categories"][0]["total"]
    assert cast(v, hv) == 200 and total() == 1
    assert login(app, "24L1FT0007", "09022222222")[1].status_code == 401   # the correct phone is now refused: the problem being fixed
    clear = lambda **k: a.post("/api/admin/voters/clear", json=k, headers=ha)
    assert clear().status_code == 400 and clear(phone="123").status_code == 400 and clear(matric="24L1FT0999").status_code == 404
    p = clear(matric="24L1FT0007", phone="09022222222")   # preview only: nothing is deleted yet
    assert p.status_code == 200 and p.json["matches"] == [dict(matric="24L1FT0007", votes=1, face=False)] and total() == 1
    r = clear(matric="24L1FT0007", phone="09022222222", confirm=True)
    assert r.status_code == 200 and (r.json["voters"], r.json["votes"]) == (1, 1) and total() == 0
    assert v.get("/api/ballot").status_code == 401   # the old session ends at once
    v2, rv2 = login(app, "24L1FT0007", "09022222222"); assert rv2.status_code == 200
    assert cast(v2, H(rv2)) == 200 and total() == 1   # votes again with the right details
    assert "voter_cleared" in [x["action"] for x in a.get("/api/admin/audit").json]

def test_clear_matches_by_phone_or_by_matric_and_is_admin_only(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    login(app, "24L1FT0001", "09033333333"); login(app, "24L1FT0002", "09044444444")
    clear = lambda **k: a.post("/api/admin/voters/clear", json=k, headers=ha)
    assert [m["matric"] for m in clear(phone="+234 903 333 3333").json["matches"]] == ["24L1FT0001"]   # phone only
    assert [m["matric"] for m in clear(matric="24l1ft0002").json["matches"]] == ["24L1FT0002"]          # matric only
    assert [m["matric"] for m in clear(matric="24L1FT0001", phone="09044444444").json["matches"]] == ["24L1FT0001", "24L1FT0002"]   # either one matches
    assert clear(matric=ADM).status_code == 404   # the admin's own record is never cleared
    v, rv = login(app, "24L1FT0003", "09055555555")
    assert v.post("/api/admin/voters/clear", json=dict(matric="24L1FT0001", confirm=True), headers=H(rv)).status_code == 403
    assert v.post("/api/admin/voters/clear-all", json=dict(confirm=True), headers=H(rv)).status_code == 403

def test_clear_all_voters_keeps_admin_and_lets_everyone_login_fresh(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    a.post("/api/admin/election/start", json={}, headers=ha)
    b = a.get("/api/ballot").json["categories"][0]; users = []
    for i in (1, 2):
        c, r = login(app, f"24L1FT000{i}", f"0906000000{i}"); users.append(c)
        assert c.post("/api/vote", json=dict(category_id=b["id"], candidate_id=b["candidates"][0]["id"]), headers=H(r)).status_code == 200
    assert a.post("/api/admin/voters/clear-all", json={}, headers=ha).status_code == 400   # needs confirmation
    r = a.post("/api/admin/voters/clear-all", json=dict(confirm=True), headers=ha)
    assert r.status_code == 200 and (r.json["voters"], r.json["votes"]) == (2, 2)
    o = a.get("/api/admin/overview"); assert o.status_code == 200 and o.json["stats"]["voters"] == 1 and o.json["results"][0]["total"] == 0   # admin stays logged in
    assert all(c.get("/api/ballot").status_code == 401 for c in users)
    assert login(app, "24L1FT0001", "09077777777")[1].status_code == 200   # different phone now accepted

def test_cannot_clear_voters_after_voting_closed(app):
    a, ra = login(app, ADM, ADMP, admin_password=PW); ha = H(ra)
    login(app, "24L1FT0001", "09033333333")
    a.post("/api/admin/election/start", json={}, headers=ha); a.post("/api/admin/election/stop", json={}, headers=ha)
    assert a.post("/api/admin/voters/clear", json=dict(matric="24L1FT0001", confirm=True), headers=ha).status_code == 409
    assert a.post("/api/admin/voters/clear-all", json=dict(confirm=True), headers=ha).status_code == 409
