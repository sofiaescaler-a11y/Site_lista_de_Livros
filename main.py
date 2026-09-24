from sys import excepthook

from flask import Flask, render_template, request, redirect,url_for,flash, session
import fdb
import flask
app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave_secreta_da_turma_b'

host = "localhost"
database = r"C:\Users\Aluno\Desktop\Site_lista_de_Livros-main\BANCO_yasmin\BANCO.FDB"
user = "sysdba"
password = "sysdba"

con = fdb.connect(host=host,database=database,user=user,password=password)
@app.route("/")
def index():
    id_pessoa_atual = session.get('id_pessoa')

    if not id_pessoa_atual:
        livros = []
    else:

        cursor = con.cursor()
        cursor.execute("""
                       SELECT ID_LIVRO, NOME, AUTOR, ANO_PUBLICADO
                       FROM LIVRO
                       WHERE id_pessoas = ?
                       """, (id_pessoa_atual,))

        livros = cursor.fetchall()
        cursor.close()

    return render_template('livros.html', livros=livros)
@app.route("/novo")
def novo():
    return render_template('novo.html')

@app.route('/criar', methods=['POST'])
def criar():
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    ano_publicado = request.form.get('ano_publicado')


    id_pessoa_atual = session.get('id_pessoa')

    if not id_pessoa_atual:
        flash("Você precisa estar logado para cadastrar um livro!")
        return redirect(url_for('login'))

    cursor = con.cursor()
    try:

        cursor.execute("""
                       INSERT INTO LIVRO (nome, autor, ANO_PUBLICADO, id_pessoas)
                       VALUES (?, ?, ?, ?)
                       """, (titulo, autor, ano_publicado, id_pessoa_atual))
        con.commit()
        flash("Livro cadastrado na sua lista com sucesso!")
    except Exception as e:
        flash(f"Erro ao cadastrar: {e}")
        con.rollback()
    finally:
        cursor.close()

    return redirect(url_for('index'))

@app.route("/editar/<int:id>", methods=['GET', 'POST'])
def editar(id):
    cursor = con.cursor()

    try:
        cursor.execute("""
            SELECT id_livro, nome, autor, ano_publicado
            FROM LIVRO
            WHERE id_livro = ?
        """, (id,))

        livro = cursor.fetchone()

        if not livro:
            flash("Livro não encontrado")
            return redirect(url_for('index'))

        if request.method == 'POST':
            titulo = request.form['titulo']
            autor = request.form['autor']
            ano_publicado = request.form['ano_publicado']

            cursor.execute("""
                UPDATE LIVRO
                SET nome = ?, autor = ?, ano_publicado = ?
                WHERE id_livro = ?
            """, (titulo, autor, ano_publicado, id))

            con.commit()

            flash("Livro editado com sucesso!")
            return redirect(url_for('index'))

        return render_template("editar.html", livro=livro)

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for('index'))

    finally:
        cursor.close()

@app.route("/deletar/<int:id>", methods=['GET', 'POST'])
def deletar(id):
    cursor = con.cursor()

    try:

        if request.method == 'POST':
            cursor.execute("""
                DELETE FROM LIVRO
                WHERE id_livro = ?
            """, (id,))

            con.commit()
            flash("Livro deletado com sucesso!")
            return redirect(url_for('index'))


        cursor.execute("""
            SELECT id_livro, nome, autor, ano_publicado
            FROM LIVRO
            WHERE id_livro = ?
        """, (id,))
        livro = cursor.fetchone()

        if not livro:
            flash("Livro não encontrado")
            return redirect(url_for('index'))

        return render_template("deletar.html", livro=livro)

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for('index'))

    finally:
        cursor.close()


@app.route('/cadastro')
def criar_cadastro():
    return render_template('criar_cadastro.html')


@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        email = request.form.get('email')
        senha = request.form.get('senha')

        print(f"Recebido: {usuario}, {email}")
        flash("Conta criada com sucesso!")
        return redirect(url_for('index'))

    return render_template('criar_cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        cursor = con.cursor()
        try:
            cursor.execute("""
                           SELECT id_pessoas, usuario FROM PESSOAS
                           WHERE usuario = ? AND senha = ?
                           """, (usuario, senha))

            resultado = cursor.fetchone()

            if resultado:

                session['id_pessoa'] = resultado[0]
                session['usuario'] = resultado[1]

                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('index'))
            else:
                flash("Erro: Usuário ou senha incorretos!", "error")
                return redirect(url_for('login'))
        finally:
            cursor.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)