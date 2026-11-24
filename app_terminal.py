"""
app_terminal.py — Interface de TERMINAL (Níveis 2 e 3).

  python app_terminal.py              -> Nível 2: dados só na memória
  python app_terminal.py --db         -> Nível 3: salva em biblioteca.db (SQLite)
"""
import argparse
from datetime import date

from modelos import Livro, Revista, Aluno, Professor, Recibo
from repositorio import RepositorioMemoria, RepositorioSQLite
from biblioteca import Biblioteca, BibliotecaErro

MENU = """
========== BIBLIOTECA ==========
 1 - Cadastrar livro          6 - Listar usuários
 2 - Cadastrar revista        7 - Emprestar
 3 - Cadastrar aluno          8 - Devolver
 4 - Cadastrar professor      9 - Empréstimos ativos
 5 - Listar acervo           10 - Buscar item
11 - Carregar dados de exemplo
 0 - Sair
================================"""


def ler_texto(msg: str) -> str:
    while True:
        valor = input(msg).strip()
        if valor:
            return valor
        print("  Campo obrigatório.")


def ler_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("  Digite um número inteiro.")


def ler_data_opcional(msg: str) -> date | None:
    texto = input(msg).strip()
    return date.fromisoformat(texto) if texto else None


class AppTerminal:
    def __init__(self, biblioteca: Biblioteca):
        self.bib = biblioteca
        # Dicionário "opção -> método": evita um if/elif gigante.
        self.acoes = {
            "1": self.cadastrar_livro, "2": self.cadastrar_revista,
            "3": self.cadastrar_aluno, "4": self.cadastrar_professor,
            "5": self.listar_acervo, "6": self.listar_usuarios,
            "7": self.emprestar, "8": self.devolver,
            "9": self.listar_ativos, "10": self.buscar,
            "11": self.dados_exemplo,
        }

    def executar(self) -> None:
        while True:
            print(MENU)
            opcao = input("Escolha: ").strip()
            if opcao == "0":
                print("Até logo!")
                return
            acao = self.acoes.get(opcao)
            if acao is None:
                print("Opção inválida.")
                continue
            try:                      # erros de regra viram mensagem, não crash
                acao()
            except (BibliotecaErro, ValueError) as erro:
                print(f"  ERRO: {erro}")

    # ---------- ações ----------
    def cadastrar_livro(self):
        item = self.bib.cadastrar_item(Livro(ler_texto("Título: "), ler_texto("Autor: ")))
        print(f"  Livro cadastrado com ID {item.id}.")

    def cadastrar_revista(self):
        item = self.bib.cadastrar_item(Revista(ler_texto("Título: "), ler_texto("Edição: ")))
        print(f"  Revista cadastrada com ID {item.id}.")

    def cadastrar_aluno(self):
        u = self.bib.cadastrar_usuario(Aluno(ler_texto("Nome: "), ler_texto("CPF: ")))
        print(f"  Aluno cadastrado com ID {u.id}.")

    def cadastrar_professor(self):
        u = self.bib.cadastrar_usuario(Professor(ler_texto("Nome: "), ler_texto("CPF: ")))
        print(f"  Professor cadastrado com ID {u.id}.")

    def listar_acervo(self):
        for item in self.bib.listar_itens():
            print(f"  {item.id:>3} | {item}")
        if not self.bib.listar_itens():
            print("  (acervo vazio)")

    def listar_usuarios(self):
        for u in self.bib.listar_usuarios():
            print(f"  {u.id:>3} | {u} | limite {u.limite_emprestimos}, prazo {u.prazo_dias} dias")
        if not self.bib.listar_usuarios():
            print("  (nenhum usuário)")

    def emprestar(self):
        emp = self.bib.emprestar(ler_int("ID do usuário: "), ler_int("ID do item: "))
        print(f"  Empréstimo {emp.id} criado. Devolver até {emp.data_prevista:%d/%m/%Y}.")

    def devolver(self):
        data = ler_data_opcional("Data da devolução (AAAA-MM-DD, Enter = hoje): ")
        emp, multa = self.bib.devolver(ler_int("ID do empréstimo: "), data)
        print(Recibo.gerar(emp, multa))   # DEPENDÊNCIA: usa Recibo só aqui

    def listar_ativos(self):
        ativos = self.bib.emprestimos_ativos()
        for e in ativos:
            print(f"  {e.id:>3} | {e.usuario.nome} -> {e.item.titulo} "
                  f"(devolver até {e.data_prevista:%d/%m/%Y})")
        if not ativos:
            print("  (nenhum empréstimo ativo)")

    def buscar(self):
        achados = self.bib.buscar_itens(ler_texto("Termo de busca: "))
        for item in achados:
            print(f"  {item.id:>3} | {item}")
        if not achados:
            print("  Nada encontrado.")

    def dados_exemplo(self):
        if self.bib.listar_itens() or self.bib.listar_usuarios():
            raise BibliotecaErro("Já existem dados; exemplo não carregado.")
        self.bib.cadastrar_item(Livro("Dom Casmurro", "Machado de Assis"))
        self.bib.cadastrar_item(Livro("O Cortiço", "Aluísio Azevedo"))
        self.bib.cadastrar_item(Revista("Superinteressante", "Ed. 450"))
        self.bib.cadastrar_usuario(Aluno("Ana", "111.111.111-11"))
        self.bib.cadastrar_usuario(Professor("Carlos", "222.222.222-22"))
        print("  Dados de exemplo carregados (3 itens, 2 usuários).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", nargs="?", const="biblioteca.db",
                        help="usa SQLite (opcionalmente informe o arquivo)")
    args = parser.parse_args()
    repo = RepositorioSQLite(args.db) if args.db else RepositorioMemoria()
    AppTerminal(Biblioteca("Biblioteca Central", repo)).executar()
