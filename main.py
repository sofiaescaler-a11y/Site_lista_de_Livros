from sys import excepthook

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import fdb
from flask_bcrypt import Bcrypt
from fpdf import FPDF
import flask


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'chave_secreta_da_turma_b'

host = "localhost"
database = r"C:\Users\Aluno\Desktop\Site_lista_de_Livros-main\BANCO_yasmin\BANCO.FDB"
user = "sysdba"
password = "sysdba"

con = fdb.connect(host=host, database=database, user=user, password=password)

@app.route("/")
def index():
    # Traz todos os livros cadastrados junto com o nome da pessoa que os cadastrou
    cursor = con.cursor()
    try:
        cursor.execute("""
                       SELECT l.ID_LIVRO, l.NOME, l.AUTOR, l.ANO_PUBLICADO, p.USUARIO
                       FROM LIVRO l
                                JOIN PESSOAS p ON l.id_pessoas = p.id_pessoas
                       """)
        livros = cursor.fetchall()
    except Exception as e:
        livros = []
    finally:
        cursor.close()

    return render_template('livros.html', livros=livros)

@app.route("/novo")
def novo():
    if 'id_pessoa' not in session:
        flash('Você precisa estar logado!')
        return redirect(url_for('login'))
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
                       VALUES (?, ?, ?, ?)  RETURNING ID_LIVRO
                       """, (titulo, autor, ano_publicado, id_pessoa_atual))

        id_livro = cursor.fetchone()[0]
        con.commit()

        arquivo = request.files['imagem']
        arquivo.save(f'uploads/capa{id_livro}.jpg')

        flash("Livro cadastrado na sua lista com sucesso!")
    except Exception as e:
        flash(f"Erro ao cadastrar: {e}")
        con.rollback()
    finally:
        cursor.close()

    return redirect(url_for('index'))

@app.route("/editar/<int:id>", methods=['GET', 'POST'])
def editar(id):
    id_pessoa_atual = session.get('id_pessoa')
    if not id_pessoa_atual:
        flash("Você precisa estar logado para editar livros!")
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:
        cursor.execute("""
                       SELECT id_livro, nome, autor, ano_publicado
                       FROM LIVRO
                       WHERE id_livro = ? AND id_pessoas = ?
                       """, (id, id_pessoa_atual))

        livro = cursor.fetchone()

        if not livro:
            flash("Livro não encontrado ou você não tem permissão para editá-lo!")
            return redirect(url_for('index'))

        if request.method == 'POST':
            titulo = request.form['titulo']
            autor = request.form['autor']
            ano_publicado = request.form['ano_publicado']

            cursor.execute("""
                           UPDATE LIVRO
                           SET nome = ?, autor = ?, ano_publicado = ?
                           WHERE id_livro = ? AND id_pessoas = ?
                           """, (titulo, autor, ano_publicado, id, id_pessoa_atual))

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
    id_pessoa_atual = session.get('id_pessoa')
    if not id_pessoa_atual:
        flash("Você precisa estar logado para deletar livros!")
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:
        cursor.execute("""
                       SELECT id_livro, nome, autor, ano_publicado
                       FROM LIVRO
                       WHERE id_livro = ? AND id_pessoas = ?
                       """, (id, id_pessoa_atual))
        livro = cursor.fetchone()

        if not livro:
            flash("Livro não encontrado ou você não tem permissão para deletá-lo!")
            return redirect(url_for('index'))

        if request.method == 'POST':
            cursor.execute("""
                           DELETE FROM LIVRO
                           WHERE id_livro = ? AND id_pessoas = ?
                           """, (id, id_pessoa_atual))

            con.commit()
            flash("Livro deletado com sucesso!")
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
        novo_usuario = request.form.get('usuario')
        email = request.form.get('email')
        nova_senha = request.form.get('senha')

        if not novo_usuario or not email or not nova_senha:
            flash("Preencha todos os campos para cadastrar!", "error")
            return redirect(url_for('criar_cadastro'))

        cursor = con.cursor()
        try:
            cursor.execute("SELECT id_pessoas FROM PESSOAS WHERE email = ?", (email,))
            conta_existente = cursor.fetchone()

            if conta_existente:
                flash("Este e-mail já está cadastrado! Faça o login.", "info")
                return redirect(url_for('login'))

            senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')

            cursor.execute("""
                           INSERT INTO PESSOAS (usuario, email, senha)
                           VALUES (?, ?, ?)
                           """, (novo_usuario, email, senha_hash))

            con.commit()
            flash("Conta criada com sucesso! Faça o login para continuar.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Erro ao criar conta: {e}", "error")
            con.rollback()
        finally:
            cursor.close()

    return render_template('criar_cadastro.html')

@app.route('/continuar_tentando')
def continuar_tentando():
    session['tentativas_erro'] = 0
    return redirect(url_for('login'))
@app.route('/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_digitado = request.form.get('email')
        senha = request.form.get('senha')

        cursor = con.cursor()
        try:
            # Buscamos também o status de bloqueio e as tentativas da pessoa
            cursor.execute("""
                           SELECT id_pessoas, usuario, senha, BLOQUEADO, TENTATIVAS_ERRO
                           FROM PESSOAS
                           WHERE email = ?
                           """, (email_digitado,))

            resultado = cursor.fetchone()

            if resultado:
                id_pessoa = resultado[0]
                nome_usuario = resultado[1]
                senha_hash_banco = resultado[2]
                bloqueado = resultado[3]
                tentativas = resultado[4] or 0

                # 1. Se a conta já estiver bloqueada, barra na hora
                if bloqueado == 'SIM':
                    return render_template('bloqueio_senha.html')

                if isinstance(senha_hash_banco, str):
                    senha_hash_banco = senha_hash_banco.encode('utf-8')

                # 2. Verifica se a senha está correta
                if bcrypt.check_password_hash(senha_hash_banco, senha):
                    # Acertou: zera as tentativas de erro e entra
                    cursor.execute("UPDATE PESSOAS SET TENTATIVAS_ERRO = 0 WHERE id_pessoas = ?", (id_pessoa,))
                    con.commit()

                    session['id_pessoa'] = id_pessoa
                    session['usuario'] = nome_usuario

                    flash("Login realizado com sucesso!", "success")
                    return redirect(url_for('index'))
                else:
                    # 3. Errou a senha: soma 1 nas tentativas do banco
                    tentativas += 1

                    if tentativas >= 3:
                        # Bloqueia de vez no banco!
                        cursor.execute("UPDATE PESSOAS SET BLOQUEADO = 'SIM', TENTATIVAS_ERRO = ? WHERE id_pessoas = ?", (tentativas, id_pessoa))
                        con.commit()
                        return render_template('bloqueio_senha.html')
                    else:
                        # Apenas atualiza o contador de erros
                        cursor.execute("UPDATE PESSOAS SET TENTATIVAS_ERRO = ? WHERE id_pessoas = ?", (tentativas, id_pessoa))
                        con.commit()
                        flash(f"E-mail ou senha incorretos! Tentativa {tentativas} de 3.", "error")
                        return redirect(url_for('login'))
            else:
                flash("Erro: E-mail não encontrado!", "error")
                return redirect(url_for('login'))
        finally:
            cursor.close()

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('id_pessoa', None)
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for('login'))

@app.route('/livro/relatorio', methods=['GET'])
def relatorio():
    cursor = con.cursor()

    try:
        # Traz todos os livros e o nome do usuário responsável no relatório também
        cursor.execute("""
                       SELECT l.ID_LIVRO, l.NOME, l.AUTOR, l.ANO_PUBLICADO, p.USUARIO
                       FROM LIVRO l
                                JOIN PESSOAS p ON l.id_pessoas = p.id_pessoas
                       """)
        livros = cursor.fetchall()
    except Exception as e:
        flash(f"Erro ao gerar relatório: {e}")
        return redirect(url_for('index'))
    finally:
        cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatório Geral de Livros", ln=True, align='C')

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Arial", size=11)

    for livro in livros:
        pdf.cell(
            200,
            10,
            f"ID: {livro[0]} | Livro: {livro[1]} | Autor: {livro[2]} | Ano: {livro[3]} | Cadastrado por: {livro[4]}",
            ln=True
        )

    contador_livros = len(livros)

    pdf.ln(10)

    pdf.set_font("Arial", style='B', size=12)

    pdf.cell(
        200,
        10,
        f"Total de livros cadastrados: {contador_livros}",
        ln=True,
        align='C'
    )

    pdf_path = "relatorio_livros.pdf"
    pdf.output(pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(debug=True)