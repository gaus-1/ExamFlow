import qrcode  # type: ignore
from io import BytesIO
import base64

def generate_qr_code(url):
    """Генерирует QR-код для указанного URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # type: ignore
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#81D8D0", back_color="white")

        buffer = BytesIO()
        img.save(buffer, "PNG")  # Исправлено: убран именованный параметр
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        # Возвращаем заглушку в случае ошибки
        return f"data:text/plain;base64,{base64.b64encode(f'QR Error: {str(e)}'.encode()).decode()}"
