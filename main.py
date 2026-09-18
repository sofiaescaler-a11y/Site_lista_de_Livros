from sys import excepthook

from flask import Flask, render_template, request, redirect,url_for,flash
import fdb
import flask
app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave_secreta_da_turma_b'

host = "localhost"
database = r"C:\Users\Aluno\Downloads\site-lais-parte-2--main (1)\site-lais-parte-2--main\BANCO_yasmin\BANCO.FDB"
user = "sysdba"
password = "sysdba"

con = fdb.connect(host=host,database=database,user=user,password=password)

@app.route("/")
def index():
    cursor = con.cursor()
    cursor.execute(""" SELECT l.ID_LIVRO 
                    ,l.NOME 
                    ,l.AUTOR 
                    ,l.ANO_PUBLICADO 
                FROM LIVRO l
""")
    livros = cursor.fetchall()
    cursor.close()
    return render_template('livros.html',livros=livros)
@app.route("/novo")
def novo():
    return render_template('novo.html')

@app.route('/criar', methods=['POST'])
def criar():
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    ano_publicado = request.form.get('ano_publicado')

    if not titulo or not autor or not ano_publicado:
        flash("Erro: Preencha todos os campos do formulário!")
        return redirect(url_for('novo'))

    cursor = con.cursor()
    try:
        cursor.execute("""SELECT 1 FROM LIVRO l WHERE nome = ?""", (titulo,))
        if cursor.fetchone():
            flash("Erro: Livro já existe no banco")
            return redirect(url_for('novo'))

        cursor.execute(""" 
            INSERT INTO LIVRO (nome, autor, ANO_PUBLICADO)
            VALUES (?, ?, ?) 
        """, (titulo, autor, ano_publicado))

        con.commit()
        flash("Livro cadastrado com sucesso!")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        con.rollback()
        return redirect(url_for('novo'))
    finally:
        cursor.close()

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
        # Se clicar no botão de confirmação dentro da página de deletar
        if request.method == 'POST':
            cursor.execute("""
                DELETE FROM LIVRO
                WHERE id_livro = ?
            """, (id,))

            con.commit()
            flash("Livro deletado com sucesso!")
            return redirect(url_for('index'))

        # Se for GET (quando clica para abrir a página deletar.html)
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

if __name__ == "__main__":
    app.run(debug=True)