from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv, dotenv_values
import certifi
import json
from datetime import datetime
from src.schemas.order import OrderProps
from bson import ObjectId
from starlette.middleware.cors import CORSMiddleware

load_dotenv()
config = dotenv_values(".env")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.buchetul-simonei.com",
        "https://buchetul-simonei.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


MONGO_URI = config.get("MONGO_URI")
DB_NAME = config.get("DB_NAME")
COLLECTION_NAME = config.get("COLLECTION_NAME")

# Create client only if MONGO_URI provided; use short serverSelectionTimeoutMS for fast failures
client = None
db = None
orders_collection = None
if MONGO_URI:
    try:
        client = MongoClient(
            MONGO_URI,
            server_api=ServerApi("1"),
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        # verify connection
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB Atlas!")
        db = client[DB_NAME] if DB_NAME else None
        # evitam truth-testing pe obiecte pymongo; comparam explicit cu None
        orders_collection = db[COLLECTION_NAME] if (db is not None and COLLECTION_NAME) else None
    except Exception as e:
        print("MongoDB connection failed:", e)
        client = None
        db = None
        orders_collection = None
else:
    print("MONGO_URI not set in .env; skipping MongoDB connection.")

@app.get("/")
def home():
    return {"status": "Backend Python functioneaza!"}

@app.get("/export-orders")
def export_orders():
    # Collection does not support truth-value testing — compare explicitly with None
    if orders_collection is None:
        return JSONResponse(
            status_code=503,
            content={"error": "MongoDB not available. Set MONGO_URI to your Atlas connection string in .env."}
        )

    # Citim documentele din MongoDB
    raw_orders = list(orders_collection.find({}))  # include _id daca exista
    rows = []
    for doc in raw_orders:
        # normalizeaza _id -> id
        if "_id" in doc and "id" not in doc:
            try:
                doc["id"] = str(doc["_id"])
            except Exception:
                doc["id"] = doc["_id"]
        # Convert datetimes to ISO strings (pydantic/Excel friendly)
        if "orderDate" in doc and isinstance(doc["orderDate"], datetime):
            doc["orderDate"] = doc["orderDate"].isoformat()
        if "deliveryDate" in doc and isinstance(doc["deliveryDate"], datetime):
            doc["deliveryDate"] = doc["deliveryDate"].isoformat()

        # Ensure products is serializable; keep as list of dicts and stringify for Excel
        products = doc.get("products", [])
        try:
            products_json = json.dumps(products, ensure_ascii=False)
        except Exception:
            products_json = str(products)

        # Try to validate/normalize with OrderProps; if fails, fall back to raw mapping
        try:
            order = OrderProps.parse_obj(doc)
            row = {
                "id": order.id,
                "userId": order.userId,
                "orderNumber": order.orderNumber,
                "clientName": order.clientName,
                "clientEmail": order.clientEmail,
                "clientPhone": order.clientPhone,
                "clientAddress": order.clientAddress,
                "orderDate": order.orderDate.isoformat() if isinstance(order.orderDate, datetime) else str(order.orderDate),
                "deliveryDate": order.deliveryDate.isoformat() if isinstance(order.deliveryDate, datetime) else (str(order.deliveryDate) if order.deliveryDate else ""),
                "info": order.info or "",
                "status": order.status,
                "totalPrice": order.totalPrice,
                "paymentMethod": order.paymentMethod,
                "products": json.dumps([p.dict() for p in order.products], ensure_ascii=False)
            }
        except Exception:
            # fallback: use doc fields and stringify products
            row = {
                "id": doc.get("id", ""),
                "userId": doc.get("userId", ""),
                "orderNumber": doc.get("orderNumber", ""),
                "clientName": doc.get("clientName", ""),
                "clientEmail": doc.get("clientEmail", ""),
                "clientPhone": doc.get("clientPhone", ""),
                "clientAddress": doc.get("clientAddress", ""),
                "orderDate": doc.get("orderDate", ""),
                "deliveryDate": doc.get("deliveryDate", ""),
                "info": doc.get("info", ""),
                "status": doc.get("status", ""),
                "totalPrice": doc.get("totalPrice", ""),
                "paymentMethod": doc.get("paymentMethod", ""),
                "products": products_json
            }

        rows.append(row)

    # Ordinea coloanelor conform OrderProps
    columns = [
        "id",
        "userId",
        "orderNumber",
        "clientName",
        "clientEmail",
        "clientPhone",
        "clientAddress",
        "orderDate",
        "deliveryDate",
        "info",
        "status",
        "totalPrice",
        "paymentMethod",
        "products"
    ]

    df = pd.DataFrame(rows, columns=columns)

    stream = BytesIO()
    df.to_excel(stream, index=False, engine="openpyxl")
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=comenzi.xlsx"}
    )

