import subprocess
import os
import threading
import win32print

from render import file_comanda
from config import configs

printer_executable = "HTMLPrint/bin/HTMLPrint.exe"
formato_carta = "A5"

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
	
	return(status_message)


def printer_ready(printer_name):
	status, attributes = get_status(printer_name)
	return not (attributes & win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE) and status == 0


def processo_stampe(app, stampe):
	stampante = configs['Stampa']['stampante']
	out = ''
	for stampa in stampe:
		out += ("" if len(out) == 0 else ",") + str(stampa['ordine']['id']) + "_" + stampa['template']
	if not printer_ready(stampante):
		app.log_message(f"Stampante {stampante} offline. {len(stampe)} stampe in attesa: {out}\n")
		while not printer_ready(stampante) and not app.stop_event.is_set(): pass
	
	if not app.stop_event.is_set():
		if len(stampe) > 0:
			app.log_message(f"Avviata la stampa di {len(stampe)} comande\n")
			app.log_stampe("--------------------", True)
		for stampa in stampe:
			stampa_comanda(stampa['ordine']['id'], stampa['template'], app)
	else:
		app.log_message(f"Processo terminato. {len(stampe)} stampe annullate: {out}")

def stampa_singola(app, template):
	id = app.input_id.get()
	if not id.isdigit():
		app.stato_singolo.config(text=f"Inserire un id valido")
		return
	if os.path.isfile(file_comanda(id, "cliente")):
		if os.path.isfile(file_comanda(id, template)):
			threading.Thread(target=stampa_comanda, args=(id, template, app, True)).start()
			app.stato_singolo.config(text="")
		else:
			app.stato_singolo.config(text=f"L'ordine {id} non prevede la copia {template}")
	else:
		app.stato_singolo.config(text=f"L'ordine {id} non è stato scaricato")

def stampa_comanda(id, tipo, app, manuale = False):
	output_file = file_comanda(id, tipo)
	params = [output_file, configs['Stampa']['stampante'], formato_carta]
	result = subprocess.run([printer_executable] + params, capture_output=True, text=True)
	if (result.returncode != 0):
		app.log_message("Errore di stampa della comanda ID " + str(id) + '_' + tipo + "\n" + result.stderr)
		if manuale:
			app.stato_singolo.config(text="Stampa fallita")
		else:
			app.log_stampe(f"{id}_{tipo}", False)
	else:
		app.log_stampe(f"Stampata manualmente {id}_{tipo}" if manuale else f"Stampata {id}_{tipo}", True)
