import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import win32print
import psycopg2
from datetime import datetime, timedelta
import time

import config
from config import configs
import render

class App:
	def __init__(self, root):
		self.root = root
		self.root.title("Stampa comande")
		
		self.thread = None
		self.stop_event = threading.Event()
		self.info_turno = None

		self.root.minsize(900, 500)
		self.root.resizable(True, True)
		self.root.grid_columnconfigure(0, minsize=400, weight=1)
		self.root.grid_columnconfigure(1, minsize=400, weight=1)
		self.root.grid_rowconfigure(1, weight=1)

		self.create_widget()
	
	def create_widget(self):
		self.frame0 = ttk.Frame(self.root)
		self.frame0.grid(row=0, column=0, padx=0, pady=10, sticky="wn")
		self.frame0.grid_columnconfigure(0, minsize=150, weight=0)
		self.frame0.grid_columnconfigure(1, minsize=250, weight=0)

		self.frame1 = ttk.Frame(self.root)
		self.frame1.grid(row=0, column=1, padx=0, pady=10, sticky="wn")
		self.frame1.grid_columnconfigure(0, minsize=200, weight=0)
		self.frame1.grid_columnconfigure(1, minsize=200, weight=0)

		self.widget_frame0()
		self.widget_frame1()

		# Riquadro di sola lettura per log
		self.log_box = tk.Text(self.root, state='disabled', height=10, width=40)
		self.log_box.grid(row=1, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="nsew")

	def widget_frame0(self):
		# Label titolo 1
		self.ltitolo1 = ttk.Label(self.frame0, text="Processo di stampa automatica", font=("Helvetica", 12, "bold"))
		self.ltitolo1.grid(row=0, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="w")

		# Input IP del server
		self.lserver = ttk.Label(self.frame0, text="Server di connessione:")
		self.lserver.grid(row=1, column=0, padx=10, pady=[0, 10], sticky="w")
		
		#self.inputserver = tk.StringVar()
		self.inputserver = ttk.Entry(self.frame0)
		self.inputserver.grid(row=1, column=1, padx=10, pady=[0, 10], sticky="ew")
		self.inputserver.insert(0, configs['PostgreSQL']['server'])

		# Input stampante
		self.lstampante = ttk.Label(self.frame0, text="Stampante:")
		self.lstampante.grid(row=2, column=0, padx=10, pady=[0, 10], sticky="w")
		
		printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
		self.options = [p[2] for p in printers]
		self.inputstampante = ttk.Combobox(self.frame0, values=self.options)
		self.inputstampante.set(configs['Stampa']['stampante'])
		self.inputstampante.grid(row=2, column=1, padx=10, pady=[0, 10], sticky="ew")

		self.btnsave = ttk.Button(self.frame0, text="Salva configurazione", command=self.save, bootstyle="outline-primary")
		self.btnsave.grid(row=3, column=0, padx=10, pady=0, sticky="w")

		self.separator = ttk.Separator(self.frame0, orient='horizontal')
		self.separator.grid(row=4, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
		
		# Azioni processo
		self.frame0b = ttk.Frame(self.frame0)
		self.frame0b.grid(row=5, column=0, columnspan=2, padx=0, pady=0, sticky="ew")
		self.frame0b.grid_columnconfigure(0, minsize=250, weight=0)
		self.frame0b.grid_columnconfigure(1, minsize=150, weight=1)

		self.lstato = ttk.Label(self.frame0b, text="Il processo è sospeso")
		self.lstato.grid(row=1, column=0, padx=10, pady=[0, 10], sticky="w")
		self.btnstart_stop = ttk.Button(self.frame0b, text="Avvia processo", command=self.processo, bootstyle="success")
		self.btnstart_stop.grid(row=1, column=1, padx=10, pady=0, sticky="ew")
	
	def widget_frame1(self):
		# Label titolo 2
		self.ltitolo2 = ttk.Label(self.frame1, text="Stampa una singola comanda", font=("Helvetica", 12, "bold"))
		self.ltitolo2.grid(row=0, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="w")

		# Input ID ordine
		self.lstampante = ttk.Label(self.frame1, text="ID dell'ordine:")
		self.lstampante.grid(row=1, column=0, padx=10, pady=[0, 10], sticky="w")

		self.numeric_var = ttk.Entry() #StringVal
		self.numeric_entry = ttk.Entry(self.frame1, textvariable=self.numeric_var, validate="key")
		self.numeric_entry['validatecommand'] = (self.numeric_entry.register(self.validate_numeric), '%P')
		self.numeric_entry.grid(row=1, column=1, padx=10, pady=[0, 10], sticky="ew")

		# Operazioni sull'ordine
		self.button1 = ttk.Button(self.frame1, text="Scarica ordine aggiornato", command=self.action1, bootstyle="primary")
		self.button1.grid(row=2, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="w")

		self.button2 = ttk.Button(self.frame1, text="Stampa comanda bar", command=self.action2, bootstyle="info")
		self.button2.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
		self.button2 = ttk.Button(self.frame1, text="Stampa comanda cucina", command=self.action2, bootstyle="warning")
		self.button2.grid(row=3, column=1, padx=10, pady=0, sticky="ew")


	def validate_numeric(self, value_if_allowed):
		return (value_if_allowed == "" or value_if_allowed.isdigit())
	
	def update_configs(self):
		configs['PostgreSQL']['server'] = self.inputserver.get()
		configs['Stampa']['stampante'] = self.inputstampante.get()

	def processo(self):
		if not self.thread or not self.thread.is_alive():
			# Avvia thread
			self.update_configs()
			self.stop_event.clear()
			self.thread = threading.Thread(target=self.query_process, daemon=True)
			self.thread.start()
			self.lstato.config(text="Il processo è in esecuzione")
			self.btnstart_stop.config(text="Arresta processo", bootstyle="danger")
		else:
			# Arresta thread
			self.stop_event.set()
			self.connection.close()
			self.lstato.config(text="Il processo è sospeso")
			self.btnstart_stop.config(text="Avvia processo", bootstyle="success")
			
	def action1(self):
		pass
	def action2(self):
		pass
	def save(self):
		self.update_configs()
		config.save()

	def log_message(self, message):
		now = datetime.now()
		self.log_box.config(state='normal')  # Rendi modificabile
		self.log_box.insert(tk.END, now.strftime("%H:%M:%S") + " | " + message + "\n")
		self.log_box.config(state='disabled')  # Torna a sola lettura
		self.log_box.see(tk.END)  # Scrolla automaticamente verso il basso

	def start_connection(self):
		self.connection = config.get_connection()

	def query_process(self):
		self.start_connection()
		cur = self.connection.cursor()

		# Aggiornamento turno di servizio
		cur.execute("SELECT * FROM shiftstart;")
		data1 = cur.fetchone()[0]
		data2 = data1 + timedelta(days=1)
		self.info_turno = "ordini.data >= '" + str(data1.date()) + "' and ordini.data < '" + str(data2.date()) + "' and ordini.ora > '" + str(data1.time()) + "'" + (" and ordini.ora < '17:00'" if data1.hour == 0 else "")

		while not self.stop_event.is_set():
			self.connection.reset()
			cur.execute("SELECT ordini.* FROM ordini LEFT JOIN passaggi_stato ON passaggi_stato.id_ordine = ordini.id \
				WHERE " + self.info_turno + " and(\
					(ordini.esportazione = 't' and passaggi_stato.stato is null) or \
					(passaggi_stato.stato is null and ordini.\"numeroTavolo\" <> '') or \
					(passaggi_stato.stato = 0 and (EXTRACT(HOUR FROM (LOCALTIME - passaggi_stato.ora)) * 3600 + \
									EXTRACT(MINUTE FROM (LOCALTIME - passaggi_stato.ora)) * 60 + \
									EXTRACT(SECOND FROM (LOCALTIME - passaggi_stato.ora))) > 30)) \
				and ordini.stato_bar <> 'evaso' and ordini.stato_cucina <> 'evaso'\
				ORDER BY ordini.esportazione desc, passaggi_stato.ora;")
			ordini = config.get_dict(cur)

			threading.Thread(target=render.processa_ordini, args=(ordini,self)).start()

			i = 0
			while i < 20 and not self.stop_event.is_set():
				time.sleep(2)
				i += 2

if __name__ == "__main__":
	config.init()
		
	root = ttk.Window(themename="flatly")
	app = App(root)
	root.mainloop()
