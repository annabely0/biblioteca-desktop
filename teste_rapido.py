"""Teste automático das regras (rode: python teste_rapido.py)."""
import os, tempfile
from datetime import date, timedelta
from modelos import Livro, Revista, Aluno, Professor
from repositorio import RepositorioMemoria, RepositorioSQLite
from biblioteca import Biblioteca, BibliotecaErro


def cenario(bib):
    livro = bib.cadastrar_item(Livro("Dom Casmurro", "Machado"))
    rev = bib.cadastrar_item(Revista("Super", "450"))
    ana = bib.cadastrar_usuario(Aluno("Ana", "1"))
    prof = bib.cadastrar_usuario(Professor("Carlos", "2"))
    # polimorfismo: prazos diferentes
    e1 = bib.emprestar(ana.id, livro.id, hoje=date(2026, 1, 1))
    e2 = bib.emprestar(prof.id, rev.id, hoje=date(2026, 1, 1))
    assert (e1.data_prevista - e1.data_emprestimo).days == 7
    assert (e2.data_prevista - e2.data_emprestimo).days == 14
    # item indisponível
    try: bib.emprestar(prof.id, livro.id); assert False
    except BibliotecaErro: pass
    # multa: aluno atrasa 3 dias com livro (R$1/dia) = 3.00
    _, multa = bib.devolver(e1.id, hoje=date(2026, 1, 11))
    assert multa == 3.0, multa
    # revista: atraso 4 dias (R$0,50) = 2.00
    _, multa = bib.devolver(e2.id, hoje=date(2026, 1, 19))
    assert multa == 2.0, multa
    # limite do aluno = 3
    for n in range(3):
        bib.cadastrar_item(Livro(f"L{n}", "x"))
    ids = [i.id for i in bib.listar_itens() if i.disponivel]
    for i in ids[:3]:
        bib.emprestar(ana.id, i)
    try: bib.emprestar(ana.id, ids[3]); assert False
    except BibliotecaErro: pass
    # CPF duplicado
    try: bib.cadastrar_usuario(Aluno("Outra", "1")); assert False
    except BibliotecaErro: pass


cenario(Biblioteca("T", RepositorioMemoria()))
print("Memória OK")

caminho = os.path.join(tempfile.mkdtemp(), "t.db")
repo = RepositorioSQLite(caminho)
cenario(Biblioteca("T", repo)); repo.fechar()
# reabre: dados persistiram?
b2 = Biblioteca("T", RepositorioSQLite(caminho))
assert len(b2.listar_itens()) == 5 and len(b2.listar_usuarios()) == 2
assert len(b2.emprestimos_ativos()) == 3
print("SQLite OK (persistência confirmada)")
