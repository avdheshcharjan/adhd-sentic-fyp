import requests
import xlrd
import xlwt

LANG = 'en'
API_KEY = '<YOUR_API_KEY_HERE>'
API_URL = f'https://sentic.net/api/{LANG}/{API_KEY}.py?text='
FILE_NAME = 'data'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/111.0.0.0 Safari/537.36'
    )
}

wb = xlrd.open_workbook(FILE_NAME + '.xls')
sheet = wb.sheet_by_index(0)

new_wb = xlwt.Workbook(style_compression=2)
new_sheet = new_wb.add_sheet('labeled')

new_wb.set_colour_RGB(33, 249, 221, 46)     # ECSTASY
new_wb.set_colour_RGB(34, 250, 231, 133)    # JOY
new_wb.set_colour_RGB(35, 245, 238, 191)    # CONTENTMENT
new_wb.set_colour_RGB(36, 136, 193, 230)    # MELANCHOLY 
new_wb.set_colour_RGB(37, 64, 165, 216)     # SADNESS
new_wb.set_colour_RGB(38, 3, 139, 199)      # GRIEF
new_wb.set_colour_RGB(39, 247, 152, 34)     # BLISS
new_wb.set_colour_RGB(40, 246, 182, 104)    # CALMNESS
new_wb.set_colour_RGB(41, 248, 204, 152)    # SERENITY
new_wb.set_colour_RGB(42, 245, 200, 182)    # ANNOYANCE
new_wb.set_colour_RGB(43, 240, 137, 104)    # ANGER
new_wb.set_colour_RGB(44, 235, 92, 85)      # RAGE
new_wb.set_colour_RGB(45, 13, 172, 192)     # DELIGHT
new_wb.set_colour_RGB(46, 24, 191, 220)     # PLEASANTNESS
new_wb.set_colour_RGB(47, 157, 219, 229)    # ACCEPTANCE
new_wb.set_colour_RGB(48, 190, 218, 192)    # DISLIKE
new_wb.set_colour_RGB(49, 154, 202, 161)    # DISGUST
new_wb.set_colour_RGB(50, 107, 187, 104)    # LOATHING
new_wb.set_colour_RGB(51, 238, 89, 160)     # ENTHUSIASM
new_wb.set_colour_RGB(52, 240, 131, 180)    # EAGERNESS
new_wb.set_colour_RGB(53, 241, 185, 213)    # RESPONSIVENESS
new_wb.set_colour_RGB(54, 182, 170, 206)    # ANXIETY
new_wb.set_colour_RGB(55, 141, 117, 174)    # FEAR
new_wb.set_colour_RGB(56, 101, 69, 153)     # TERROR

header_style = xlwt.easyxf('font: bold on; align: horiz center')
cell_style = xlwt.easyxf('align: horiz center')
pos_style = xlwt.easyxf('pattern: pattern solid, fore_colour sea_green; font: colour white; align: horiz center')
neg_style = xlwt.easyxf('pattern: pattern solid, fore_colour red; font: colour white; align: horiz center')

styles = {
    "ECSTASY": xlwt.easyxf('pattern: pattern solid, fore_colour 33; align: horiz center'),
    "JOY": xlwt.easyxf('pattern: pattern solid, fore_colour 34; align: horiz center'),
    "CONTENTMENT": xlwt.easyxf('pattern: pattern solid, fore_colour 35; align: horiz center'),
    "MELANCHOLY": xlwt.easyxf('pattern: pattern solid, fore_colour 36; font: colour white; align: horiz center'),
    "SADNESS": xlwt.easyxf('pattern: pattern solid, fore_colour 37; font: colour white; align: horiz center'),
    "GRIEF": xlwt.easyxf('pattern: pattern solid, fore_colour 38; font: colour white; align: horiz center'),

    "BLISS": xlwt.easyxf('pattern: pattern solid, fore_colour 39; align: horiz center'),
    "CALMNESS": xlwt.easyxf('pattern: pattern solid, fore_colour 40; align: horiz center'),
    "SERENITY": xlwt.easyxf('pattern: pattern solid, fore_colour 41; align: horiz center'),
    "ANNOYANCE": xlwt.easyxf('pattern: pattern solid, fore_colour 42; font: colour white; align: horiz center'),
    "ANGER": xlwt.easyxf('pattern: pattern solid, fore_colour 43; font: colour white; align: horiz center'),
    "RAGE": xlwt.easyxf('pattern: pattern solid, fore_colour 44; font: colour white; align: horiz center'),
    
    "DELIGHT": xlwt.easyxf('pattern: pattern solid, fore_colour 45; align: horiz center'),
    "PLEASANTNESS": xlwt.easyxf('pattern: pattern solid, fore_colour 46; align: horiz center'),
    "ACCEPTANCE": xlwt.easyxf('pattern: pattern solid, fore_colour 47; align: horiz center'),
    "DISLIKE": xlwt.easyxf('pattern: pattern solid, fore_colour 48; font: colour white; align: horiz center'),
    "DISGUST": xlwt.easyxf('pattern: pattern solid, fore_colour 49; font: colour white; align: horiz center'),
    "LOATHING": xlwt.easyxf('pattern: pattern solid, fore_colour 50; font: colour white; align: horiz center'),

    "ENTHUSIASM": xlwt.easyxf('pattern: pattern solid, fore_colour 51; align: horiz center'),
    "EAGERNESS": xlwt.easyxf('pattern: pattern solid, fore_colour 52; align: horiz center'),
    "RESPONSIVENESS": xlwt.easyxf('pattern: pattern solid, fore_colour 53; align: horiz center'),
    "ANXIETY": xlwt.easyxf('pattern: pattern solid, fore_colour 54; font: colour white; align: horiz center'),
    "FEAR": xlwt.easyxf('pattern: pattern solid, fore_colour 55; font: colour white; align: horiz center'),
    "TERROR": xlwt.easyxf('pattern: pattern solid, fore_colour 56; font: colour white; align: horiz center'),
}

