import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import win32print
from datetime import datetime

from src import config
from src.config import configs
from src import ordini
from src import printfile

class App:
	def __init__(self, root):
		self.root = root
		self.root.title("Stampa comande")
		
		self.thread = None
		self.stop_event = threading.Event()
		self.info_turno = None

		self.root.minsize(1000, 500)
		self.root.resizable(True, True)
		self.root.grid_columnconfigure(0, minsize=400, weight=0)
		self.root.grid_columnconfigure(1, minsize=500, weight=1)
		self.root.grid_rowconfigure(3, weight=1)

		self.create_widget()
	
	def create_widget(self):
		self.lturno = ttk.Label(self.root, text="Avviare il processo per identificare il turno di lavoro")
		self.lturno.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nw")

		self.separator = ttk.Separator(self.root, orient='horizontal')
		self.separator.grid(row=1, column=0, columnspan=2, padx=5, pady=[0, 10], sticky="ew")

		self.frame0 = ttk.Frame(self.root)
		self.frame0.grid(row=2, column=0, padx=0, pady=[0, 10], sticky="nw")
		self.frame0.grid_columnconfigure(0, minsize=150, weight=0)
		self.frame0.grid_columnconfigure(1, minsize=250, weight=0)

		self.frame1 = ttk.Frame(self.root)
		self.frame1.grid(row=2, column=1, padx=0, pady=[0, 10], sticky="nw")
		self.frame1.grid_columnconfigure(0, minsize=250, weight=0)
		self.frame1.grid_columnconfigure(1, minsize=250, weight=0)

		self.framelog = ttk.Frame(self.root)
		self.framelog.grid(row=3, column=0, columnspan=2, padx=0, pady=[0, 10], sticky="nsew")
		self.framelog.grid_columnconfigure(0, minsize=200, weight=1)
		self.framelog.grid_columnconfigure(2, minsize=50, weight=0)
		self.framelog.grid_columnconfigure(4, minsize=50, weight=0)
		self.framelog.grid_rowconfigure(1, weight=1)

		self.widget_frame0()
		self.widget_frame1()
		self.widget_framelog()

	def widget_frame0(self):
		# Label titolo 1
		self.ltitolo1 = ttk.Label(self.frame0, text="Processo di stampa automatica", font=("Helvetica", 12, "bold"))
		self.ltitolo1.grid(row=0, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="wn")

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

		self.input_id = ttk.Entry() #StringVal
		self.input_id = ttk.Entry(self.frame1, textvariable=self.input_id, validate="key")
		self.input_id['validatecommand'] = (self.input_id.register(self.validate_numeric), '%P')
		self.input_id.grid(row=1, column=1, padx=10, pady=[0, 10], sticky="ew")

		self.stato_singolo = ttk.Label(self.frame1, text="")
		self.stato_singolo.grid(row=2, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="ne")

		# Operazioni sull'ordine
		self.btnscarica = ttk.Button(self.frame1, text="Scarica ordine aggiornato", command=lambda:ordini.scarica(self), bootstyle="primary")
		self.btnscarica.grid(row=3, column=0, padx=10, pady=[0, 10], sticky="ew")
		self.btncliente = ttk.Button(self.frame1, text="Stampa ricevuta cliente", command=lambda:printfile.stampa_singola(self, 'cliente'), bootstyle="secondary")
		self.btncliente.grid(row=3, column=1, padx=10, pady=[0, 10], sticky="ew")
		self.btnbar = ttk.Button(self.frame1, text="Stampa comanda bar", command=lambda:printfile.stampa_singola(self, 'bar'), bootstyle="info")
		self.btnbar.grid(row=4, column=1, padx=10, pady=[0, 10], sticky="ew")
		self.btncucina = ttk.Button(self.frame1, text="Stampa comanda cucina", command=lambda:printfile.stampa_singola(self, 'cucina'), bootstyle="warning")
		self.btncucina.grid(row=5, column=1, padx=10, pady=0, sticky="ew")

	def widget_framelog(self):
		ltitolo1 = ttk.Label(self.framelog, text="Log generali", font=("Helvetica", 12, "bold"))
		ltitolo1.grid(row=0, column=0, columnspan=2, padx=10, pady=[0, 10], sticky="wn")

		self.log_box = tk.Text(self.framelog, state='disabled', height=10, width=40)
		self.log_box.grid(row=1, column=0, padx=[10, 0], pady=0, sticky="nsew")
		scrollb = ttk.Scrollbar(self.framelog, command=self.log_box.yview)
		scrollb.grid(row=1, column=1, sticky='nsew')
		self.log_box['yscrollcommand'] = scrollb.set

		ltitolo2 = ttk.Label(self.framelog, text="Stampe eseguite", font=("Helvetica", 12, "bold"), bootstyle="success")
		ltitolo2.grid(row=0, column=2, columnspan=2, padx=10, pady=[0, 10], sticky="wn")

		self.log_box_stampe = tk.Text(self.framelog, state='disabled', height=10, width=40)
		self.log_box_stampe.grid(row=1, column=2, padx=[10, 0], pady=0, sticky="nsew")
		scrollbs = ttk.Scrollbar(self.framelog, command=self.log_box_stampe.yview)
		scrollbs.grid(row=1, column=3, sticky='nsew')
		self.log_box_stampe['yscrollcommand'] = scrollbs.set

		ltitolo3 = ttk.Label(self.framelog, text="Stampe fallite", font=("Helvetica", 12, "bold"), bootstyle="danger")
		ltitolo3.grid(row=0, column=4, columnspan=2, padx=10, pady=[0, 10], sticky="wn")

		self.log_box_fallite = tk.Text(self.framelog, state='disabled', height=10, width=40)
		self.log_box_fallite.grid(row=1, column=4, padx=[10, 0], pady=0, sticky="nsew")
		scrollbf = ttk.Scrollbar(self.framelog, command=self.log_box_fallite.yview)
		scrollbf.grid(row=1, column=5, sticky='nsew', padx=[0, 10])
		self.log_box_fallite['yscrollcommand'] = scrollbf.set

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
			self.thread = threading.Thread(target=ordini.query_process, args=(self,), daemon=True)
			self.thread.start()
			self.lstato.config(text="Il processo è in esecuzione")
			self.btnstart_stop.config(text="Arresta processo", bootstyle="danger")
		else:
			# Arresta thread
			self.btnstart_stop.config(state="disabled")
			self.stop_event.set()
			self.log_message("Il processo è stato arrestato dall'utente\n")

	def fine_processo(self):
		self.lstato.config(text="Il processo è sospeso")
		self.btnstart_stop.config(text="Avvia processo", bootstyle="success")
		self.btnstart_stop.config(state="normal")

	def save(self):
		self.update_configs()
		config.save()

	def log_message(self, message):
		now = datetime.now()
		self.log_box.config(state='normal')  # Rendi modificabile
		out_text = now.strftime("%H:%M:%S") + " | " + message
		self.log_box.insert(tk.END, out_text)
		self.log_box.config(state='disabled')  # Torna a sola lettura
		self.log_box.see(tk.END)  # Scrolla automaticamente verso il basso
		try:
			with open("general.log", "a", encoding="utf-8") as logfile:
				logfile.write(out_text)
		except Exception as e:
			print(f"Errore di scrittura log generale: {e}")
	
	def log_stampe(self, message, riuscita):
		if riuscita:
			target = self.log_box_stampe
		else:
			target = self.log_box_fallite
		target.config(state='normal')  # Rendi modificabile
		target.insert(tk.END, message + "\n")
		target.config(state='disabled')  # Torna a sola lettura
		target.see(tk.END)  # Scrolla automaticamente verso il basso
		try:
			with open("stampe_" + ("eseguite" if riuscita else "fallite") + ".log", "a", encoding="utf-8") as logfile:
				logfile.write(message + "\n")
		except Exception as e:
			print("Errore di scrittura log stampe " + ("eseguite" if riuscita else "fallite") + f": {e}")


if __name__ == "__main__":
	config.init()
	print("Current working directory:", os.getcwd())
		
	root = ttk.Window(themename="flatly")
	root.state("zoomed")
	app = App(root)
	root.mainloop()
