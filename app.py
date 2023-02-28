from flask import Flask, render_template, request, redirect, flash
import sqlite3
import os
from main import MAI

currentdirectory = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dfgsgsa4vag'
id_user = 0
id_expert = 0
id_hr = 0


# Вхід в систему
@app.route('/', methods=['POST', 'GET'])
def login():
    global id_user
    global id_expert
    global id_hr
    if id_user != 0:
        return redirect('/open_vacancies')
    elif id_expert != 0:
        return redirect('/expert/vacancies')
    elif id_hr != 0:
        return redirect('/hr/hr_vac')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    if request.method == "POST":
        user = request.form['user']
        phone = str(request.form['phone'])

        password = str(request.form['password'])
        match user:
            case 'candidate':
                q1 = "SELECT * FROM candidate WHERE candidate.phone_can = ?;"
                person = cursor.execute(q1, (phone,)).fetchone()
                if person:
                    if password == person[3]:
                        id_user = person[0]
                        connection.close()
                        return redirect('/candidate')
                    else:
                        flash('Невірний пароль')
                else:
                    connection.close()
                    return redirect('/registr')
            case 'expert':
                q1 = "SELECT * FROM experts WHERE experts.phone = ?;"
                person = cursor.execute(q1, (phone,)).fetchone()
                if person:
                    if password == person[3]:
                        id_expert = person[0]
                        connection.close()
                        return redirect('/expert/vacancies')
                    else:
                        flash('Невірний пароль')
                else:
                    flash('Зверніться до адміністратора, щоб додав вас у систему!')
            case 'hr':
                if request.form['phone'] == "admin" and request.form['password'] == "admin":
                    connection.close()
                    id_hr = 1
                    return redirect('/hr/hr_vac')
                else:
                    flash('Невірні дані')
    connection.close()
    return render_template("index.html")


# Реєстрація
@app.route('/registr', methods=['POST', 'GET'])
def registr():
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    if request.method == "POST":
        phone = str(request.form['phone'])
        user_name = request.form['user_name']
        about_me = request.form['about_me']
        password = str(request.form['password'])
        cpassword = str(request.form['confirm_password'])

        q1 = "SELECT * FROM candidate WHERE candidate.phone_can = ?;"
        person = cursor.execute(q1, (phone,)).fetchone()
        print(person)
        if person:
            flash("Користувач уже зареєстрований")
        else:
            if password != cpassword:
                flash("Паролі не збігаються!")
            else:
                sql = "INSERT INTO candidate (name_can, phone_can, password, about_me) VALUES(?,?,?,?)"
                cursor.execute(sql, (user_name, phone, password, about_me))
                connection.commit()
                global id_user
                id_user = cursor.execute("SELECT id_can FROM candidate ORDER BY id_can DESC LIMIT 1").fetchone()[0]
                connection.close()
                return redirect('/open_vacancies')
    connection.close()
    return redirect("/")


# Виведення на екран вакансії на які кандидат надіслав резюме
@app.route('/candidate', methods=['POST', 'GET'])
def cndt():
    global id_user
    if id_user == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "SELECT id_vac, name_vac, v_c.id_cv, name_crit, value FROM (SELECT name_crit, id_cv, vacancies.* FROM criteria INNER JOIN crt_vac ON criteria.id_crit = crt_vac.id_c INNER JOIN ( SELECT id_vac, name_vac FROM vacancies WHERE status = 0 )as vacancies ON crt_vac.id_v = vacancies.id_vac ORDER BY id_vac, id_cv) as crt_vac INNER JOIN (SELECT id_cv, value FROM value_candidate WHERE id_can = ?) as v_c ON crt_vac.id_cv = v_c.id_cv"
    my_anc1 = cursor.execute(sql, (id_user,)).fetchall()
    my_anc = [[]]
    if len(my_anc1) != 0:
        id_vac = my_anc1[0][0]
        for m in my_anc1:
            if m[0] != id_vac:
                id_vac = m[0]
                my_anc.append([])
            my_anc[len(my_anc) - 1].append(m)
        del my_anc1
    connection.close()
    return render_template("cndt/candidate.html", my_anc=my_anc)


# Виведення відкритих вакансій на екран у підсистемі кандидата
@app.route('/open_vacancies', methods=['POST', 'GET'])
def open_vacancies():
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    open_vac = cursor.execute("SELECT * FROM vacancies WHERE status = FALSE").fetchall()

    connection.close()
    return render_template("cndt/open_vacancies.html", open_vac=open_vac)


