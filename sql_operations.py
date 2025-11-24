import sqlite3
import re


con = sqlite3.connect("assemly.db")
cur = con.cursor()


class Details():
    ...


def inset_into_details(partNumber, name, amount, parent):
    partNumber, name, parent = map(lambda a: a.strip(), (partNumber, name, parent))
    pattern = r"КЛГИ\.\d{6}\.\d{3}"

    if not re.match(pattern, partNumber):
        raise Exception(f"формат номера у детали {name} не верен")

    if re.match(pattern, parent):
        cur.execute("""SELECT id from assembly_details WHERE partNumber = ?""", (parent, ))
        parent_id = cur.fetchone()[0]
    else:
        parent_id = None
    cur.execute("""SELECT id from assembly_details WHERE partNumber = ?""", (partNumber, ))

    detail_id = cur.fetchone()
    if detail_id:
        if parent_id:
            cur.execute("""UPDATE assembly_details SET amount = ?, parent_id = ? WHERE id = ?""", (amount,parent_id, detail_id[0] ))
        else:
            cur.execute("""UPDATE assembly_details SET amount = ? WHERE id = ?""",
                        (amount, detail_id[0]))
    else:
        try:
            cur.execute("""INSERT  INTO assembly_details(partNumber, name, amount, parent_id) VALUES (?,?,?,?)""", (partNumber, name, amount, parent_id))

        except Exception as e:
            con.rollback()
            print(f"error {e}")
    con.commit()

def get_details():
    cur.execute("""SELECT child.partNumber, child.name, child.amount, parent.partNumber, child.Drawing, child.Checked 
    FROM assembly_details as child left join assembly_details as parent ON child.parent_id= parent.id
    """)
    details = cur.fetchall()
    return details

def update_detail_status(partNumber, drawing, checked):
    print(drawing, checked)
    cur.execute("""UPDATE  assembly_details SET Drawing = ?, Checked = ? WHERE partNumber = ?""", (drawing, checked, partNumber))
    con.commit()
    return True

def incert_drawings(drawings):
    try:
        for drawing in drawings:
            cur.execute("""UPDATE assembly_details SET Drawing = 1 WHERE partNumber = ?""", (drawing, ))
        con.commit()
        affected_rows = cur.rowcount
        print(f"Обновлено строк: {affected_rows}")
    except Exception as e:
        print(e)
        con.rollback()

def get_info_for_stats():
    try:
        cur.execute("""SELECT COUNT(id), SUM(Drawing), SUM(Checked) FROM assembly_details """)
        data = list(cur.fetchone())
        data.append(round((data[1]+data[2]) / (2 * data[0]), 2))
        return data
    except Exception as e:
        return [e,]