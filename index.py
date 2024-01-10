from flask import Flask, render_template, redirect, url_for, request
import mysql.connector
import re

db = mysql.connector.connect(
    host='mysql01.cgkdrobnydiy.us-east-1.rds.amazonaws.com',
    user='aluno_fatec',
    password='aluno_fatec',
    database='meu_banco'
)

mycursor = db.cursor()

app = Flask(__name__)

########################################## Validação de CPF ##########################################


def valida_cpf(cpf):
    cpf = re.sub('[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == '00000000000' or cpf == '11111111111' or cpf == '22222222222' or cpf == '33333333333' or cpf == '44444444444' or cpf == '55555555555' or cpf == '66666666666' or cpf == '77777777777' or cpf == '88888888888' or cpf == '99999999999':
        return False
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[9]):
        return False
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[10]):
        return False
    return True

########################################## Rota Principal ##########################################


@app.route('/')
def principal():
    return render_template('principal.html')

########################################## Rota Login ##########################################


@app.route('/login')
def login():
    return render_template('login.html')

########################################## Login Aluno ##########################################


@app.route('/loginAluno', methods=['POST'])
def login_aluno():
    cpf = request.form['cpf']
    senha = request.form['senha1']

    # Busca na coluna cpf e senha se existe o valor passado pelo usuario
    query = 'SELECT * FROM leoP_aluno WHERE cpf = %s and senha = %s'
    mycursor.execute(query, (cpf, senha))

    # Armazenando em uma variavel o resultado da query
    aluno = mycursor.fetchone()

    if aluno is None:
        return render_template('login.html')

    # Buscas pelas notas do aluno em todas as materias através de um IDAluno fazendo uma relação entre tabelas
    query = ("SELECT m.nomeMateria, n.nota1, n.nota2, n.nota3, n.nota4 FROM leoP_nota n "
             "INNER JOIN leoP_materia m ON n.id_Materia = m.idMateria "
             "WHERE n.id_Aluno = %s ")

    # Executa a query
    mycursor.execute(query, (aluno[0],))

    # Armazenando em uma variavel o resultado da query
    materia = mycursor.fetchall()

    # Renderiza a página
    return render_template('homeAluno.html', aluno=aluno, materias=materia)

########################################## Login Funcionário ##########################################


@app.route('/loginSecretario', methods=['POST'])
def login_secretario():
    login = request.form['loginAcademico']
    senha = request.form['senha']

    # Busca na coluna cpf e senha se existe o valor passado pelo usuario
    query = 'SELECT * FROM leoP_funcionario WHERE login = %s and senha = %s'
    mycursor.execute(query, (login, senha,))

    # Armazenando em uma variavel o resultado da query
    funcionario = mycursor.fetchone()

    if funcionario is not None:
        return render_template('homeSecretaria.html', funcionario=funcionario)

    return render_template('login.html')

########################################## Cadastro/Exclusão/Update de Aluno ##########################################


@app.route('/cadastroAluno', methods=['GET', 'POST'])
def cadastro_aluno():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']

        # Valida o CPF antes de armazenar
        if not valida_cpf(cpf):
            message = "CPF Inválido"
            return render_template('cadastroAluno.html', message=message)

        # Formata o CPF no formato correto(xxx.xxx.xxx-xx)
        cpf_formatado = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

        # Verifica se o aluno já existe no banco
        query_verificacao = "SELECT * FROM leoP_aluno WHERE cpf = %s"
        mycursor.execute(query_verificacao, (cpf_formatado,))
        aluno_existente = mycursor.fetchone()

        if aluno_existente:
            message = "Este CPF já está vinculado a um aluno."
            return render_template('cadastroAluno.html', message=message)

        # Query para realizar o INSERT no banco de dados
        query = "INSERT INTO leoP_aluno (nome, cpf, senha) VALUES (%s, %s, %s)"
        mycursor.execute(query, (nome, cpf_formatado, senha,))
        db.commit()

        return redirect(url_for('cadastro_aluno'))

    if request.method == 'GET':
        query = ("SELECT * from leoP_aluno")
        mycursor.execute(query)
        aluno = mycursor.fetchall()

        return render_template('cadastroAluno.html', alunos=aluno)

    return render_template('cadastroAluno.html')


