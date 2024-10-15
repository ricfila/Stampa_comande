#include <fpdfview.h>

bool ConvertHtmlToPdf(const std::string& htmlFilePath, const std::string& pdfFilePath, PageInfo *pi) {
    char buffer[MAX_PATH];  // Buffer per contenere il percorso
    GetModuleFileNameA(NULL, buffer, MAX_PATH);  // Recupera il percorso completo dell'eseguibile
    
    std::string path(buffer);
    
    // Trova l'ultimo separatore di percorso (backslash) e rimuove il nome dell'eseguibile
    size_t pos = path.find_last_of("\\/");
    if (pos != std::string::npos) {
        path = path.substr(0, pos);  // Ottiene solo la directory
    }

    // Assumiamo che wkhtmltopdf.exe sia nella cartella "bin" del progetto
    std::string command = path;
    command += "\\wkhtmltopdf.exe --quiet ";
	command += "--page-size ";
	command += pi->paper;
	command += " --zoom ";
	command += pi->zoom;
	command += " --margin-top ";
	command += pi->mt;
	command += " --margin-bottom ";
	command += pi->mb;
	command += " --margin-right ";
	command += pi->mr;
	command += " --margin-left ";
	command += pi->ml;
    command += " ";
    command += htmlFilePath;
    command += " ";
    command += pdfFilePath;

    // Esegui il comando
    int result = system(command.c_str());
    if (result == 0) {
        //std::cout << "Conversione HTML in PDF completata con successo!" << std::endl;
		return true;
    } else {
        std::cerr << "Errore durante la conversione HTML in PDF." << std::endl;
		return false;
    }
}


// Funzione per ottenere le dimensioni in pixel della pagina della stampante
void GetPrinterPageSize(HDC printerDC, int& pageWidth, int& pageHeight) {
    pageWidth = GetDeviceCaps(printerDC, HORZRES);  // Larghezza della pagina in pixel
    pageHeight = GetDeviceCaps(printerDC, VERTRES); // Altezza della pagina in pixel
}


