"""Generate editable draw.io diagrams; export with the draw.io desktop CLI."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / "doc/diagrams"
BASE = "html=1;whiteSpace=wrap;sketch=0;"


class Drawing:
    def __init__(self, title, subtitle):
        self.file = ET.Element("mxfile", host="app.diagrams.net")
        diagram = ET.SubElement(self.file, "diagram", id="overview", name="Overview")
        model = ET.SubElement(diagram, "mxGraphModel", dx="2800", dy="1600", page="1", pageWidth="2400", pageHeight="1400")
        self.root = ET.SubElement(model, "root")
        ET.SubElement(self.root, "mxCell", id="0")
        ET.SubElement(self.root, "mxCell", id="1", parent="0")
        self.n = 0
        self.positions = {}
        self.box("background", "", 0, 0, 2400, 1400, "fillColor=#F5F5F5;strokeColor=none;")
        self.box("title", f"<b>{title}</b><br>manisa504 | 2026-10-10 | v2 · Bedrock RAG", 60, 35, 1600, 100,
                 "text;align=left;verticalAlign=top;fontSize=24;spacing=8;")
        self.box("subtitle", subtitle, 70, 155, 2180, 80, "text;align=left;fontSize=18;fontColor=#42594E;")

    def box(self, id, label, x, y, w, h, style):
        cell = ET.SubElement(self.root, "mxCell", id=id, value=label, style=BASE + style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), attrib={"as": "geometry"})
        return id

    def icon(self, id, label, x, y, shape, color="#232F3D", service=False, secondary=False):
        size = 65 if secondary else 78
        self.positions[id] = (x, y, size)
        style = (f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{shape};strokeColor=#ffffff;"
                 if service else f"shape=mxgraph.aws4.{shape};strokeColor=none;")
        self.box(id, "", x, y, size, size, style + f"fillColor={color};")
        self.box(id + "-label", label, x-95, y+size+24, 270, 85,
                 "text;align=center;verticalAlign=top;fontSize=12;fontColor=#232F3D;")
        return id

    def edge(self, src, dst, label=None, vertical=False, dashed=False, error=False):
        self.n += 1
        style = BASE + "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeWidth=2;fontSize=12;labelBackgroundColor=#F5F5F5;"
        style += "exitX=0.5;exitY=1;entryX=0.5;entryY=0;align=right;" if vertical else "exitX=1;exitY=0.5;entryX=0;entryY=0.5;verticalAlign=bottom;"
        style += "strokeColor=#DD344C;dashed=1;" if error else "strokeColor=#232F3D;" + ("dashed=1;" if dashed else "")
        attrs = {"id": f"edge-{self.n}", "style": style, "edge": "1", "source": src, "target": dst, "parent": "1"}
        if label:
            attrs["value"] = label
        cell = ET.SubElement(self.root, "mxCell", **attrs)
        geometry = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        if vertical:
            x, y, size = self.positions[src]
            tx, ty, ts = self.positions[dst]
            points = ET.SubElement(geometry, "Array", attrib={"as": "points"})
            route_x = x + 220
            route_y = ty - 35 - self.n * 15
            for px, py in [(x + size / 2, y + size + 16),
                           (route_x, y + size + 16), (route_x, route_y),
                           (tx + ts / 2, route_y)]:
                ET.SubElement(points, "mxPoint", x=str(px), y=str(py))

    def note(self, text):
        self.box("note", text, 100, 1170, 2200, 140, "text;align=left;verticalAlign=top;fontSize=20;fontColor=#42594E;")

    def save(self, name, guide):
        ROOT.mkdir(parents=True, exist_ok=True)
        ET.indent(self.file)
        ET.ElementTree(self.file).write(ROOT / f"{name}.drawio", encoding="utf-8", xml_declaration=True)
        (ROOT / f"{name}.md").write_text(guide)


def main():
    d = Drawing("AWS deployment · one application, two models", "Request path runs left to right. Supporting deployment and identity services sit below.")
    d.box("aws", "AWS Cloud · us-east-2 / Ohio", 460, 270, 1850, 820,
          "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=40;fontSize=18;")
    d.icon("browser", "Browser<br>Streamlit session", 130, 370, "client")
    d.icon("alb", "Application Load Balancer<br>Managed HTTPS endpoint", 610, 370, "elastic_load_balancing", "#8C4FFF", True)
    d.icon("app", "ECS Express Mode / Fargate<br>Python 3.12 · Streamlit · FAISS<br>1 ARM64 task · 0.25 vCPU / 1 GiB", 1090, 370, "fargate", "#ED7100", True)
    d.icon("bedrock", "Amazon Bedrock<br>Titan Text Embeddings V2<br>Nova Lite · regional invocation", 2030, 370, "bedrock", "#01A88D", True)
    d.edge("browser", "alb", "HTTPS")
    d.edge("alb", "app", "HTTP 8501")
    d.edge("app", "bedrock", "InvokeModel")
    d.icon("ecr", "Amazon ECR<br>Immutable container image", 610, 810, "ecr", "#ED7100", True, True)
    d.icon("iam", "IAM task role<br>InvokeModel on two models only<br>Separate image/log execution role", 1090, 810, "role", "#DD344C", secondary=True)
    d.icon("logs", "Amazon CloudWatch<br>Container logs", 1550, 810, "cloudwatch_2", "#E7157B", True, True)
    d.icon("cert", "AWS Certificate Manager<br>HTTPS certificate", 2030, 810, "certificate_manager_3", "#DD344C", True, True)
    d.edge("app", "iam", "Identity", True, True)
    d.edge("app", "logs", "Logs", True, True)
    d.edge("app", "ecr", "Image pull", True, True)
    d.edge("alb", "cert", "TLS", True, True)
    d.note("Session isolation: PDFs, extracted text, embeddings and the FAISS index live in task memory.<br>No durable/shared document store. A refresh or task replacement can discard a session. Solid: request path. Dashed: supporting services.")
    d.save("aws-deployment", "# AWS deployment\n\n1. Browser reaches the managed HTTPS load balancer.\n2. Traffic reaches the single Fargate task on port 8501.\n3. boto3 uses the task role to invoke Titan embeddings and Nova Lite in Ohio.\n\nECR supplies the container image; the execution role permits image pulls and logs. The dedicated task role permits only the two model ARNs. CloudWatch receives container logs. ACM manages the endpoint certificate. The diagram omits service-managed subnet details. Documents and FAISS are session-local, not durable or shared.\n")
    d = Drawing("Document ingestion · preserve the source before retrieval", "Build index is explicit: users preview the extracted pages before paying for embeddings.")
    for id, label, x, shape in [("upload", "Upload PDFs<br>20 MiB each · text PDFs", 130, "documents"),
        ("pages", "PyMuPDF extraction<br>Filename + one-based page", 610, "source_code"),
        ("chunks", "Page-bound word windows<br>200 words / 40 overlap", 1090, "document"),
        ("embed", "Titan V2 embeddings<br>256 dimensions · normalized", 1570, "bedrock"),
        ("index", "FAISS IndexFlatIP<br>Vectors + source metadata", 2050, "gear")]:
        d.icon(id, label, x, 390, shape, "#01A88D" if id=="embed" else "#232F3D", id=="embed")
    for a,b,label in [("upload","pages","Parse"),("pages","chunks","Chunk"),("chunks","embed","Build index"),("embed","index","Cosine search")]: d.edge(a,b,label)
    d.icon("invalid", "Reject invalid / encrypted PDFs<br>Other valid uploads still work", 130, 850, "document", "#DD344C", secondary=True)
    d.icon("blank", "Blank page stays in page list<br>No chunk · references do not shift", 610, 850, "document", secondary=True)
    d.icon("stale", "Any upload/chunk change<br>Discard old index and answer", 2050, 850, "gear", secondary=True)
    d.edge("upload","invalid","Invalid",True,error=True);d.edge("pages","blank","Empty page",True,True);d.edge("index","stale","Invalidate",True,True)
    d.note("Word windows are not model token counts. The demo caps indexing at 200 chunks.<br>Index publication is atomic: failed embedding calls do not leave a partial searchable index. No cross-user global cache.")
    d.save("document-pipeline", "# Document ingestion\n\n1. Validate PDF bytes and extract pages in memory.\n2. Preserve blank pages and one-based metadata.\n3. Split text into overlapping windows without crossing pages.\n4. Send chunks to Titan V2 on explicit Build index.\n5. Normalize vectors and store them in FAISS beside metadata.\n\nMalformed/encrypted files are rejected individually. Upload or settings changes invalidate old evidence. The 200-chunk cap bounds demonstration usage; there is no durable/shared store.\n")
    d = Drawing("Question answering · retrieve, ground, verify", "A simple router chooses documents or general knowledge. No autonomous agent loop.")
    d.icon("question", "User question<br>Auto / Documents / General", 130, 360, "client")
    d.icon("router", "Rule-based router<br>Uploaded PDFs default to RAG", 610, 360, "gear")
    d.icon("retrieve", "Titan query embedding + FAISS<br>Top 4 relevant chunks", 1090, 360, "gear")
    d.icon("llm", "Amazon Bedrock · Nova Lite<br>Evidence-only JSON claims", 1570, 360, "bedrock", "#01A88D", True)
    d.icon("answer", "Validate source IDs + exact quotes<br>Render filename / page citations", 2050, 360, "document")
    for a,b,label in [("question","router",None),("router","retrieve","Documents"),("retrieve","llm","Evidence"),("llm","answer","Claims")]: d.edge(a,b,label)
    d.icon("general", "Amazon Bedrock · Nova Lite<br>General answer · no file citations", 610, 850, "bedrock", "#01A88D", True)
    d.icon("abstain", "Insufficient / unverifiable evidence<br>Explicit abstention", 2050, 850, "document", "#DD344C", secondary=True)
    d.edge("router","general","General",True,True);d.edge("answer","abstain","Unsupported",True,error=True)
    d.note("Citations are built from retrieved metadata, not invented by the model. Each claim must cite an existing source and a verbatim quote.<br>This checks provenance, not full semantic entailment. Review the retrieved evidence; the 12-case evaluation is a small demonstration benchmark.")
    d.save("answer-flow", "# Question answering\n\n1. Auto uses documents when uploaded; General and Documents explicitly override.\n2. Embed a document question and retrieve top four cosine matches.\n3. Nova Lite receives the question and retrieved evidence.\n4. Validate its JSON, source IDs and verbatim quotes before showing a cited answer.\n5. Abstain for missing/unverifiable support; use direct inference for General mode.\n\nCitation checks prove provenance, not semantic correctness. Exact-match evidence and prompt instructions do not guarantee resistance to every malicious PDF. Inspect source text and evaluate behavior.\n")


if __name__ == "__main__":
    main()