@app.route('/cadastrarAluno')
def cadastrarAluno():
    return render_template('cadastrarAluno.html')


@app.route('/excluirAluno/<int:id>', methods=['GET'])
def excluirAluno(id):
    query_verificacao = "SELECT COUNT(*) FROM leoP_nota WHERE id_Aluno = %s"
    mycursor.execute(query_verificacao, (id,))
    count_alunos = mycursor.fetchone()[0]

    if count_alunos > 0:
        messagem = "Não é possível excluir este(a) Aluno(a), pois está associada a uma matéria."
        return render_template('cadastroAluno.html', messagem=messagem)

    query = "DELETE FROM leoP_aluno WHERE idAluno = %s"
    mycursor.execute(query, (id,))
    db.commit()

    return redirect(url_for('cadastro_aluno'))


@app.route('/updateAluno/<int:id>', methods=['GET'])
def updateAluno(id):
    query = "SELECT * FROM leoP_aluno WHERE idAluno = %s"
    mycursor.execute(query, (id,))
    aluno = mycursor.fetchone()

    return render_template('updateAluno.html', aluno=aluno)


@app.route('/updateAluno', methods=['POST'])
def update_aluno():
    if request.method == 'POST':
        id = request.form['id']
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']

        # Valida o CPF antes de armazenar
        if not valida_cpf(cpf):
            message = "CPF Inválido"
            return render_template('cadastroAluno.html', message=message)

        # Verifica se o CPF já está formatado
        if '-' not in cpf:
            # Se não estiver formatado, formata
            cpf_formatado = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        else:
            # Se já estiver formatado, apenas use o CPF fornecido
            cpf_formatado = cpf

        query = "UPDATE leoP_aluno SET nome = %s, cpf = %s, senha = %s WHERE idAluno = %s"
        mycursor.execute(query, (nome, cpf_formatado, senha, id,))
        db.commit()

        return redirect(url_for('cadastro_aluno'))

    return render_template('updateAluno.html')

########################################## Cadastro/Exclusão/Update de Funcionário ##########################################


@app.route('/cadastroFuncionario', methods=['GET', 'POST'])
def cadastro_funcionario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        login = request.form['login']
        senha = request.form['senha']

        # Valida o CPF antes de armazenar
        if not valida_cpf(cpf):
            message = "CPF Inválido"
            return render_template('cadastroAluno.html', message=message)

        # Formata o CPF no formato desejado
        cpf_formatado = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

        # Verifica se o funcionário já existe no banco
        query_verificacao = "SELECT * FROM leoP_funcionario WHERE cpf = %s"
        mycursor.execute(query_verificacao, (cpf_formatado,))
        funcionario_existente = mycursor.fetchone()

        if funcionario_existente:
            message = "Este CPF já está vinculado a um funcionário."
            return render_template('cadastroFuncionario.html', message=message)

        # Realiza o INSERT no banco de dados
        query = "INSERT INTO leoP_funcionario (nome, email, cpf, login, senha) VALUES (%s, %s, %s, %s, %s)"
        mycursor.execute(query, (nome, email, cpf_formatado, login, senha,))

        db.commit()

        return redirect(url_for('cadastro_funcionario'))

    if request.method == 'GET':

        query = ("SELECT * from leoP_funcionario")

        mycursor.execute(query)

        funcionario = mycursor.fetchall()

        return render_template('cadastroFuncionario.html', funcionarios=funcionario)

    return render_template('cadastroFuncionario.html')


@app.route('/cadastrarFuncionario')
def cadastrarFuncionario():
    return render_template('cadastrarFuncionario.html')


@app.route('/excluirFuncionario/<int:id>', methods=['GET'])
def excluirFuncionario(id):
    query = "DELETE FROM leoP_funcionario WHERE idFuncionario = %s"
    mycursor.execute(query, (id,))
    db.commit()

    return redirect(url_for('cadastro_funcionario'))


