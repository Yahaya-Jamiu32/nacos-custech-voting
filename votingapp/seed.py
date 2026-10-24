from .models import db, Category
NAMES = ["Chapter President","Vice President (Administration)","Vice President (Special Duties)","Secretary-General",
 "Assistant Secretary-General","Director of Finance","Director of Research and Innovation","Director of Publicity and Media",
 "Director of Welfare","Director of Academic Planning","Director of Transport and Logistics","Provost Marshal","Financial Secretary",
 "Director of Sport","Director of Feminine Gender","Senate President","Senate Clerk","Deputy Senate President",
 "PENDING: category 19 - name awaiting official election document","Departmental Presidents/Representatives"]

def seed():
    """Create tables; seed categories only if none exist (idempotent, safe on every cold start)."""
    db.create_all()
    if Category.query.count() == 0:
        for i, n in enumerate(NAMES, 1): db.session.add(Category(name=n, position=i, active=(i != 19)))
        db.session.commit()