def _build_orders_df():
    raw_orders = list(orders_collection.find({}))
    rows = []
    for doc in raw_orders:
        if "_id" in doc and "id" not in doc:
            try:
                doc["id"] = str(doc["_id"])
            except Exception:
                doc["id"] = doc["_id"]

        if "orderDate" in doc and isinstance(doc["orderDate"], datetime):
            doc["orderDate"] = doc["orderDate"].isoformat()
        if "deliveryDate" in doc and isinstance(doc["deliveryDate"], datetime):
            doc["deliveryDate"] = doc["deliveryDate"].isoformat()

        products = doc.get("products", [])
        try:
            products_json = json.dumps(products, ensure_ascii=False)
        except Exception:
            products_json = str(products)

        try:
            order = OrderProps.parse_obj(doc)
            row = {
                "id": order.id,
                "userId": order.userId,
                "orderNumber": order.orderNumber,
                "clientName": order.clientName,
                "clientEmail": order.clientEmail,
                "clientPhone": order.clientPhone,
                "clientAddress": order.clientAddress,
                "orderDate": order.orderDate.isoformat() if isinstance(order.orderDate, datetime) else str(order.orderDate),
                "deliveryDate": order.deliveryDate.isoformat() if isinstance(order.deliveryDate, datetime) else (str(order.deliveryDate) if order.deliveryDate else ""),
                "info": order.info or "",
                "status": order.status,
                "totalPrice": order.totalPrice,
                "paymentMethod": order.paymentMethod,
                "products": json.dumps([p.dict() for p in order.products], ensure_ascii=False)
            }
        except Exception:
            row = {
                "id": doc.get("id", ""),
                "userId": doc.get("userId", ""),
                "orderNumber": doc.get("orderNumber", ""),
                "clientName": doc.get("clientName", ""),
                "clientEmail": doc.get("clientEmail", ""),
                "clientPhone": doc.get("clientPhone", ""),
                "clientAddress": doc.get("clientAddress", ""),
                "orderDate": doc.get("orderDate", ""),
                "deliveryDate": doc.get("deliveryDate", ""),
                "info": doc.get("info", ""),
                "status": doc.get("status", ""),
                "totalPrice": doc.get("totalPrice", ""),
                "paymentMethod": doc.get("paymentMethod", ""),
                "products": products_json
            }

        rows.append(row)

    columns = [
        "id",
        "userId",
        "orderNumber",
        "clientName",
        "clientEmail",
        "clientPhone",
        "clientAddress",
        "orderDate",
        "deliveryDate",
        "info",
        "status",
        "totalPrice",
        "paymentMethod",
        "products"
    ]

    df = pd.DataFrame(rows, columns=columns)
    return df

@app.get("/export-orders.csv")
def export_orders_csv():
    if orders_collection is None:
        return JSONResponse(
            status_code=503,
            content={"error": "MongoDB not available. Set MONGO_URI to your Atlas connection string in .env."}
        )

    df = _build_orders_df()

    stream = BytesIO()
    # UTF-8 with BOM (excel-friendly), without index column
    df.to_csv(stream, index=False, encoding="utf-8-sig")
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=comenzi.csv"}
    )

