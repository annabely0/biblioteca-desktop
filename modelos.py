"""
modelos.py — Camada de DOMÍNIO do sistema de biblioteca.

Aqui ficam as "coisas do mundo real": pessoas, itens, empréstimos...
Nada neste arquivo sabe falar com banco de dados, terminal ou janela.
"""
from abc import ABC, abstractmethod
from datetime import date, timedelta


# =====================================================================
# HERANÇA + POLIMORFISMO (1): hierarquia de PESSOAS
# =====================================================================
class Pessoa(ABC):
    """Classe ABSTRATA: define o que TODA pessoa do sistema precisa ter,
    mas não pode ser instanciada diretamente (Pessoa() dá erro)."""

    def __init__(self, nome: str, cpf: str, id: int | None = None):
        if not nome.strip():
            raise ValueError("O nome não pode ser vazio.")
        if not cpf.strip():
            raise ValueError("O CPF não pode ser vazio.")
        # Atributos com "_" = convenção de ENCAPSULAMENTO (uso interno).
        self._nome = nome.strip()
        self._cpf = cpf.strip()
        self.id = id  # o repositório preenche quando salva

    # Propriedades somente leitura: de fora você lê, mas não altera.
    @property
    def nome(self) -> str:
        return self._nome

    @property
    def cpf(self) -> str:
        return self._cpf

    # Métodos/propriedades ABSTRATOS: cada subclasse é OBRIGADA a implementar.
    @property
    @abstractmethod
    def tipo(self) -> str: ...

    @property
    @abstractmethod
    def limite_emprestimos(self) -> int: ...

    @property
    @abstractmethod
    def prazo_dias(self) -> int: ...

    def __str__(self) -> str:
        return f"[{self.tipo}] {self.nome} (CPF {self.cpf})"


class Aluno(Pessoa):
    """Aluno: poucos empréstimos e prazo curto."""
    @property
    def tipo(self) -> str:
        return "Aluno"

    @property
    def limite_emprestimos(self) -> int:
        return 3

    @property
    def prazo_dias(self) -> int:
        return 7


class Professor(Pessoa):
    """Professor: mais empréstimos e prazo maior (mesmo método, outro comportamento)."""
    @property
    def tipo(self) -> str:
        return "Professor"

    @property
    def limite_emprestimos(self) -> int:
        return 5

    @property
    def prazo_dias(self) -> int:
        return 14


# =====================================================================
# HERANÇA + POLIMORFISMO (2): hierarquia de ITENS do acervo
# =====================================================================
class Item(ABC):
    """Classe abstrata para tudo que pode ser emprestado."""

    def __init__(self, titulo: str, detalhe: str, id: int | None = None,
                 disponivel: bool = True):
        if not titulo.strip() or not detalhe.strip():
            raise ValueError("Título e detalhe (autor/edição) são obrigatórios.")
        self._titulo = titulo.strip()
        self._detalhe = detalhe.strip()   # autor (Livro) ou edição (Revista)
        self._disponivel = disponivel     # ENCAPSULADO: só muda via métodos
        self.id = id

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def detalhe(self) -> str:
        return self._detalhe

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    # Regras de negócio protegidas: ninguém seta _disponivel "no braço".
    def marcar_emprestado(self) -> None:
        if not self._disponivel:
            raise ValueError("Item já está emprestado.")
        self._disponivel = False

    def marcar_disponivel(self) -> None:
        self._disponivel = True

    @property
    @abstractmethod
    def tipo(self) -> str: ...

    @property
    @abstractmethod
    def rotulo_detalhe(self) -> str: ...

    @property
    @abstractmethod
    def multa_por_dia(self) -> float: ...

    def calcular_multa(self, dias_atraso: int) -> float:
        """Método CONCRETO que usa a propriedade ABSTRATA.
        Cada subclasse define multa_por_dia -> POLIMORFISMO."""
        return max(0, dias_atraso) * self.multa_por_dia

    def __str__(self) -> str:
        situacao = "disponível" if self._disponivel else "emprestado"
        return (f"[{self.tipo}] {self.titulo} — {self.rotulo_detalhe}: "
                f"{self.detalhe} ({situacao})")


class Livro(Item):
    @property
    def tipo(self) -> str:
        return "Livro"

    @property
    def rotulo_detalhe(self) -> str:
        return "Autor"

    @property
    def multa_por_dia(self) -> float:
        return 1.00


class Revista(Item):
    @property
    def tipo(self) -> str:
        return "Revista"

    @property
    def rotulo_detalhe(self) -> str:
        return "Edição"

    @property
    def multa_por_dia(self) -> float:
        return 0.50


# =====================================================================
# ASSOCIAÇÃO: Emprestimo "conhece" um Pessoa e um Item
# =====================================================================
class Emprestimo:
    """Liga uma pessoa a um item numa data. Pessoa e Item continuam
    existindo mesmo que o empréstimo acabe (ASSOCIAÇÃO)."""

    def __init__(self, usuario: Pessoa, item: Item, data_emprestimo: date,
                 id: int | None = None, data_devolucao: date | None = None):
        self.usuario = usuario
        self.item = item
        self.data_emprestimo = data_emprestimo
        self.data_devolucao = data_devolucao
        self.id = id
        # POLIMORFISMO em ação: prazo_dias muda conforme o tipo de pessoa.
        self.data_prevista = data_emprestimo + timedelta(days=usuario.prazo_dias)

    @property
    def ativo(self) -> bool:
        return self.data_devolucao is None

    def dias_atraso(self, referencia: date | None = None) -> int:
        ref = self.data_devolucao or referencia or date.today()
        return max(0, (ref - self.data_prevista).days)

    def devolver(self, data: date | None = None) -> float:
        """Registra a devolução e devolve o valor da multa."""
        if not self.ativo:
            raise ValueError("Este empréstimo já foi devolvido.")
        self.data_devolucao = data or date.today()
        return self.item.calcular_multa(self.dias_atraso())


# =====================================================================
# AGREGAÇÃO: Acervo TEM itens, mas os itens nascem fora dele
# =====================================================================
class Acervo:
    def __init__(self):
        self._itens: list[Item] = []

    def adicionar(self, item: Item) -> None:
        self._itens.append(item)  # o item já existia; só entra na coleção

    def todos(self) -> list[Item]:
        return list(self._itens)  # cópia: protege a lista interna

    def buscar_por_id(self, id: int) -> Item | None:
        return next((i for i in self._itens if i.id == id), None)

    def buscar(self, termo: str) -> list[Item]:
        t = termo.lower()
        return [i for i in self._itens
                if t in i.titulo.lower() or t in i.detalhe.lower()]


# =====================================================================
# DEPENDÊNCIA: Recibo só USA um Emprestimo dentro de um método
# =====================================================================
class Recibo:
    """Não guarda o empréstimo em atributo: recebe, usa e esquece."""

    @staticmethod
    def gerar(emprestimo: Emprestimo, multa: float = 0.0) -> str:
        devolucao = (emprestimo.data_devolucao.strftime("%d/%m/%Y")
                     if emprestimo.data_devolucao else "—")
        return (
            "----- RECIBO -----\n"
            f"Usuário : {emprestimo.usuario.nome} ({emprestimo.usuario.tipo})\n"
            f"Item    : {emprestimo.item.titulo}\n"
            f"Retirada: {emprestimo.data_emprestimo.strftime('%d/%m/%Y')}\n"
            f"Previsto: {emprestimo.data_prevista.strftime('%d/%m/%Y')}\n"
            f"Devolvido: {devolucao}\n"
            f"Multa   : R$ {multa:.2f}\n"
            "------------------"
        )
