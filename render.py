from jinja2 import Environment, FileSystemLoader
import os
import ctypes.util
import subprocess

import config
from config import configs
printer_executable = "HTMLPrint/bin/HTMLPrint.exe"

"""
Nuovi parametri:
{{ordine.esportazione}}
{{ordine.righe_copia_cliente}}
{{ordine.righe_copia_bar}}
{{ordine.righe_copia_cucina}}
{{riga.prezzo_totale}}
"""
def processa_ordini(ordini, app):
	conn = config.get_connection()
	cur = conn.cursor()
	
	stampe_bar = []
	stampe_cucina = []
	stampe_asporto = []
	for ordine in ordini:
		cur.execute("SELECT * FROM righe JOIN righe_articoli ON righe.id = righe_articoli.id_riga WHERE righe.id_ordine = " + str(ordine['id']) + " ORDER BY righe_articoli.posizione;")

		cols = [desc[0] for desc in cur.description]
		rows = cur.fetchall()
		righe = []
		ordine['righe_copia_cliente'] = []
		ordine['righe_copia_bar'] = []
		ordine['righe_copia_cucina'] = []
		totale = 0
		for row in rows:
			riga = dict(zip(cols, row))
			riga['prezzo_totale'] = riga['prezzo'] * riga['quantita']
			totale += riga['prezzo_totale']
			if riga['copia_cliente']: ordine['righe_copia_cliente'].append(riga)
			if riga['copia_bar']: ordine['righe_copia_bar'].append(riga)
			if riga['copia_cucina']: ordine['righe_copia_cucina'].append(riga)
			righe.append(riga)
		ordine['totale'] = totale

		if ordine['id_progressivo_bar'] is not None and not ordine['esportazione']:
			stampe_bar.append({'ordine': ordine, 'template': 'bar'})
		if ordine['id_progressivo_cucina'] is not None:
			if ordine['esportazione']:
				stampe_asporto.append({'ordine': ordine, 'template': 'cucina'})
			else:
				stampe_cucina.append({'ordine': ordine, 'template': 'cucina'})

		if ordine['esportazione']:
			cur.execute("INSERT INTO passaggi_stato (id_ordine, ora, stato) VALUES (" + str(ordine['id']) + ", LOCALTIME, 10);")
		else:
			cur.execute("UPDATE passaggi_stato SET stato = 10 WHERE id_ordine = " + str(ordine['id']) + " AND stato = 0;")
	conn.commit()

	tot_stampe = len(stampe_bar) + len(stampe_cucina) + len(stampe_asporto)
	if tot_stampe > 0:
		app.log_message("Avviata la stampa di " + str(len(tot_stampe)) + " comande")
	
	for stampa in stampe_bar:
		stampa_comanda(stampa['ordine'], stampa['template'], app)
	for stampa in stampe_cucina:
		stampa_comanda(stampa['ordine'], stampa['template'], app)
	for stampa in stampe_asporto:
		stampa_comanda(stampa['ordine'], stampa['template'], app)
	
	cur.close()
	conn.close()


def stampa_comanda(ordine, name_template, app):
	template_dir = os.path.join(os.path.dirname(__file__), 'templates')
	env = Environment(loader=FileSystemLoader(template_dir))

	# Carica il template
	template = env.get_template(name_template + ".html")
	output_html = template.render({"ordine": ordine})

	# Salva l'HTML in un file
	output_file = 'comande/' + str(ordine['id']) + '_' + name_template + '.html'
	with open(output_file, 'w', encoding="utf-8") as f:
		f.write(output_html)

	# Invia il file alla stampante
	params = [output_file, configs['Stampa']['stampante'], 'A5']
	result = subprocess.run([printer_executable] + params, capture_output=True, text=True)
	if (result.returncode != 0):
		app.log_message("Errore di stampa della comanda " + str(ordine['progressivo']) + '_' + name_template + "\n" + result.stderr)
		return False
	return True
