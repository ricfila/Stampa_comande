import subprocess
import os
import threading

from render import file_comanda
from config import configs

printer_executable = "HTMLPrint/bin/HTMLPrint.exe"
formato_carta = "A5"


def processo_stampe(app, stampe):
	if len(stampe) > 0:
		app.log_stampe("--------------------", True)
	for stampa in stampe:
		stampa_comanda(stampa['ordine']['id'], stampa['template'], app)

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
