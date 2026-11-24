"""
repositorio.py — Camada de PERSISTÊNCIA.

Duas implementações da mesma "interface" (Repositorio):
 - RepositorioMemoria  -> Nível 2 (sem banco)
 - RepositorioSQLite   -> Níveis 3 e 4 (banco de dados de verdade)
A Biblioteca não sabe qual está usando: isso é POLIMORFISMO.
"""
import sqlite3
from abc import ABC, abstractmethod
from datetime import date

from modelos import Livro, Revista, Aluno, Professor, Emprestimo

# "Fábricas": transformam o texto salvo no banco de volta em objeto.
TIPOS_ITEM = {"Livro": Livro, "Revista": Revista}
TIPOS_USUARIO = {"Aluno": Aluno, "Professor": Professor}


class Repositorio(ABC):
    @abstractmethod
    def salvar_item(self, item): ...
    @abstractmethod
    def salvar_usuario(self, usuario): ...
    @abstractmethod
    def salvar_emprestimo(self, emprestimo): ...
    @abstractmethod
    def carregar_itens(self): ...
    @abstractmethod
    def carregar_usuarios(self): ...
    @abstractmethod
    def carregar_emprestimos(self, itens_por_id, usuarios_por_id): ...


class RepositorioMemoria(Repositorio):
    """Não guarda nada: os dados vivem só na RAM, dentro da Biblioteca.
    Ao fechar o programa, tudo se perde (como o Nível 2 permite)."""

    def __init__(self):
        self._contadores = {"item": 1, "usuario": 1, "emprestimo": 1}

    def _gerar_id(self, objeto, chave):
        if objeto.id is None:
            objeto.id = self._contadores[chave]
            self._contadores[chave] += 1

    def salvar_item(self, item):
        self._gerar_id(item, "item")

    def salvar_usuario(self, usuario):
        self._gerar_id(usuario, "usuario")

    def salvar_emprestimo(self, emprestimo):
        self._gerar_id(emprestimo, "emprestimo")

    def carregar_itens(self):
        return []

    def carregar_usuarios(self):
        return []

    def carregar_emprestimos(self, itens_por_id, usuarios_por_id):
        return []


class RepositorioSQLite(Repositorio):
    def __init__(self, caminho: str = "biblioteca.db"):
        self._conn = sqlite3.connect(caminho)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._criar_tabelas()

    def _criar_tabelas(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                detalhe TEXT NOT NULL,
                disponivel INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                nome TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                item_id INTEGER NOT NULL REFERENCES itens(id),
                data_emprestimo TEXT NOT NULL,
                data_devolucao TEXT
            );
        """)
        self._conn.commit()

    # ---------- escrita (INSERT se id é None, senão UPDATE) ----------
    def salvar_item(self, item):
        if item.id is None:
            cur = self._conn.execute(
                "INSERT INTO itens (tipo, titulo, detalhe, disponivel) VALUES (?,?,?,?)",
                (item.tipo, item.titulo, item.detalhe, int(item.disponivel)))
            item.id = cur.lastrowid
        else:
            self._conn.execute("UPDATE itens SET disponivel=? WHERE id=?",
                               (int(item.disponivel), item.id))
        self._conn.commit()

    def salvar_usuario(self, usuario):
        if usuario.id is None:
            cur = self._conn.execute(
                "INSERT INTO usuarios (tipo, nome, cpf) VALUES (?,?,?)",
                (usuario.tipo, usuario.nome, usuario.cpf))
            usuario.id = cur.lastrowid
            self._conn.commit()

    def salvar_emprestimo(self, emp):
        if emp.id is None:
            cur = self._conn.execute(
                "INSERT INTO emprestimos (usuario_id, item_id, data_emprestimo) VALUES (?,?,?)",
                (emp.usuario.id, emp.item.id, emp.data_emprestimo.isoformat()))
            emp.id = cur.lastrowid
        else:
            dev = emp.data_devolucao.isoformat() if emp.data_devolucao else None
            self._conn.execute("UPDATE emprestimos SET data_devolucao=? WHERE id=?",
                               (dev, emp.id))
        self._conn.commit()

    # ---------- leitura ----------
    def carregar_itens(self):
        linhas = self._conn.execute(
            "SELECT id, tipo, titulo, detalhe, disponivel FROM itens ORDER BY id")
        return [TIPOS_ITEM[tipo](titulo, detalhe, id=id_, disponivel=bool(disp))
                for id_, tipo, titulo, detalhe, disp in linhas]

    def carregar_usuarios(self):
        linhas = self._conn.execute("SELECT id, tipo, nome, cpf FROM usuarios ORDER BY id")
        return [TIPOS_USUARIO[tipo](nome, cpf, id=id_) for id_, tipo, nome, cpf in linhas]

    def carregar_emprestimos(self, itens_por_id, usuarios_por_id):
        linhas = self._conn.execute(
            "SELECT id, usuario_id, item_id, data_emprestimo, data_devolucao "
            "FROM emprestimos ORDER BY id")
        resultado = []
        for id_, uid, iid, d_emp, d_dev in linhas:
            resultado.append(Emprestimo(
                usuarios_por_id[uid], itens_por_id[iid],
                date.fromisoformat(d_emp), id=id_,
                data_devolucao=date.fromisoformat(d_dev) if d_dev else None))
        return resultado

    def fechar(self):
        self._conn.close()
