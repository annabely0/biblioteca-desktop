"""
app_gui.py — Interface GRÁFICA com Tkinter (Nível 4).
Rode com:  python app_gui.py      (usa o banco biblioteca.db)
No Linux, se faltar o tkinter:  sudo apt install python3-tk
"""
import tkinter as tk
from tkinter import ttk, messagebox

from modelos import Livro, Revista, Aluno, Professor, Recibo
from repositorio import RepositorioSQLite
from biblioteca import Biblioteca, BibliotecaErro

# Paleta de cores personalizada (estilo próprio exigido no Nível 4)
FUNDO, PRIMARIA, DESTAQUE, TEXTO = "#f4f1ea", "#2f5d50", "#d98e04", "#22312c"


class FormularioDialogo(tk.Toplevel):
    """Janela reutilizável: recebe os campos e uma função 'ao_salvar'."""

    def __init__(self, pai, titulo, campos, ao_salvar):
        super().__init__(pai)
        self.title(titulo)
        self.configure(bg=FUNDO, padx=20, pady=15)
        self.resizable(False, False)
        self.transient(pai)       # fica "presa" à janela principal
        self.grab_set()           # bloqueia a janela de trás (modal)
        self._ao_salvar = ao_salvar
        self._widgets = []
        for linha, (rotulo, opcoes) in enumerate(campos):
            ttk.Label(self, text=rotulo).grid(row=linha, column=0, sticky="w", pady=5)
            if opcoes:  # lista de opções -> caixa de seleção
                w = ttk.Combobox(self, values=opcoes, state="readonly", width=32)
                w.current(0)
            else:       # sem opções -> campo de texto
                w = ttk.Entry(self, width=35)
            w.grid(row=linha, column=1, padx=(10, 0), pady=5)
            self._widgets.append(w)
        ttk.Button(self, text="Salvar", style="Primary.TButton",
                   command=self._salvar).grid(row=len(campos), column=0,
                                              columnspan=2, pady=(12, 0))

    def _salvar(self):
        try:
            self._ao_salvar([w.get() for w in self._widgets])
            self.destroy()
        except (BibliotecaErro, ValueError) as erro:
            messagebox.showerror("Erro", str(erro), parent=self)


