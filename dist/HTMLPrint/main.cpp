#include <windows.h>
//#include <filesystem>
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <string>

struct PageInfo {
	const char* paper;
	const char* zoom;
	const char* mt;
	const char* mb;
	const char* mr;
	const char* ml;
};

#include "status.cpp"
#include "print.cpp"
//#include "status2.cpp"
#include "save_bitmap.cpp"

/*
Thanks to
https://github.com/bblanchon/pdfium-binaries
https://github.com/wkhtmltopdf/wkhtmltopdf/releases (wkhtmltox-0.12.5-1.mxe-cross-win64.7z)

Comando per compilare:
g++ -o bin/HTMLPrint main.cpp -Iinclude -Llib -lpdfium -lgdi32 -lwinspool
*/


int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Utilizzo: " << argv[0] << " <file_html> <nome_stampante> <dim_foglio> <zoom> <margine_alto> <margine_basso> <margine_destro> <margine_sinistro>" << std::endl;
        return 1;
    }

    const char* html_path = argv[1];
    const char* printer_name = argv[2];
	const char* pdf_path = "temp.pdf";

	PageInfo pi;
	pi.paper = (argc >= 4 ? argv[3] : "A5");
	pi.zoom = (argc >= 5 ? argv[8] : "1.25");
	pi.mt = (argc >= 6 ? argv[4] : "0");
	pi.mb = (argc >= 7 ? argv[5] : "0");
	pi.mr = (argc >= 8 ? argv[6] : "0");
	pi.ml = (argc >= 9 ? argv[7] : "0");

	/*
	// Controllo stato stampante
	std::cout << printer_name << std::endl;

	DWORD status;
	if (GetPrinterStatus(printer_name, status)) {
		PrintStatus(status);
	}
	*/

	if (!ConvertHtmlToPdf(html_path, pdf_path, &pi)) {
		return 2;
	}
	if (!PrintPdfPage(pdf_path, printer_name, &pi)) {
		return 3;
	}

	/*
	// Cancellazione PDF temporaneo dopo la stampa
	// Non necessaria: il file si può tenere per debug
	try {
		std::filesystem::remove(pdf_path);
	} catch (const std::filesystem::filesystem_error& err) {
		std::cerr << "Filesystem error: " << err.what() << '\n';
	}
	*/
	return 0;
}