# Надсилання/редагування резюме кандидата по вакансії в БД
@app.route('/open_vacancies/vacancy=<int:id_vac>', methods=['POST', 'GET'])
def vacancy(id_vac):
    global id_user
    if id_user == 0:
        return redirect('/')
    print(id_user)
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "SELECT id_cv, name_crit FROM crt_vac INNER JOIN criteria on crt_vac.id_c = criteria.id_crit WHERE crt_vac.id_v IN(SELECT id_vac FROM vacancies WHERE status = FALSE AND id_vac = ?);"
    anc_crit = cursor.execute(sql, (id_vac,)).fetchall()

    sql = "SELECT vacancies.name_vac, vacancies.about FROM vacancies WHERE vacancies.id_vac = ?;"
    vac_info = cursor.execute(sql, (id_vac,)).fetchone()
    if request.method == "POST":

        for el in anc_crit:
            row = (request.form["crit" + str(el[0])], el[0], id_user)
            sql = "SELECT EXISTS(SELECT * FROM value_candidate WHERE id_cv= ? and id_can = ?)"

            if cursor.execute(sql, (el[0], id_user,)).fetchone()[0] != 0:
                sql = "UPDATE value_candidate SET value = ? WHERE id_cv= ? and id_can = ?"
                cursor.execute(sql, row)

            else:
                sql = "INSERT INTO value_candidate (value, id_cv, id_can) VALUES(?,?,?)"
                cursor.execute(sql, row)
        # sql = "DELETE FROM value_candidate WHERE id_can = 0"
        # cursor.execute(sql)
        connection.commit()
        connection.close()
        return redirect('/candidate')
    connection.close()
    return render_template("cndt/vacancy.html", anc_crit=anc_crit, vac_info=vac_info)


# Видалення резюме кандидата по вакансії з БД
@app.route('/open_vacancies/vacancy=<int:id_vac>/delete')
def cand_vac_del(id_vac):
    global id_user
    if id_user == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = 'DELETE FROM value_candidate WHERE value_candidate.id_cv in (SELECT id_cv FROM crt_vac WHERE crt_vac.id_v = ?) and value_candidate.id_can = ?;'
    cursor.execute(sql, (id_vac, id_user,))
    connection.commit()
    connection.close()
    return redirect('/candidate')


# Виведення усіх вакансій на екран у підсистемі експерта
@app.route('/expert/vacancies')
def expert_vacancies():
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    global id_expert
    if id_expert == 0:
        return redirect('/')
    vac = cursor.execute("SELECT * FROM vacancies").fetchall()

    connection.close()
    return render_template("exprt/vacancies.html", vac=vac)


# Заповнення на запис в БД МПП критеріїв вакансії
@app.route('/expert/vacancy=<int:id_vac>/mpp', methods=['POST', 'GET'])
def mpp(id_vac):
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "SELECT id_cv, name_crit FROM crt_vac INNER JOIN criteria on crt_vac.id_c = criteria.id_crit WHERE id_v = ? ORDER BY id_cv"
    a = cursor.execute(sql, (id_vac,)).fetchall()
    mas = [e[1] for e in a]
    a = [e[0] for e in a]
    print(a)
    if request.method == "POST":
        value_crit = request.form.getlist('value_cr')
        k = 0
        for i in range(0, len(a)):
            for j in range(i + 1, len(a)):
                sql = "SELECT EXISTS(SELECT * FROM opinion_crit WHERE id_exp = ? and id_cv1 = ? and id_cv2 = ?)"

                if cursor.execute(sql, (id_expert, a[i], a[j],)).fetchone()[0] == 0:
                    sql = "INSERT INTO opinion_crit (id_exp, id_cv1, id_cv2, value) VALUES(?,?,?,?)"
                    cursor.execute(sql, (id_expert, a[i], a[j], value_crit[k],))
                else:
                    sql = "UPDATE opinion_crit SET value = ? WHERE id_exp = ? and id_cv1 = ? and id_cv2 = ?"
                    cursor.execute(sql, (value_crit[k], id_expert, a[i], a[j],))
                k += 1
        connection.commit()
        return redirect('/expert/vacancies')
    sql = "SELECT name_vac, about FROM vacancies WHERE id_vac = ?"
    v = cursor.execute(sql, (id_vac,)).fetchone()
    sql = "SELECT opinion_crit.value FROM opinion_crit WHERE opinion_crit.id_exp = ? and id_cv1 in (SELECT id_cv FROM crt_vac WHERE crt_vac.id_v = ?)"
    val = cursor.execute(sql, (id_expert, id_vac,)).fetchall()
    return render_template("exprt/mpp.html", v=v, id_vac=id_vac, mas=mas, val=val)


# Видалення матриці попарних порівнянь критеріїв вакансії
@app.route('/expert/vacancy=<int:id_vac>/mpp/del', methods=['POST', 'GET'])
def mpp_del(id_vac):
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql="DELETE FROM opinion_crit WHERE id_exp = ? and id_cv1 in (SELECT id_cv FROM crt_vac WHERE id_v = ?)"
    cursor.execute(sql, (id_expert, id_vac,))
    connection.commit()
    connection.close()
    return redirect('/expert/vacancy='+str(id_vac)+'/mpp')