@app.route('/updateFuncionario/<int:id>', methods=['GET'])
def updateFuncionario(id):
    query = "SELECT * FROM leoP_funcionario WHERE idFuncionario = %s"
    mycursor.execute(query, (id,))
    funcionario = mycursor.fetchone()

    return render_template('updateFuncionario.html', funcionario=funcionario)


@app.route('/updateFuncionario', methods=['POST'])
def update_funcionario():
    if request.method == 'POST':
        id = request.form['id']
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        usuario = request.form['login']
        senha = request.form['senha']

        # Valida o CPF antes de armazenar
        if not valida_cpf(cpf):
            message = "CPF Inválido"
            return render_template('cadastroFuncionario.html', message=message)

        # Verifica se o CPF já está formatado
        if '-' not in cpf:
            # Se não estiver formatado, formata
            cpf_formatado = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        else:
            # Se já estiver formatado, apenas use o CPF fornecido
            cpf_formatado = cpf

        query = "UPDATE leoP_funcionario SET nome = %s, email = %s, cpf = %s, login = %s, senha = %s WHERE idFuncionario = %s"
        mycursor.execute(
            query, (nome, email, cpf_formatado, usuario, senha, id,))
        db.commit()

        return redirect(url_for('cadastro_funcionario'))

    return render_template('updateFuncionario.html')

########################################## Cadastro/Exclusão/Update de Matéria ##########################################


@app.route('/cadastroMateria', methods=['GET', 'POST'])
def cadastro_materia():
    if request.method == 'POST':
        materia = request.form['materia']

        query_check = "SELECT * FROM leoP_materia WHERE nomeMateria = %s"
        mycursor.execute(query_check, (materia,))
        existe = mycursor.fetchone()

        if existe:
            mensagem = "Esta matéria ja foi cadastrada"
            return render_template("cadastroMateria.html", mensagem=mensagem)
        else:
            # Realiza o INSERT no banco de dados
            query = "INSERT INTO leoP_materia (nomeMateria) VALUES (%s)"
            mycursor.execute(query, (materia,))
            db.commit()

            return redirect(url_for('cadastro_materia'))

    if request.method == 'GET':

        query = ("SELECT * from leoP_materia")

        mycursor.execute(query)

        materia = mycursor.fetchall()

        return render_template('cadastroMateria.html', materias=materia)

    return render_template('cadastroMateria.html')


@app.route('/cadastrarMateria')
def cadastrarMateria():
    return render_template('cadastrarMateria.html')


@app.route('/excluirMateria/<int:id>', methods=['GET'])
def excluirMateria(id):

    query_verificacao = "SELECT COUNT(*) FROM leoP_nota WHERE id_Materia = %s"
    mycursor.execute(query_verificacao, (id,))
    count_alunos = mycursor.fetchone()[0]

    if count_alunos > 0:
        message = "Não é possível excluir esta matéria, pois está associada a pelo menos um aluno."
        return render_template('cadastroMateria.html', message=message)

    query_exclusao = "DELETE FROM leoP_materia WHERE idMateria = %s"
    mycursor.execute(query_exclusao, (id,))

    db.commit()

    return redirect(url_for('cadastro_materia'))


@app.route('/updateMateria/<int:id>', methods=['GET'])
def updateMateria(id):
    query = "SELECT * FROM leoP_materia WHERE idMateria = %s"
    mycursor.execute(query, (id,))
    materia = mycursor.fetchone()

    return render_template('updateMateria.html', materia=materia)


@app.route('/updateMateria', methods=['POST'])
def update_materia():
    if request.method == 'POST':
        id = request.form['id']
        materia = request.form['materia']

        query = "UPDATE leoP_materia SET nomeMateria = %s WHERE idMateria = %s"
        mycursor.execute(query, (materia, id,))
        db.commit()

        return redirect(url_for('cadastro_materia'))

    return render_template('updateMateria.html')

########################################## Cadastro/Exclusão/Update de Nota ##########################################


