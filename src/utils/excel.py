import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

def generate_excel(orders):
    df = pd.DataFrame(orders)
    stream = BytesIO()
    df.to_excel(stream, index=False, engine='openpyxl')
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=comenzi.xlsx"}
    )