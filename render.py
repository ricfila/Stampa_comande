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
def processa_ordini(ordini):
	conn = config.get_connection()
	cur = conn.cursor()
	
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
			stampa_comanda(ordine, 'bar')
			
		if ordine['id_progressivo_cucina'] is not None:
			stampa_comanda(ordine, 'cucina')
	
	cur.close()
	conn.close()


def stampa_comanda(ordine, name_template):
	# Configura l'ambiente Jinja2
	template_dir = os.path.join(os.path.dirname(__file__), 'templates')
	env = Environment(loader=FileSystemLoader(template_dir))

	# Carica il template
	template = env.get_template(name_template + ".html")

	# Genera l'HTML
	output_html = template.render({"ordine": ordine})

	# Salva l'HTML in un file
	output_file = 'comande/' + str(ordine['id']) + '_' + name_template + '.html'
	with open(output_file, 'w', encoding="utf-8") as f:
		f.write(output_html)

	# Invia il file alla stampante
	params = [output_file, configs['Stampa']['stampante'], 'A5']
	result = subprocess.run([printer_executable] + params, capture_output=True, text=True)
	if (result.returncode != 0):
		print(result.stdout)
		print(result.stderr)
