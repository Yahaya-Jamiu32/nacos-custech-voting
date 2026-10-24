from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Index
db = SQLAlchemy()
def utcnow(): return datetime.now(timezone.utc).replace(tzinfo=None)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matric = db.Column(db.String(40), unique=True, nullable=False)
    phone_hash = db.Column(db.String(64), unique=True, nullable=False)  # HMAC, never plaintext
    created_at = db.Column(db.DateTime, default=utcnow)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(12), nullable=False, default="draft")  # draft|open|closed|cancelled
    opened_at = db.Column(db.DateTime); closed_at = db.Column(db.DateTime)
    cancel_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    position = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True, nullable=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    matric = db.Column(db.String(40)); department = db.Column(db.String(120))
    manifesto = db.Column(db.Text); photo_url = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True, nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("election.id"), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey("voter.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("election_id", "voter_id", "category_id", name="uq_one_vote_per_category"),
                      Index("ix_vote_tally", "election_id", "category_id", "candidate_id"))

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    at = db.Column(db.DateTime, default=utcnow, index=True)
    action = db.Column(db.String(60), index=True); actor = db.Column(db.String(40))
    detail = db.Column(db.Text); ip = db.Column(db.String(64), index=True)
