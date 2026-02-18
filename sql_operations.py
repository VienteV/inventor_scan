import json
import sqlite3
import re


con = sqlite3.connect("assemly.db")
cur = con.cursor()


class Details():
    ...


def insert_into_details(partNumber, name, parent_parts):
    """
    Добавляет деталь и связывает ее с родительскими сборками

    Args:
        partNumber (str): Номер детали (формат КЛГИ.XXXXXX.XXX)
        name (str): Наименование детали
        amount (int): Количество
        parent_parts (list): Список номеров родительских сборок или пустой список
    """
    try:
        partNumber = partNumber.strip()
        name = name.strip()

        pattern = r"КЛГИ\.\d{6}\.\d{3}"
        if not re.match(pattern, partNumber):
            raise Exception(f"Формат номера у детали '{name}' не верен. Должен быть: КЛГИ.XXXXXX.XXX")

        cur.execute("""SELECT id FROM assembly_details WHERE partNumber = ?""", (partNumber,))
        result = cur.fetchone()

        if result:
            detail_id = result[0]
            cur.execute("""UPDATE assembly_details SET amount = amount + 1, name = ? WHERE id = ?""",
                        (name, detail_id))
            print(f"Обновлена существующая деталь: {partNumber}")
        else:
            cur.execute("""INSERT INTO assembly_details(partNumber, name, amount) VALUES (?, ?, 1)""",
                        (partNumber, name))
            detail_id = cur.lastrowid
            print(f"Создана новая деталь: {partNumber}")

        if parent_parts:
            if isinstance(parent_parts, str):
                parent_parts = [p.strip() for p in parent_parts.split(',') if p.strip()]

            for parent_part in parent_parts:
                parent_part = parent_part.strip()

                if not re.match(pattern, parent_part):
                    print(f"Предупреждение: Неверный формат родительской детали '{parent_part}' - пропускаем")
                    continue

                parent_part = parent_part[0:15]

                cur.execute("""SELECT id FROM assembly_details WHERE partNumber = ?""", (parent_part,))
                parent_result = cur.fetchone()

                if parent_result:
                    parent_id = parent_result[0]

                    cur.execute("""SELECT id FROM assembly_structure WHERE parent_id = ? AND child_id = ?""",
                                (parent_id, detail_id))

                    if cur.fetchone():
                        cur.execute(
                            """UPDATE assembly_structure SET quantity = quantity + 1 WHERE parent_id = ? AND child_id = ?""",
                            (parent_id, detail_id))
                        print(f"Обновлена связь: {parent_part} -> {partNumber}")
                    else:
                        cur.execute("""INSERT INTO assembly_structure(parent_id, child_id, quantity) VALUES (?,?,?)""",
                                    (parent_id, detail_id, 1))
                        print(f"Создана связь: {parent_part} -> {partNumber}")
                else:
                    print(f"Родительская сборка {parent_part} не найдена, создаем...")
                    cur.execute("""INSERT INTO assembly_details(partNumber, name, amount) VALUES (?,?,?)""",
                                (parent_part, "Автосозданная сборка", 0))
                    parent_id = cur.lastrowid

                    cur.execute("""INSERT INTO assembly_structure(parent_id, child_id, quantity) VALUES (?,?,?)""",
                                (parent_id, detail_id, 1))
                    print(f"Создана сборка {parent_part} и связь: {parent_part} -> {partNumber}")

        con.commit()
        print(f"Деталь {partNumber} успешно сохранена")

    except Exception as e:
        con.rollback()
        print(f"Ошибка при сохранении детали: {e}")
        raise

def get_details():

    cur.execute("""
        SELECT 
            d.partNumber, 
            d.name, 
            d.amount, 
            GROUP_CONCAT(p.partNumber, ', ') as parent_numbers,
            d.Drawing, 
            d.Checked, 
            d.Is_borrowed
        FROM assembly_details d
        LEFT JOIN assembly_structure s ON d.id = s.child_id
        LEFT JOIN assembly_details p ON s.parent_id = p.id
        GROUP BY d.id, d.partNumber, d.name, d.amount, d.Drawing, d.Checked, d.Is_borrowed
        ORDER BY d.partNumber
    """)
    details = cur.fetchall()
    return details

