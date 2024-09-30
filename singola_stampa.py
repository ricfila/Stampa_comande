import asyncio
import win32print
import datetime
import subprocess
import os

import render
#import stampa_pdf

def main():
	printer_name = "HP3"#"\\\\CASSA3\\HP3"
	paper_format = "A5"

	print('=== Avvio di stampa comande ===')
	print('* Stampante selezionata: ' + printer_name)

	template = 'template.html'
	html_file = 'comande/output.html'
	pdf_file = 'print.pdf'

	render.render_template(template, html_file)

	executable = "HTMLPrint/bin/HTMLPrint.exe"
	params = [html_file, printer_name, paper_format]

	result = subprocess.run([executable] + params, capture_output=True, text=True)
	if (result.returncode != 0):
		print(result.stdout)
		print(result.stderr)

	#asyncio.run(stampa_pdf.print_pdf(html_file, pdf_file, printer_name))




if __name__ == "__main__":
	main()
