#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

void bof(char *str) {
    char buffer[50];
    // --- (Info Leak) ---
    printf("[INFO LEAK] O endereco real do buffer eh: %p\n", (void *)buffer);
    fflush(stdout); 
    strcpy(buffer, str);
    printf("Mensagem copiada!\n");
}

int main() {
    char input[500];
    printf("Servidor iniciado. Aguardando entrada...\n");
    fflush(stdout);
    if (read(STDIN_FILENO, input, 500) > 0){
        bof(input);
    }
    return 0;
}