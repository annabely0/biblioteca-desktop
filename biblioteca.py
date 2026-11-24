"""
biblioteca.py — Camada de REGRAS DE NEGÓCIO (o "cérebro" do sistema).
Terminal e janela chamam este arquivo; as regras ficam em UM lugar só.
"""
from datetime import date

from modelos import Acervo, Emprestimo, Item, Pessoa
from repositorio import Repositorio


class BibliotecaErro(Exception):
    """Erro de regra de negócio (ex.: item já emprestado)."""


class Biblioteca:
    def __init__(self, nome: str, repositorio: Repositorio):
        self._nome = nome
        self._repo = repositorio          # ASSOCIAÇÃO: recebido de fora
        self._acervo = Acervo()           # COMPOSIÇÃO: criado AQUI dentro;
                                          # sem Biblioteca, não há Acervo
        self._usuarios: list[Pessoa] = []     # AGREGAÇÃO (pessoas nascem fora)
        self._emprestimos: list[Emprestimo] = []
        self._carregar()

    @property
    def nome(self) -> str:
        return self._nome

    def _carregar(self) -> None:
        """Ao abrir o programa, traz do banco tudo que já foi salvo."""
        for item in self._repo.carregar_itens():
            self._acervo.adicionar(item)
        self._usuarios = self._repo.carregar_usuarios()
        itens = {i.id: i for i in self._acervo.todos()}
        usuarios = {u.id: u for u in self._usuarios}
        self._emprestimos = self._repo.carregar_emprestimos(itens, usuarios)

    # ---------------- cadastros ----------------
    def cadastrar_item(self, item: Item) -> Item:
        self._repo.salvar_item(item)      # gera o id
        self._acervo.adicionar(item)
        return item

    def cadastrar_usuario(self, usuario: Pessoa) -> Pessoa:
        if any(u.cpf == usuario.cpf for u in self._usuarios):
            raise BibliotecaErro(f"Já existe usuário com CPF {usuario.cpf}.")
        self._repo.salvar_usuario(usuario)
        self._usuarios.append(usuario)
        return usuario

    # ---------------- consultas ----------------
    def listar_itens(self) -> list[Item]:
        return self._acervo.todos()

    def buscar_itens(self, termo: str) -> list[Item]:
        return self._acervo.buscar(termo)

    def listar_usuarios(self) -> list[Pessoa]:
        return list(self._usuarios)

    def listar_emprestimos(self) -> list[Emprestimo]:
        return list(self._emprestimos)

    def emprestimos_ativos(self, usuario: Pessoa | None = None) -> list[Emprestimo]:
        return [e for e in self._emprestimos
                if e.ativo and (usuario is None or e.usuario is usuario)]

    # ---------------- operações ----------------
    def emprestar(self, usuario_id: int, item_id: int,
                  hoje: date | None = None) -> Emprestimo:
        usuario = next((u for u in self._usuarios if u.id == usuario_id), None)
        item = self._acervo.buscar_por_id(item_id)
        if usuario is None:
            raise BibliotecaErro("Usuário não encontrado.")
        if item is None:
            raise BibliotecaErro("Item não encontrado.")
        if not item.disponivel:
            raise BibliotecaErro("Item indisponível (já emprestado).")
        if len(self.emprestimos_ativos(usuario)) >= usuario.limite_emprestimos:
            raise BibliotecaErro(
                f"{usuario.nome} atingiu o limite de {usuario.limite_emprestimos} empréstimos.")

        emp = Emprestimo(usuario, item, hoje or date.today())
        item.marcar_emprestado()
        self._repo.salvar_emprestimo(emp)
        self._repo.salvar_item(item)      # grava disponivel=False
        self._emprestimos.append(emp)
        return emp

    def devolver(self, emprestimo_id: int, hoje: date | None = None) -> tuple[Emprestimo, float]:
        emp = next((e for e in self._emprestimos if e.id == emprestimo_id), None)
        if emp is None:
            raise BibliotecaErro("Empréstimo não encontrado.")
        if not emp.ativo:
            raise BibliotecaErro("Este empréstimo já foi devolvido.")
        multa = emp.devolver(hoje)
        emp.item.marcar_disponivel()
        self._repo.salvar_emprestimo(emp)
        self._repo.salvar_item(emp.item)
        return emp, multa
