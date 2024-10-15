import os
from jinja2 import Environment, FileSystemLoader

cartella_comande = "comande"

"""
Nuovi parametri:
{{ordine.esportazione}}
{{ordine.righe_copia_cliente}}
{{ordine.righe_copia_bar}}
{{ordine.righe_copia_cucina}}
{{ordine.totale}}
{{riga.prezzo_totale}}
"""

def render_template(ordine, name_template):
	template_dir = os.path.join(os.getcwd(), 'templates')
	env = Environment(loader=FileSystemLoader(template_dir))

	# Carica il template
	template = env.get_template(name_template + ".html")
	output_html = template.render({"ordine": ordine})

	# Salva l'HTML in un file
	output_file = file_comanda(ordine['id'], name_template)
	with open(output_file, 'w', encoding="utf-8") as f:
		f.write(output_html)

def file_comanda(id, tipo):
	return f"{cartella_comande}/{id}_{tipo}.html"