def update_detail_status(partNumber, drawing, checked, is_borrowed):

    try:
        cur.execute("""
            UPDATE assembly_details 
            SET Drawing = ?, Checked = ?, Is_borrowed = ? 
            WHERE partNumber = ?
        """, (drawing, checked, is_borrowed, partNumber))
        con.commit()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении статуса детали {partNumber}: {e}")
        con.rollback()
        return False

def incert_drawings(drawings):
    try:
        for drawing in drawings:
            cur.execute("""UPDATE assembly_details SET Drawing = 1 WHERE partNumber = ?""", (drawing, ))
        con.commit()
        affected_rows = cur.rowcount
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

def get_unique_assemblies():

    try:
        cur.execute("""SELECT DISTINCT parent.partNumber, parent.id
        FROM assembly_details as child left join assembly_details as parent ON child.parent_id= parent.id
        """)
        assembles= dict(cur.fetchall())

        return assembles
    except:
        con.rollback()
        return []


def get_details_by_assembly(assembly_partNumber):

    try:
        cur.execute("""
            SELECT 
                child.partNumber, 
                child.name, 
                s.quantity as amount_in_assembly,
                child.amount as total_amount,
                child.Drawing, 
                child.Checked, 
                child.Is_borrowed
            FROM assembly_structure s
            JOIN assembly_details child ON s.child_id = child.id
            JOIN assembly_details parent ON s.parent_id = parent.id
            WHERE parent.partNumber = ?
            ORDER BY child.partNumber
        """, (assembly_partNumber,))
        details = cur.fetchall()
        return details
    except Exception as e:
        print(f"Ошибка при получении деталей сборки {assembly_partNumber}: {e}")
        return []


def get_info_for_stats_by_assembly(assembly_partNumber):

    try:
        cur.execute("""
            SELECT 
                COUNT(*) as total_parts,
                SUM(CASE WHEN child.Drawing = 1 THEN 1 ELSE 0 END) as with_drawing,
                SUM(CASE WHEN child.Checked = 1 THEN 1 ELSE 0 END) as checked,
                AVG(CASE 
                    WHEN child.Drawing = 1 AND child.Checked = 1 THEN 1.0
                    WHEN child.Drawing = 1 OR child.Checked = 1 THEN 0.5
                    ELSE 0.0 
                END) as readiness_percentage
            FROM assembly_structure s
            JOIN assembly_details child ON s.child_id = child.id
            JOIN assembly_details parent ON s.parent_id = parent.id
            WHERE parent.partNumber = ?
        """, (assembly_partNumber,))

        result = cur.fetchone()
        if result:
            total, with_drawing, checked, readiness = result
            readiness_percentage = round((readiness or 0) * 100, 2)
            return [total, with_drawing, checked, readiness_percentage]
        return [0, 0, 0, 0]

    except Exception as e:
        print(f"Ошибка при получении статистики сборки {assembly_partNumber}: {e}")
        return [0, 0, 0, 0]


def delete_detail(part_number):
    try:
        cur.execute("""DELETE FROM assembly_details WHERE partNumber = ?""", (part_number, ))
        con.commit()
        return cur.rowcount > 0
    except Exception as e:
        con.rollback()
        print(e)
        return False


def get_parent_assemblies_for_part(partNumber):

    cur.execute("""
        SELECT 
            p.partNumber,
            p.name,
            s.quantity
        FROM assembly_structure s
        JOIN assembly_details p ON s.parent_id = p.id
        JOIN assembly_details c ON s.child_id = c.id
        WHERE c.partNumber = ?
        ORDER BY p.partNumber
    """, (partNumber,))
    return cur.fetchall()


