import os
import threading
import time
from datetime import timedelta
from psycopg2 import DatabaseError, OperationalError

import config
from render import render_template
import print

secondi_attesa = 20


def query_process(app):
	conn = config.get_connection()
	cur = conn.cursor()

	try:
		# Aggiornamento turno di servizio
		cur.execute("SELECT * FROM shiftstart;")
		data1 = cur.fetchone()[0]
		data2 = data1 + timedelta(days=1)
		app.info_turno = "ordini.data >= '" + str(data1.date()) + "' and ordini.data < '" + str(data2.date()) + "' and ordini.ora > '" + str(data1.time()) + "'" + (" and ordini.ora < '17:00'" if data1.hour == 0 else "")
		text_turno = data1.strftime("%A %d") + (" pranzo" if data1.hour < 17 else " cena")
		app.lturno.config(text=("Turno di " + text_turno))
		app.log_message("Processo avviato nel turno di " + text_turno)

		while not app.stop_event.is_set():
			try:
				conn.reset()
				cur.execute("SELECT ordini.* FROM ordini LEFT JOIN passaggi_stato ON passaggi_stato.id_ordine = ordini.id \
					WHERE " + app.info_turno + " and(\
						(ordini.esportazione = 't' and passaggi_stato.stato is null) or \
						(passaggi_stato.stato is null and ordini.\"numeroTavolo\" <> '') or \
						(passaggi_stato.stato = 0 and (EXTRACT(HOUR FROM (LOCALTIME - passaggi_stato.ora)) * 3600 + \
										EXTRACT(MINUTE FROM (LOCALTIME - passaggi_stato.ora)) * 60 + \
										EXTRACT(SECOND FROM (LOCALTIME - passaggi_stato.ora))) > 30)) \
					and ordini.stato_bar <> 'evaso' and ordini.stato_cucina <> 'evaso'\
					ORDER BY ordini.esportazione desc, passaggi_stato.ora;")
				ordini = config.get_dict(cur)

				processa_ordini(ordini, app)

			except OperationalError as e:
				app.log_message(f"Errore di connessione (nuovo tentativo tra {secondi_attesa} secondi): {e}")
			except DatabaseError as e:
				app.log_message(f"Errore del database (nuovo tentativo tra {secondi_attesa} secondi): {e}")
			except Exception as e:
				app.log_message(f"Errore durante l'esecuzione del processo automatico (nuovo tentativo tra {secondi_attesa} secondi): {e}")
			finally:
				i = 0
				while i < secondi_attesa and not app.stop_event.is_set():
					time.sleep(2)
					i += 2
	
	except OperationalError as e:
		app.log_message(f"Errore di connessione durante l'inizializzazione del processo automatico: {e}")
	except DatabaseError as e:
		app.log_message(f"Errore del database durante l'inizializzazione del processo automatico: {e}")
	except Exception as e:
		app.log_message(f"Errore durante l'inizializzazione del processo automatico: {e}")
	finally:
		cur.close()
		conn.close()

			
def processa_ordini(ordini, app):
	conn = config.get_connection()
	cur = conn.cursor()
	
	stampe_bar = []
	stampe_cucina = []
	stampe_asporto = []
	for ordine in ordini:
		ordine = processa_singolo_ordine(conn, ordine, app)

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
		app.log_message(f"Avviata la stampa di {tot_stampe} comande")
	
	threading.Thread(target=print.processo_stampe, args=(app, (stampe_bar + stampe_cucina + stampe_asporto))).start()
	
	cur.close()
	conn.close()

def processa_singolo_ordine(conn, ordine, app):
	try:
		cur = conn.cursor()
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

		render_template(ordine, 'cliente')
		if ordine['id_progressivo_bar'] is not None and not ordine['esportazione']:
			render_template(ordine, 'bar')
		if ordine['id_progressivo_cucina'] is not None:
			render_template(ordine, 'cucina')
		
	except OperationalError as e:
		app.log_message(f"Errore di connessione: {e}")
	except DatabaseError as e:
		app.log_message(f"Errore del database: {e}")
	except Exception as e:
		app.log_message("Errore durante il processamento dell'ordine ID " + str(ordine['id']) + f": {e}")
	finally:
		cur.close()
		return ordine

def scarica(app):
	id = app.input_id.get()
	if not id.isdigit():
		app.stato_singolo.config(text=f"Inserire un id valido")
		return
	conn = config.get_connection()
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM ordini WHERE id = {id};")
	if cur.rowcount == 1:
		ordini = config.get_dict(cur)
		processa_singolo_ordine(conn, ordini[0], app)
		app.stato_singolo.config(text=f"")
	else:
		app.stato_singolo.config(text=f"L'ordine con ID {id} non esiste")
	cur.close()
	conn.close()

