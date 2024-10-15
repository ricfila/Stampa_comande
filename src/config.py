import configparser
import os
import psycopg2

configs = configparser.ConfigParser()
config_file_path = os.path.join(os.getcwd(), 'configs.ini')

def init():
	# Crea il file configs.ini se non esiste
	if not os.path.exists(config_file_path):
		open(config_file_path, 'x')

	# Importa le impostazioni dal file
	configs.read(config_file_path)

	# Aggiunge impostazioni di default se non erano presenti nel file
	sezioni = {"PostgreSQL": {"server": "192.168.1.1",
							  "port": 5432,
							  "database": "sagra",
							  "username": "postgres",
							  "password": "pwd"},
			   "Stampa": {"stampante": "Microsoft Print to PDF"}
			  }

	for k, v in sezioni.items():
		if (k not in configs.sections()
				or any(key not in configs[k] for key in v.keys())):
			configs[k] = v

	# Salva tutte le impostazioni (vecchie e nuove) su file
	save()

def save():
	configfile = open(config_file_path, 'w')
	configs.write(configfile)
	configfile.close()

def get_connection(app):
	conn = None
	try:
		conn = psycopg2.connect(database=configs['PostgreSQL']['database'],
								host=configs['PostgreSQL']['server'],
								user=configs['PostgreSQL']['username'],
								password=configs['PostgreSQL']['password'],
								port=configs['PostgreSQL']['port'])
	except psycopg2.OperationalError as e:
		app.log_message(f"Errore di operazione durante la creazione della connessione: {e}")
	except psycopg2.DatabaseError as e:
		app.log_message(f"Errore del database durante la creazione della connessione: {e}")
	except Exception as e:
		app.log_message(f"Errore durante la creazione della connessione: {e}")
	finally:
		return conn

def get_dict(cur):
	cols = [desc[0] for desc in cur.description]
	rows = cur.fetchall()
	return [dict(zip(cols, row)) for row in rows]