@app.route('/cadastroNota', methods=['GET', 'POST'])
def cadastro_nota():
    if request.method == 'POST':
        idAluno = request.form.get('nome')
        idMateria = request.form.get('materia')
        nota1 = float(request.form['nota1'].replace(',', '.'))
        nota2 = float(request.form['nota2'].replace(',', '.'))
        nota3 = float(request.form['nota3'].replace(',', '.'))
        nota4 = float(request.form['nota4'].replace(',', '.'))

        # Validar as notas
        if not (0 <= nota1 <= 10) or not (0 <= nota2 <= 10) or not (0 <= nota3 <= 10) or not (0 <= nota4 <= 10):
            message = "Apenas notas de 0 a 10 são válidas!"
            return render_template('cadastroNota.html', message=message)

        # Verificar se já existem notas para o aluno na matéria
        query_check = "SELECT * FROM leoP_nota WHERE id_Aluno = %s AND id_Materia = %s"
        mycursor.execute(query_check, (idAluno, idMateria))
        existing_notes = mycursor.fetchall()

        if existing_notes:
            mensagem = "As notas já foram atribuídas para o aluno nesta matéria."
            return render_template('cadastroNota.html', mensagem=mensagem)

        # Se não existem notas para a matéria em questão, realizar a inserção
        query_insert = 'INSERT INTO leoP_nota (id_Aluno, id_Materia, nota1, nota2, nota3, nota4) VALUES (%s, %s, %s, %s, %s, %s)'
        mycursor.execute(query_insert, (idAluno, idMateria, nota1, nota2, nota3, nota4))
        db.commit()

        return redirect(url_for('cadastro_nota'))

    if request.method == 'GET':
        query = ("SELECT idNota, a.nome, m.nomeMateria, n.nota1, n.nota2, n.nota3, n.nota4 FROM leoP_nota n INNER JOIN leoP_materia m ON n.id_Materia = m.idMateria INNER JOIN leoP_aluno a ON n.id_Aluno = a.idAluno")
        mycursor.execute(query)
        nota = mycursor.fetchall()

        return render_template('cadastroNota.html', notas=nota)

    return render_template('cadastroNota.html')


@app.route('/cadastrarNota')
def cadastrarNota():
    query = ("SELECT * FROM leoP_aluno")
    mycursor.execute(query)
    aluno = mycursor.fetchall()

    query = ("SELECT * FROM leoP_materia")
    mycursor.execute(query)
    materia = mycursor.fetchall()

    return render_template('cadastrarNota.html', alunos=aluno, materias=materia)


@app.route('/excluirNota/<int:id>', methods=['GET'])
def excluirNota(id):
    query = "DELETE FROM leoP_nota WHERE idNota = %s"
    mycursor.execute(query, (id,))
    db.commit()

    return redirect(url_for('cadastro_nota'))


@app.route('/updateNota/<int:id>', methods=['GET'])
def updateNota(id):
    query = "SELECT * FROM leoP_nota WHERE idNota = %s"
    mycursor.execute(query, (id,))
    nota = mycursor.fetchone()

    return render_template('updateNota.html', nota=nota)


@app.route('/updateNota', methods=['POST'])
def update_nota():
    if request.method == 'POST':
        id = request.form['id']
        nota1 = float(request.form['nota1'].replace(',', '.'))
        nota2 = float(request.form['nota2'].replace(',', '.'))
        nota3 = float(request.form['nota3'].replace(',', '.'))
        nota4 = float(request.form['nota4'].replace(',', '.'))

        # Validar as notas
        if not (0 <= nota1 <= 10) or not (0 <= nota2 <= 10) or not (0 <= nota3 <= 10) or not (0 <= nota4 <= 10):
            message = "Apenas notas de 0 a 10 são válidas!"
            return render_template('cadastroNota.html', message=message)

        query = "UPDATE leoP_nota SET nota1 = %s, nota2 = %s, nota3 = %s, nota4 = %s WHERE idNota = %s"
        mycursor.execute(query, (nota1, nota2, nota3, nota4, id,))
        db.commit()

        return redirect(url_for('cadastro_nota'))

    return render_template('updateNota.html')


app.run()
