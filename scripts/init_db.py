"""Optional manual init: python scripts/init_db.py (the app also does this automatically on Vercel)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from votingapp import create_app
from votingapp.seed import seed
app = create_app()
with app.app_context(): seed(); print("Done. Category 19 is inactive until renamed and activated in the admin dashboard.")