class AppGUI(tk.Tk):
    def __init__(self, biblioteca: Biblioteca):
        super().__init__()
        self.bib = biblioteca
        self.title(f"{biblioteca.nome} — POO em Python")
        self.geometry("920x540")
        self.configure(bg=FUNDO)
        self._configurar_estilos()
        self._montar_interface()
        self.atualizar()

    def _configurar_estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=FUNDO)
        s.configure("TLabel", background=FUNDO, foreground=TEXTO, font=("Segoe UI", 10))
        s.configure("Titulo.TLabel", font=("Georgia", 20, "bold"), foreground=PRIMARIA)
        s.configure("Primary.TButton", background=PRIMARIA, foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=8, borderwidth=0)
        s.map("Primary.TButton", background=[("active", "#3f7a69")])
        s.configure("Destaque.TButton", background=DESTAQUE, foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=8, borderwidth=0)
        s.map("Destaque.TButton", background=[("active", "#b87700")])
        s.configure("Treeview", rowheight=28, font=("Segoe UI", 10),
                    background="white", fieldbackground="white")
        s.configure("Treeview.Heading", background=PRIMARIA, foreground="white",
                    font=("Segoe UI", 10, "bold"))
        s.configure("TNotebook", background=FUNDO)
        s.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10, "bold"))

    def _montar_interface(self):
        ttk.Label(self, text="📚 " + self.bib.nome, style="Titulo.TLabel").pack(
            anchor="w", padx=20, pady=(15, 5))

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=20, pady=8)
        botoes = [("+ Item", self.novo_item, "Primary.TButton"),
                  ("+ Usuário", self.novo_usuario, "Primary.TButton"),
                  ("Emprestar", self.emprestar, "Primary.TButton"),
                  ("Devolver selecionado", self.devolver, "Destaque.TButton")]
        for texto, comando, estilo in botoes:
            ttk.Button(barra, text=texto, command=comando, style=estilo).pack(
                side="left", padx=(0, 8))

        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.t_itens = self._criar_tabela(abas, "Acervo",
                                          ("ID", "Tipo", "Título", "Detalhe", "Situação"))
        self.t_usuarios = self._criar_tabela(abas, "Usuários",
                                             ("ID", "Tipo", "Nome", "CPF", "Limite"))
        self.t_emprestimos = self._criar_tabela(
            abas, "Empréstimos",
            ("ID", "Usuário", "Item", "Retirada", "Previsto", "Situação"))

    def _criar_tabela(self, abas, titulo, colunas):
        quadro = ttk.Frame(abas)
        abas.add(quadro, text=titulo)
        tabela = ttk.Treeview(quadro, columns=colunas, show="headings")
        for c in colunas:
            tabela.heading(c, text=c)
            tabela.column(c, width=60 if c in ("ID", "Limite") else 150)
        barra = ttk.Scrollbar(quadro, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabela

    # ---------- atualiza as três tabelas a partir da Biblioteca ----------
    def atualizar(self):
        for t in (self.t_itens, self.t_usuarios, self.t_emprestimos):
            t.delete(*t.get_children())
        for i in self.bib.listar_itens():
            self.t_itens.insert("", "end", values=(
                i.id, i.tipo, i.titulo, i.detalhe,
                "Disponível" if i.disponivel else "Emprestado"))
        for u in self.bib.listar_usuarios():
            self.t_usuarios.insert("", "end", values=(
                u.id, u.tipo, u.nome, u.cpf, u.limite_emprestimos))
        for e in self.bib.listar_emprestimos():
            situacao = "Ativo" if e.ativo else f"Devolvido {e.data_devolucao:%d/%m/%Y}"
            self.t_emprestimos.insert("", "end", values=(
                e.id, e.usuario.nome, e.item.titulo,
                f"{e.data_emprestimo:%d/%m/%Y}", f"{e.data_prevista:%d/%m/%Y}", situacao))

    # ---------- botões ----------
    def novo_item(self):
        def salvar(v):
            tipo, titulo, detalhe = v
            classe = {"Livro": Livro, "Revista": Revista}[tipo]
            self.bib.cadastrar_item(classe(titulo, detalhe))
            self.atualizar()
        FormularioDialogo(self, "Novo item",
                          [("Tipo", ["Livro", "Revista"]), ("Título", None),
                           ("Autor (livro) ou Edição (revista)", None)], salvar)

    def novo_usuario(self):
        def salvar(v):
            tipo, nome, cpf = v
            classe = {"Aluno": Aluno, "Professor": Professor}[tipo]
            self.bib.cadastrar_usuario(classe(nome, cpf))
            self.atualizar()
        FormularioDialogo(self, "Novo usuário",
                          [("Tipo", ["Aluno", "Professor"]), ("Nome", None),
                           ("CPF", None)], salvar)

    def emprestar(self):
        usuarios = [f"{u.id} - {u.nome}" for u in self.bib.listar_usuarios()]
        itens = [f"{i.id} - {i.titulo}" for i in self.bib.listar_itens() if i.disponivel]
        if not usuarios or not itens:
            messagebox.showwarning("Atenção", "Cadastre usuários e tenha itens disponíveis.")
            return

        def salvar(v):
            emp = self.bib.emprestar(int(v[0].split(" - ")[0]), int(v[1].split(" - ")[0]))
            self.atualizar()
            messagebox.showinfo("Empréstimo feito",
                                f"Devolver até {emp.data_prevista:%d/%m/%Y}.")
        FormularioDialogo(self, "Novo empréstimo",
                          [("Usuário", usuarios), ("Item", itens)], salvar)

    def devolver(self):
        selecao = self.t_emprestimos.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um empréstimo na aba Empréstimos.")
            return
        id_emp = int(self.t_emprestimos.item(selecao[0])["values"][0])
        try:
            emp, multa = self.bib.devolver(id_emp)
        except BibliotecaErro as erro:
            messagebox.showerror("Erro", str(erro))
            return
        self.atualizar()
        messagebox.showinfo("Devolução", Recibo.gerar(emp, multa))


if __name__ == "__main__":
    AppGUI(Biblioteca("Biblioteca Central", RepositorioSQLite("biblioteca.db"))).mainloop()