def update_part_links(partNumber, assembly_list):
    try:
        cur.execute("BEGIN TRANSACTION")

        cur.execute("""
            DELETE FROM assembly_structure 
            WHERE child_id = (SELECT id FROM assembly_details WHERE partNumber = ?)
        """, (partNumber,))

        for assembly_part in assembly_list:
            cur.execute("""
                INSERT INTO assembly_structure (parent_id, child_id, quantity)
                SELECT 
                    (SELECT id FROM assembly_details WHERE partNumber = ?),
                    (SELECT id FROM assembly_details WHERE partNumber = ?),
                    1
                WHERE EXISTS (SELECT 1 FROM assembly_details WHERE partNumber = ?)
            """, (assembly_part, partNumber, assembly_part))

        cur.execute("COMMIT")
        return True
    except Exception as e:
        cur.execute("ROLLBACK")
        print(f"Ошибка при обновлении связей: {e}")
        return False


def delete_detail(partNumber):

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("""
            DELETE FROM assembly_structure 
            WHERE child_id = (SELECT id FROM assembly_details WHERE partNumber = ?)
        """, (partNumber,))

        cur.execute("""
            DELETE FROM assembly_structure 
            WHERE parent_id = (SELECT id FROM assembly_details WHERE partNumber = ?)
        """, (partNumber,))

        cur.execute("""
            DELETE FROM assembly_details WHERE partNumber = ?
        """, (partNumber,))

        cur.execute("COMMIT")
        return True
    except Exception as e:
        cur.execute("ROLLBACK")
        print(f"Ошибка при удалении детали {partNumber}: {e}")
        return False

def get_all_parts():
    cur.execute("SELECT partNumber, name FROM assembly_details ORDER BY partNumber")
    return cur.fetchall()

def get_all_assemblies():
    cur.execute("""
        SELECT DISTINCT 
            p.id,
            p.partNumber,
            p.name,
            COUNT(s.child_id) as child_count
        FROM assembly_details p
        LEFT JOIN assembly_structure s ON p.id = s.parent_id
        GROUP BY p.id, p.partNumber, p.name
        HAVING COUNT(s.child_id) > 0 OR p.name = 'Автосозданная сборка'
        ORDER BY p.partNumber
    """)
    return cur.fetchall()


def create_new_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assembly_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partNumber TEXT UNIQUE,
        name TEXT,
        amount INTEGER,
        drawing_link TEXT DEFAULT NULL,
        file_link TEXT DEFAULT NULL,
        Drawing INTEGER DEFAULT 0,
        Checked INTEGER DEFAULT 0,
        Is_borrowed INTEGER DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS assembly_structure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,  -- ID сборки
        child_id INTEGER NOT NULL,   -- ID детали в этой сборке
        quantity INTEGER DEFAULT 0,  -- Количество деталей в сборке
        UNIQUE(parent_id, child_id), -- Уникальная связь
        FOREIGN KEY (parent_id) REFERENCES assembly_details(id) ON DELETE CASCADE,
        FOREIGN KEY (child_id) REFERENCES assembly_details(id) ON DELETE CASCADE
    );""")

    cur.execute("""CREATE INDEX IF NOT EXISTS idx_parent_id ON assembly_structure(parent_id);""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_child_id ON assembly_structure(child_id);
    """)

def load_from_json():
    with open("assembly_components.json", 'r') as file:
        try:
            assembly = json.load(file)
        except Exception as e:
            print(e)

    for i in assembly:
        if "КЛГИ" in i["partNumber"]:
            try:
                insert_into_details(i["partNumber"], i["Description"], i["parent"])
            except Exception as e:
                print(e, i)

def clear_db():
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("""DROP TABLE IF EXISTS assembly_structure""")
        cur.execute("""DROP TABLE IF EXISTS assembly_details """)
        cur.execute("COMMIT")

        create_new_db()

        return True

    except Exception as e:
        cur.execute("ROLLBACK")
        print(f"Ошибка при удалении детали: {e}")
        return False

