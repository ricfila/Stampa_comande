
import win32print
import win32ui
import os
from PIL import Image, ImageWin

#win32print.GetDefaultPrinter()

output_path = 'img.png'

# Imposta una stampante
printer_name = "HP4"#"ET-2720 Series(Rete)"  # Inserisci il nome della tua stampante




# Carica l'immagine
image = Image.open(output_path)

"""
# Dimensioni A5 in punti (DPI = 200)
A5_WIDTH = int(148 * 200 / 25.4)  # 148mm convertiti in punti
A5_HEIGHT = int(210 * 200 / 25.4)  # 210mm convertiti in punti
# Calcola il rapporto di ridimensionamento
width_ratio = A5_WIDTH / image.width
height_ratio = A5_HEIGHT / image.height
# Usa il rapporto più piccolo per mantenere il rapporto d'aspetto
scale_ratio = min(width_ratio, height_ratio)
# Calcola le nuove dimensioni dell'immagine ridimensionata
new_width = int(image.width * scale_ratio)
new_height = int(image.height * scale_ratio)
# Ridimensiona l'immagine mantenendo il rapporto d'aspetto
resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

"""

hPrinter = win32print.OpenPrinter(printer_name)
hDC = win32ui.CreateDC()
hDC.CreatePrinterDC(printer_name)



# Ottieni DEVMODE per configurare il formato della pagina
devmode = win32print.GetPrinter(hPrinter, 2)["pDevMode"]
# Imposta il formato carta su A5 per il documento corrente
devmode.PaperSize = 11  # 11 = A5
# Avvia il lavoro di stampa
#hDC.SetMapMode(win32ui.MM_TWIPS)
#hDC.SetViewportExt((A5_WIDTH, A5_HEIGHT))



# Imposta il lavoro di stampa
win32print.StartDocPrinter(hPrinter, 1, ("Immagine di Test", None, "RAW"))
win32print.StartPagePrinter(hPrinter)



# Ottieni il contesto della finestra
hDC.StartDoc("Immagine di Test")
hDC.StartPage()

#x_offset = (A5_WIDTH - new_width) // 2
#y_offset = (A5_HEIGHT - new_height) // 2
dib = ImageWin.Dib(image)
dib.draw(hDC.GetHandleOutput(), (0, 0, image.width*3, image.height*3))

# Termina la pagina e il lavoro
hDC.EndPage()
hDC.EndDoc()
win32print.EndPagePrinter(hPrinter)
win32print.EndDocPrinter(hPrinter)
win32print.ClosePrinter(hPrinter)




