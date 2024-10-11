import qrcode
from PIL import ImageDraw, Image, ImageFont
import cv2  # opencv-python
from pyzbar.pyzbar import decode
from PIL import Image


def decode_color(color):
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def create_qr_with_logo(qr_code_text, logo_img):
    # Создание QR-кода
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1
    )
    qr.add_data(qr_code_text)
    qr.make(fit=True)
    qr_code_img = qr.make_image(fill_color=decode_color('5A89B9')).convert('RGB')

    # Размещение логотипа в центре QR-кода
    pos = ((qr_code_img.size[0] - logo_img.size[0]) // 2 + 5, (qr_code_img.size[1] - logo_img.size[1]) // 2)
    qr_code_img.paste(logo_img, pos)

    return qr_code_img


def create_image_with_text(text, font_path='DejaVuSansMono.ttf', font_size=30, image_size=(200, 50)):
    # Создание пустого изображения
    image = Image.new('RGB', image_size, color='white')
    draw = ImageDraw.Draw(image)

    # Загрузка шрифта
    font = ImageFont.truetype(font_path, font_size)

    # Расчет позиции для размещения текста по центру с использованием textbbox
    textbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = textbox[2] - textbox[0], textbox[3] - textbox[1]
    x = (image_size[0] - text_width) / 2
    y = (image_size[1] - text_height) / 2 - 5

    draw.text((x, y), text, font=font, fill=decode_color('C1D9F9'))

    # Размещение рамки
    xy = [0, 0, image_size[0] - 1, image_size[1] - 1]
    draw.rectangle(xy, outline=decode_color('C1D9F9'), width=2)

    return image


def create_beautiful_code(file_name, address, text=''):
    logo_img = create_image_with_text(text)
    qr_with_logo_img = create_qr_with_logo(address, logo_img)
    qr_with_logo_img.save(file_name)


def decode_qr_code_cv(image_path):
    image = cv2.imread(image_path)
    qr_code_detector = cv2.QRCodeDetector()
    decoded_text, points, _ = qr_code_detector.detectAndDecode(image)

    if points is not None and decoded_text:
        return decoded_text
    else:
        return None


def decode_qr_code_pyzbar(image_path):
    image = Image.open(image_path)
    decoded_objects = decode(image)
    if decoded_objects:
        return decoded_objects[0].data.decode('utf-8')
    else:
        return None


def decode_qr_code(image_path):
    result = decode_qr_code_cv(image_path)

    if result is None:
        result = decode_qr_code_pyzbar(image_path)

    if result is None:
        return None
    else:
        return result


if __name__ == '__main__':
    create_beautiful_code('qr_with_logo.png', '852f893a77a54f41876677b3cd5298c0', 'MTLFEST011')