# Створити нову вакансію
@app.route('/expert/new_vacancy', methods=['POST', 'GET'])
def new_vacancy():
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "SELECT * FROM criteria"
    crit = cursor.execute(sql).fetchall()
    if request.method == "POST":
        name_vacancy = request.form['name_vacancy']
        about = request.form['about']
        ids_crit = request.form.getlist('criteria')
        sql = 'SELECT EXISTS(SELECT * FROM vacancies WHERE name_vac = ?)'

        print(cursor.execute(sql, (name_vacancy,)).fetchone()[0])
        if cursor.execute(sql, (name_vacancy,)).fetchone()[0] == 0:
            sql = "INSERT INTO vacancies (name_vac, about) VALUES(?,?)"
            cursor.execute(sql, (name_vacancy, about))
            connection.commit()
            sql = 'SELECT id_vac FROM vacancies ORDER BY id_vac DESC'
            id_vac = cursor.execute(sql).fetchone()[0]
            sql = "INSERT INTO crt_vac (id_c, id_v) VALUES(?,?)"
            for id_crit in ids_crit:
                cursor.execute(sql, (id_crit, id_vac))
            connection.commit()
            return redirect('/expert/vacancy=' + str(id_vac) + '/mpp')
        else:
            flash("Вакансія уже існує")

    return render_template("exprt/new_vacancy.html", crit=crit)


# Додати нові критерії
@app.route('/expert/new_crit', methods=['POST', 'GET'])
def new_criteria():
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()

    if request.method == "POST":
        crit = request.form['new_crit'].split(", ")
        for c in crit:
            cursor.execute("INSERT INTO criteria (name_crit) VALUES(?)", (c,))
        connection.commit()
    connection.close()
    return redirect('/expert/new_vacancy')


# Видалити критерії з критеріальної бази
@app.route('/expert/del_crit', methods=['POST', 'GET'])
def del_criteria():
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()

    if request.method == "POST":
        ids_crit = request.form.getlist('criteria')
        print(ids_crit)
        sql = "DELETE FROM criteria WHERE id_crit = ?"
        for id_crit in ids_crit:
            cursor.execute(sql, (id_crit,))

        connection.commit()
    connection.close()
    return redirect('/expert/new_vacancy')


# Відкрити/закрити набір на вакансію
@app.route('/expert/vacancy=<int:id_vac>/set_status=<int:status>/close')
def open_close_vac(id_vac, status):
    global id_expert
    global id_hr
    if id_expert == 0 and id_hr == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "UPDATE vacancies SET status = ? WHERE id_vac = ?"
    cursor.execute(sql, (status, id_vac))
    connection.commit()
    connection.close()
    return '<script>document.location.href = document.referrer</script>'


# Видалення вакансії з БД
@app.route('/expert/vacancy=<int:id_vac>/delete')
def delete_vac(id_vac):
    global id_expert
    if id_expert == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    connection.execute("PRAGMA foreign_keys = 1")
    cursor = connection.cursor()
    sql = "DELETE FROM vacancies WHERE id_vac = ?"
    cursor.execute(sql, (id_vac,))
    connection.commit()
    connection.close()
    return redirect('/expert/vacancies')


# Виведення результатів роботи алгоритму МАІ
@app.route('/hr/vacancy=<int:id_vac>')
def hr(id_vac):
    global id_hr
    if id_hr == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()

    sql = "SELECT name_crit FROM criteria WHERE id_crit IN (SELECT id_c FROM crt_vac WHERE id_v =?)"
    name_crit = cursor.execute(sql, (id_vac,)).fetchall()
    sql = "SELECT name_can, phone_can, id_can, about_me  FROM candidate WHERE candidate.id_can IN (SELECT value_candidate.id_can FROM value_candidate WHERE value_candidate.id_cv IN (SELECT crt_vac.id_cv FROM crt_vac WHERE crt_vac.id_v = ?))"
    name_cand = cursor.execute(sql, (id_vac,)).fetchall()
    sql = "SELECT name_vac FROM vacancies WHERE id_vac = ?"
    name_vac = cursor.execute(sql, (id_vac,)).fetchone()
    mai, W, candW, GW = MAI(id_vac, len(name_crit))
    return render_template("hr/hr.html", mai=mai, name_crit=name_crit, W=W, name_cand=name_cand, candW=candW, GW=GW, name_vac=name_vac[0])


# Виведення усіх вакансій на екран у підсистемі рекрутера
@app.route('/hr/hr_vac')
def hr_vac():
    global id_hr
    if id_hr == 0:
        return redirect('/')
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    vac = cursor.execute("SELECT * FROM vacancies").fetchall()
    sql = "SELECT id_v, COUNT(id_can) FROM (SELECT crt_vac.id_v, candidate.id_can FROM candidate INNER JOIN value_candidate ON candidate.id_can = value_candidate.id_can INNER JOIN crt_vac WHERE value_candidate.id_cv = crt_vac.id_cv GROUP BY crt_vac.id_v, candidate.id_can) GROUP BY id_v"
    count = cursor.execute(sql).fetchall()
    sql = "SELECT DISTINCT id_v FROM crt_vac WHERE crt_vac.id_cv IN (SELECT opinion_crit.id_cv1 FROM opinion_crit)"
    ov = cursor.execute(sql).fetchall()
    ov = [list(e)[0] for e in ov]
    print(ov)

    connection.close()
    return render_template("hr/hr_vac.html", vac=vac, count=count, ov=ov)


# Розлогінення
@app.route('/logout')
def logout():
    global id_user
    id_user = 0
    global id_expert
    id_expert = 0
    global id_hr
    id_hr = 0
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
