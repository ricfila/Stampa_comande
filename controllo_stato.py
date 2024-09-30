import win32print
import datetime

def get_status(printer_name):
	try:
		hprint = win32print.OpenPrinter(printer_name)
		d = win32print.GetPrinter(hprint, 2)
		win32print.ClosePrinter(hprint)
		return d['Status'], d['Attributes']
	except Exception as e:
		print(f"Errore durante l'accesso alla stampante: {str(e)}")
		return None, None

def print_status(status, attributes):
	printer_status_codes = {
		0: "Pronta",
		0x00000002: "Errore",
		0x00000004: "In attesa",
		0x00000008: "Stampa in corso",
		0x00000010: "Bloccata",
		0x00000020: "Carta esaurita",
		0x00000040: "Fuori linea",
		0x00000100: "Inizializzazione in corso",
		0x00000200: "Ripristino",
		0x00000400: "Non risponde",
		0x00000800: "Rimuovere il foglio"
	}
	if attributes & win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE:
		status_message = "Stampante offline"
	else:
		status_message = printer_status_codes.get(status, f"Stato sconosciuto (codice: {status})")
	
	now = datetime.datetime.now()
	addzero = lambda x: '0' + str(x) if x < 10 else str(x)
	print("* Stato alle " + addzero(now.hour) + ":" + addzero(now.minute) + ":" + addzero(now.second) + " --> " + status_message)


def ready(status, attributes):
	return not (attributes & win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE) and status == 0


printer_name = "\\\\CASSA3\\HP3"
paper_format = "A5"

print('* Controllo stato di: ' + printer_name)

status, attributes = get_status(printer_name)
print_status(status, attributes)

if not ready(status, attributes):
	while not ready(status, attributes):
		status, attributes = get_status(printer_name)

	print_status(status, attributes)

old_status = status
old_attributes = attributes
while True:
	status, attributes = get_status(printer_name)
	if status != old_status or attributes != old_attributes:
		print_status(status, attributes)
	old_status = status
	old_attributes = attributes