@app.get("/orders/{order_id}/invoice.pdf")
def download_invoice(order_id: str):
    if orders_collection is None:
        return JSONResponse(
            status_code=503,
            content={"error": "MongoDB not available. Set MONGO_URI to your Atlas connection string in .env."}
        )

    # cautari posibile (în ordinea asta)
    tried = []
    order_doc = None

    # 1) câmp custom "id" (string UUID sau alt string)
    tried.append({"id": order_id})
    order_doc = orders_collection.find_one({"id": order_id})

    # 2) _id ca string (uneori _id este stocat ca string)
    if order_doc is None:
        tried.append({"_id": order_id})
        order_doc = orders_collection.find_one({"_id": order_id})

    # 3) _id ca ObjectId (daca order_id e un ObjectId valid)
    if order_doc is None:
        try:
            oid = ObjectId(order_id)
            tried.append({"_id": f"ObjectId('{order_id}')"})
            order_doc = orders_collection.find_one({"_id": oid})
        except Exception:
            # nu e ObjectId valid
            pass

    # 4) orderNumber (daca ai trimis numarul comenzii în URL)
    if order_doc is None:
        try:
            maybe_num = int(order_id)
            tried.append({"orderNumber": maybe_num})
            order_doc = orders_collection.find_one({"orderNumber": maybe_num})
        except Exception:
            pass

    # debug: log interogarile
    print("invoice lookup tried:", tried, "found:", bool(order_doc))

    if not order_doc:
        # return mai informativ pentru depanare (fara date sensibile)
        return JSONResponse(
            status_code=404,
            content={
                "error": "Order not found",
                "tried": tried
            }
        )

    if "_id" in order_doc and "id" not in order_doc:
        try:
            order_doc["id"] = str(order_doc["_id"])
        except Exception:
            order_doc["id"] = order_doc["_id"]
    if "orderDate" in order_doc and isinstance(order_doc["orderDate"], datetime):
        order_doc["orderDate"] = order_doc["orderDate"].isoformat()
    if "deliveryDate" in order_doc and isinstance(order_doc["deliveryDate"], datetime):
        order_doc["deliveryDate"] = order_doc["deliveryDate"].isoformat()

    # build PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    heading = ParagraphStyle("heading", parent=styles["Heading2"], spaceAfter=6)

    story = []

    # Company block (header)
    company_name = "BUCHETUL SIMONEI POEZIA FLORILOR SRL"
    company_addr = "jud. Neamt, sat Tamaseni, Str. Unirii 224, Cod 617465"
    company_reg = "Înregistrare la Registrul Comertului: J27/802/2016, CUI: 36497181"
    company_contact = "Contact: laurasimona97@yahoo.com — Tel: 0769141250"
    site_info = "www.buchetul-simonei.com"

    story.append(Paragraph(company_name, ParagraphStyle("cname", parent=styles["Heading1"], fontSize=14)))
    story.append(Paragraph(company_addr, small))
    story.append(Paragraph(company_reg, small))
    story.append(Paragraph(company_contact, small))
    story.append(Paragraph(site_info, small))
    story.append(Spacer(1, 8))

    # Invoice title + meta
    story.append(Paragraph("FACTURA", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Numar comanda: <b>{order_doc.get('orderNumber','')}</b>", normal))
    story.append(Paragraph(f"ID comanda: {order_doc.get('id','')}", normal))
    story.append(Paragraph(f"Data comanda: {order_doc.get('orderDate','')}", normal))
    story.append(Spacer(1, 8))

    # Client info
    story.append(Paragraph("<b>Date client</b>", heading))
    story.append(Paragraph(f"Nume: {order_doc.get('clientName','')}", normal))
    story.append(Paragraph(f"Email: {order_doc.get('clientEmail','')}", normal))
    story.append(Paragraph(f"Telefon: {order_doc.get('clientPhone','')}", normal))
    story.append(Paragraph(f"Adresa: {order_doc.get('clientAddress','')}", normal))
    story.append(Spacer(1, 8))

    # Products table
    prod_header = ["#", "Produs", "Cant.", "Pret unitar", "Subtotal"]
    table_data = [prod_header]
    products = order_doc.get("products", []) or []
    total = 0.0
    for i, p in enumerate(products, start=1):
        title = p.get("title") if isinstance(p, dict) else getattr(p, "title", str(p))
        qty = p.get("quantity", 0) if isinstance(p, dict) else getattr(p, "quantity", 0)
        price = p.get("price", 0.0) if isinstance(p, dict) else getattr(p, "price", 0.0)
        try:
            subtotal = float(price) * int(qty)
        except Exception:
            subtotal = 0.0
        total += subtotal
        table_data.append([str(i), title, str(qty), f"{price:.2f}", f"{subtotal:.2f}"])

    # VAT and totals
    vat_rate = 0.21
    vat_amount = total * vat_rate
    total_with_vat = total

    table_data.append(["", "", "", "Subtotal", f"{total:.2f}"])
    table_data.append(["", "", "", f"TVA {int(vat_rate*100)}%", f"{vat_amount:.2f}"])
    table_data.append(["", "", "", "Total (cu TVA)", f"{total_with_vat:.2f}"])

    col_widths = [10*mm, 95*mm, 20*mm, 30*mm, 30*mm]
    table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,-3), (-1,-1), colors.HexColor("#fafafa")),
    ]))

    story.append(table)
    story.append(Spacer(1, 10))

    # Additional info and payment method
    story.append(Paragraph(f"Informatii comanda: {order_doc.get('info','')}", normal))
    story.append(Paragraph(f"Metoda plata: {order_doc.get('paymentMethod','')}", normal))
    story.append(Spacer(1, 8))

    # Legal / contact footer block
    legal_text = (
        "Site-ul www.buchetul-simonei.com este detinut si operat de BUCHETUL SIMONEI POEZIA FLORILOR SRL, "
        "cu sediul în judetul Neamt, sat Tamaseni, Str. Unirii 224, Cod 617465. "
        "Înregistrare la Registrul Comertului: J27/802/2016, CUI: 36497181."
    )
    story.append(Paragraph(legal_text, small))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Date de contact operator:", ParagraphStyle("foot_h", parent=styles["Heading4"], fontSize=9)))
    story.append(Paragraph("BUCHETUL SIMONEI POEZIA FLORILOR SRL", small))
    story.append(Paragraph(company_addr, small))
    story.append(Paragraph(f"Email: {company_contact.split('—')[0].strip()}", small))
    story.append(Paragraph(f"Telefon: {company_contact.split('—')[-1].strip()}", small))
    story.append(Spacer(1, 6))

    # Thank you footer
    story.append(Paragraph("Multumim pentru comanda!", ParagraphStyle("center", parent=normal, alignment=1)))

    doc.build(story)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order_doc.get('id','')}.pdf"}
    )