// Funzione per stampare una pagina PDF
bool PrintPdfPage(const char* pdf_path, const char* printer_name, PageInfo *pi) {
    // Inizializza PDFium
    FPDF_InitLibrary();

    // Carica il documento PDF
    FPDF_DOCUMENT pdf_doc = FPDF_LoadDocument(pdf_path, nullptr);
    if (!pdf_doc) {
        std::cerr << "Errore nel caricamento del PDF." << std::endl;
        FPDF_DestroyLibrary();
        return false;
    }

    // Recupera il numero di pagine nel PDF
    int page_count = FPDF_GetPageCount(pdf_doc);

    // Ottieni il device context (DC) della stampante
    HDC printerDC = CreateDC(NULL, printer_name, NULL, NULL);
    if (!printerDC) {
        std::cerr << "Errore: impossibile aprire la stampante." << std::endl;
        FPDF_CloseDocument(pdf_doc);
        FPDF_DestroyLibrary();
        return false;
    }

    DEVMODE* devMode = nullptr;
    HANDLE hPrinter = nullptr;
    // Ottieni un handle alla stampante
    if (!OpenPrinter((LPSTR)printer_name, &hPrinter, NULL)) {
        std::cerr << "Errore: impossibile aprire la stampante." << std::endl;
        FPDF_CloseDocument(pdf_doc);
        FPDF_DestroyLibrary();
        return false;
    }
    // Recupera la dimensione richiesta del DEVMODE
    LONG size = DocumentProperties(NULL, hPrinter, (LPSTR)printer_name, NULL, NULL, 0);
    if (size <= 0) {
        std::cerr << "Errore: lettura parametri di default non riuscita." << std::endl;
        FPDF_CloseDocument(pdf_doc);
        FPDF_DestroyLibrary();
        return false;
    }

	// Imposta il formato carta
    //DEVMODE* devMode = (DEVMODE*)GlobalAlloc(GPTR, sizeof(DEVMODE));
    devMode = (DEVMODE*)GlobalAlloc(GPTR, size);
    if (devMode) {
        if (DocumentProperties(NULL, hPrinter, (LPSTR)printer_name, devMode, NULL, DM_OUT_BUFFER) == IDOK) {
            devMode->dmFields = DM_PAPERSIZE;
            if (!strcmp(pi->paper, "A4")) {
                devMode->dmPaperSize = DMPAPER_A4;
                std::cout << "A4" << std::endl;
            } else {
                devMode->dmPaperSize = DMPAPER_A5;
                std::cout << "A5" << std::endl;
            }
            
            HDC newDC = ResetDC(printerDC, devMode);
            if (!newDC) {
                std::cerr << "Errore durante ResetDC" << std::endl;
                GlobalFree(devMode);
                ClosePrinter(hPrinter);
                return false;
            }
        } else {
            std::cerr << "Errore DocumentProperties" << std::endl;
        }
        GlobalFree(devMode);
    }
    ClosePrinter(hPrinter);

	// Ottieni le dimensioni della pagina della stampante
    int pageWidth, pageHeight;
    GetPrinterPageSize(printerDC, pageWidth, pageHeight);

    // Configura il documento di stampa
    DOCINFO di;
    memset(&di, 0, sizeof(DOCINFO));
    di.cbSize = sizeof(DOCINFO);
    di.lpszDocName = "Stampa comanda";

    // Inizia il lavoro di stampa
    if (StartDoc(printerDC, &di) <= 0) {
        std::cerr << "Errore durante l'inizio del lavoro di stampa." << std::endl;
        DeleteDC(printerDC);
        FPDF_CloseDocument(pdf_doc);
        FPDF_DestroyLibrary();
        return false;
    }

    // Ciclo su tutte le pagine del PDF
    for (int i = 0; i < page_count; ++i) {
        FPDF_PAGE page = FPDF_LoadPage(pdf_doc, i);
        if (!page) {
            std::cerr << "Errore nel caricamento della pagina " << i + 1 << "." << std::endl;
            continue;
        }

        // Recupera le dimensioni della pagina
        double width = FPDF_GetPageWidth(page);
        double height = FPDF_GetPageHeight(page);
		
		// Calcola il fattore di scala per adattare il PDF alla larghezza della pagina della stampante
        double scale = (double)pageWidth / width;
        // Ridimensiona l'altezza in base alla scala
        int renderWidth = (int)(width * scale);
        int renderHeight = (int)(height * scale);

        // Crea un bitmap per renderizzare la pagina
        FPDF_BITMAP bitmap = FPDFBitmap_Create(renderWidth, renderHeight, 0);
        FPDFBitmap_FillRect(bitmap, 0, 0, renderWidth, renderHeight, 0xFFFFFFFF); // Sfondo bianco

        // Renderizza la pagina nel bitmap
        FPDF_RenderPageBitmap(bitmap, page, 0, 0, renderWidth, renderHeight, 0, 0);

        // Recupera il buffer del bitmap
        unsigned char* buffer = (unsigned char*)FPDFBitmap_GetBuffer(bitmap);
        int stride = FPDFBitmap_GetStride(bitmap);

		// Salva il bitmap su disco (ad esempio, per la pagina 1 "pagina_1.bmp")
		/*
		std::string filename = "pagina_" + std::to_string(i + 1) + ".bmp";
		SaveBitmapToFile(buffer, (int)width, (int)height, stride, filename.c_str());
		*/

        // Inizia una nuova pagina di stampa
        if (StartPage(printerDC) <= 0) {
            std::cerr << "Errore durante l'inizio di una nuova pagina di stampa." << std::endl;
            continue;
        }

		// Crea una bitmap compatibile con il DC della stampante
		HBITMAP hBitmap = CreateCompatibleBitmap(printerDC, (int)width, (int)height);		
		
        // Stampa il bitmap sulla pagina
        BITMAPINFO bmi = {0};
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = renderWidth;
        bmi.bmiHeader.biHeight = -renderHeight; // Negativo per l'orientamento corretto
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

		// Centra l'immagine sulla pagina della stampante
        int xOffset = (pageWidth - renderWidth) / 2;
        int yOffset = (pageHeight - renderHeight) / 2;

        SetDIBitsToDevice(
            printerDC, xOffset, yOffset, renderWidth, renderHeight, 0, 0, 0, renderHeight,
            buffer, &bmi, DIB_RGB_COLORS
        );
		
        // Fine della pagina
        EndPage(printerDC);

        // Rilascia le risorse
        FPDFBitmap_Destroy(bitmap);
        FPDF_ClosePage(page);
    }

    // Fine del lavoro di stampa
    EndDoc(printerDC);

    // Rilascia il DC della stampante
    DeleteDC(printerDC);

    // Chiude il documento PDF
    FPDF_CloseDocument(pdf_doc);

    // Deinizializza PDFium
    FPDF_DestroyLibrary();

    //std::cout << "Stampa completata con successo!" << std::endl;
	return true;
}
