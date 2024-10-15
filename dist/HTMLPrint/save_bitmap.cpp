
void SaveBitmapToFile(unsigned char* buffer, int width, int height, int stride, const char* filename) {
    BITMAPFILEHEADER bmfHeader;
    BITMAPINFOHEADER bi;

    int paddedSize = stride * height;

    // Bitmap file header
    bmfHeader.bfType = 0x4D42;  // "BM"
    bmfHeader.bfSize = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER) + paddedSize;
    bmfHeader.bfReserved1 = 0;
    bmfHeader.bfReserved2 = 0;
    bmfHeader.bfOffBits = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);

    // Bitmap info header
    bi.biSize = sizeof(BITMAPINFOHEADER);
    bi.biWidth = width;
    bi.biHeight = -height;  // Negativo per immagine dritta
    bi.biPlanes = 1;
    bi.biBitCount = 32;
    bi.biCompression = BI_RGB;
    bi.biSizeImage = 0;
    bi.biXPelsPerMeter = 0;
    bi.biYPelsPerMeter = 0;
    bi.biClrUsed = 0;
    bi.biClrImportant = 0;

    // Salva l'immagine su file
    std::ofstream file(filename, std::ios::out | std::ios::binary);
    if (!file) {
        std::cerr << "Errore durante il salvataggio del file bitmap." << std::endl;
        return;
    }

    file.write((char*)&bmfHeader, sizeof(BITMAPFILEHEADER));
    file.write((char*)&bi, sizeof(BITMAPINFOHEADER));
    file.write((char*)buffer, paddedSize);
    file.close();
}