def write_header(col, width_factor, text):
    new_sheet.write(0, col, text, header_style)
    new_sheet.col(col).width = width_factor

headers = [
    ('TEXT', 10000), ('POLARITY', 4000), ('INTENSITY', 4000), ('EMOTIONS', 10000), ('INTROSPECTION', 4000), ('TEMPER', 4000), ('ATTITUDE', 4000), ('SENSITIVITY', 4000), ('PERSONALITY', 5000), ('ASPECTS', 10000), ('SARCASM', 6000), ('DEPRESSION', 4000), ('TOXICITY', 4000), ('ENGAGEMENT', 4000), ('WELL-BEING', 4000),
]

for col, (title, width) in enumerate(headers): write_header(col, width, title)
    
for row_idx in range(sheet.nrows):
    text = str(sheet.cell_value(row_idx, 0))
    for c in [';', '&', '#', '{', '}']: text = text.replace(c, ':')

    try:
        response = requests.get(API_URL + text, headers=HEADERS, timeout=10)
        response.raise_for_status()
        label = response.text.strip()
    except Exception: label = 'Internal Server Error'

    if 'Internal Server Error' in label:
        label = (
            'NEUTRAL;0;No emotions detected;0;0;0;0;'
            'No personality trait detected;No aspects discovered;'
            'No sarcasm detected;0%;0%;0%;0%'
        )

    label = label.replace('&#8593;', '↑').replace('&#8595;', '↓')
    values = label.split(';')

    row_out = row_idx + 1
    new_sheet.write(row_out, 0, text)

    for col, value in enumerate(values, start=1):
        val_str = value.strip()

        if col == 1:
            val = val_str.upper()
            style = pos_style if val == 'POSITIVE' else neg_style if val == 'NEGATIVE' else cell_style

        elif col in [4, 5, 6, 7]:
            try: num_val = float(val_str)
            except ValueError: num_val = 0
            if col == 4:
                if num_val == 0: style = cell_style
                elif num_val > 66: style = styles["ECSTASY"]
                elif num_val > 33: style = styles["JOY"]
                elif num_val > 0: style = styles["CONTENTMENT"]
                elif num_val > -34: style = styles["MELANCHOLY"]
                elif num_val > -67: style = styles["SADNESS"]
                else: style = styles["GRIEF"]
            elif col == 5:
                if num_val == 0: style = cell_style
                elif num_val > 66: style = styles["BLISS"]
                elif num_val > 33: style = styles["CALMNESS"]
                elif num_val > 0: style = styles["SERENITY"]
                elif num_val > -34: style = styles["ANNOYANCE"]
                elif num_val > -67: style = styles["ANGER"]
                else: style = styles["RAGE"]
            elif col == 6:
                if num_val == 0: style = cell_style
                elif num_val > 66: style = styles["DELIGHT"]
                elif num_val > 33: style = styles["PLEASANTNESS"]
                elif num_val > 0: style = styles["ACCEPTANCE"]
                elif num_val > -34: style = styles["DISLIKE"]
                elif num_val > -67: style = styles["DISGUST"]
                else: style = styles["LOATHING"]
            elif col == 7:
                if num_val == 0: style = cell_style
                elif num_val > 66: style = styles["ENTHUSIASM"]
                elif num_val > 33: style = styles["EAGERNESS"]
                elif num_val > 0: style = styles["RESPONSIVENESS"]
                elif num_val > -34: style = styles["ANXIETY"]
                elif num_val > -67: style = styles["FEAR"]
                else: style = styles["TERROR"]
        else: style = cell_style

        new_sheet.write(row_out, col, value, style)

    print(f"{text}: {label.replace(';', ' | ')}")

new_wb.save(FILE_NAME + '_labeled.xls')
