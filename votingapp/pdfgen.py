import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
WM = "Designed by DeNoble (Yahaya Jamiu)"
BROWN = colors.HexColor("#4a2c17")

def build_pdf(election, results, stats, generated):
    buf = io.BytesIO(); ss = getSampleStyleSheet()
    def footer(c, d):
        c.setFont("Helvetica", 8); c.drawCentredString(A4[0] / 2, 20, f"{WM}  |  Page {d.page}")
    doc = SimpleDocTemplate(buf, pagesize=A4, title="NACOS CUSTECH Official Results")
    s = [Paragraph("NACOS CUSTECH Electronic Voting System", ss["Title"]),
         Paragraph("Official Election Results - CUSTECH, Osara, Kogi State", ss["Heading3"]),
         Paragraph(f"Election session #{election.id} | Opened: {election.opened_at} UTC | Closed: {election.closed_at} UTC | Generated: {generated} UTC", ss["Normal"]),
         Paragraph(f"Voter identities: {stats['voters']} | Voters who participated: {stats['participants']}", ss["Normal"]), Spacer(1, 12)]
    for c in results:
        w = "No votes recorded" if c["status"] == "empty" else ("TIE - resolution required: " + escape(", ".join(c["leaders"])) if c["status"] == "tie" else "Winner: " + escape(c["leaders"][0]))
        s.append(Paragraph(f"<b>{escape(c['name'])}</b> - {w}", ss["Heading4"]))
        rows = [["Candidate", "Votes", "%"]] + [[x["name"], x["votes"], f"{x['pct']}%"] for x in c["candidates"]]
        t = Table(rows, colWidths=[300, 60, 60])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BROWN), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .4, colors.grey)]))
        s += [t, Spacer(1, 10)]
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
