import copy
import math

import numpy as np
import sqlite3
import os
from scipy.stats.mstats import gmean

currentdirectory = os.path.dirname(os.path.abspath(__file__))


# Вибірка кандидатів на вакансію
def find_cand(id_vac):
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    q1 = "SELECT DISTINCT candidate.* FROM candidate INNER JOIN value_candidate on candidate.id_can = value_candidate.id_can INNER JOIN (SELECT crt_vac.id_cv FROM vacancies INNER JOIN crt_vac on vacancies.id_vac = crt_vac.id_v WHERE vacancies.id_vac = ?) as cvid on value_candidate.id_cv = cvid.id_cv ORDER BY candidate.id_can"

    return cursor.execute(q1, str(id_vac)).fetchall()


# Запуск алгоритму МАІ
def MAI(id_vac, lenW):
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    sql = "SELECT DISTINCT id_exp FROM opinion_crit WHERE opinion_crit.id_cv1 IN(SELECT crt_vac.id_cv FROM crt_vac WHERE crt_vac.id_v=?)"
    ids_exp = cursor.execute(sql, (id_vac,)).fetchall()
    ids_exp = [list(e)[0] for e in ids_exp]
    W = np.zeros(lenW)
    i = 0
    for id_exp in ids_exp:
        i += 1
        cr = crit(id_vac, id_exp)
        W += np.array(vector(cr))
    W /= i
    W = np.around(W, 3)

    cand = np.array(Saati(id_vac))

    candW = []
    for el in cand:
        candW.append(vector(el))
    candW = np.around(np.array(candW), 3)

    GW = np.around(W.dot(candW), 3)

    return find_cand(id_vac)[np.argmax(GW)], W, candW, GW


# Побудова вектору пріоритетів
def vector(matrix):
    W = []
    S = 0
    for i in range(0, len(matrix)):
        a = round(gmean(matrix[i]), 5)
        S += a
        W.append(a)

    return [num / S for num in W]


# Зведення оцінок кандидатів до шкали Сааті
def Saati(id_vac):
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()
    q = "SELECT value_candidate.* FROM value_candidate INNER JOIN (SELECT crt_vac.id_cv FROM crt_vac WHERE crt_vac.id_v = ?) as cv on value_candidate.id_cv = cv.id_cv ORDER BY id_cv, id_can;"
    m = cursor.execute(q, str(id_vac)).fetchall()
    arr = []
    i = 0
    while len(m) != 0:
        arr.append([])
        e = copy.deepcopy(m[0])
        while e[1] == m[0][1]:
            arr[i].append(m[0])
            m.pop(0)
            if len(m) == 0:
                break
        i = i + 1
    del m
    del e

    for i in range(0, len(arr)):
        arr[i] = np.array(arr[i]).T.tolist()

        Max = max(arr[i][2])
        Min = min(arr[i][2])
        for j in range(0, len(arr[i][2])):
            if Max != Min:
                arr[i][2][j] = (arr[i][2][j] - Min) * 8 / (Max - Min) + 1
            else:
                arr[i][2][j] = 1
        arr[i] = np.array(arr[i]).T.tolist()


    b = []

    for k in range(0, len(arr)):
        a = np.zeros((len(arr[0]), len(arr[0])))
        for i in range(0, len(arr[k])):
            for j in range(i, len(arr[k])):
                a[i][j] = arr[k][i][2] / arr[k][j][2]
                a[j][i] = 1 / a[i][j]
        b.append(a.tolist())



    connection.close()
    return b


# Вибірка МПП критеріїв по вакансії з БД
def crit(id_vac, id_exp):
    connection = sqlite3.connect(currentdirectory + "\HR.db")
    cursor = connection.cursor()

    sql = "SELECT * FROM opinion_crit WHERE opinion_crit.id_cv1 IN(SELECT crt_vac.id_cv FROM crt_vac WHERE crt_vac.id_v=?) and opinion_crit.id_exp = ? ORDER BY id_cv1, id_cv2"
    op_crit = cursor.execute(sql, (id_vac, id_exp,)).fetchall()
    x = int((1 + math.sqrt(1 + 8*len(op_crit)))/2)
    cr = np.ones((x, x))
    for i in range(0, len(cr)):
        for j in range(i+1, len(cr)):
            cr[i][j] = op_crit[0][3]
            cr[j][i] = 1/cr[i][j]
            op_crit.pop(0)
    connection.close()
    return cr