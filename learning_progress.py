import sqlite3
import json

# Создание векторного хранилища обучения
class LearningDatabase:
    def __init__(self, db_path='learning_progress.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        # Таблица тем
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_name TEXT UNIQUE NOT NULL,
                category TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица прогресса по темам
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                completion_date TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        ''')
        
        # Таблица домашних заданий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS homeworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE NOT NULL,
                topic_name TEXT,
                status TEXT DEFAULT 'pending',
                completed_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def add_topic(self, topic_name, category='datetime'):
        self.cursor.execute(
            'INSERT OR IGNORE INTO topics (topic_name, category) VALUES (?, ?)',
            (topic_name, category)
        )
        self.conn.commit()
    
    def mark_completed(self, topic_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM topics WHERE topic_name = ?', (topic_name,))
        row = cursor.fetchone()
        
        if row:
            topic_id = row[0]
            cursor.execute('''
                INSERT OR IGNORE INTO progress (topic_id, completion_date) 
                VALUES (?, CURRENT_TIMESTAMP)
            ''', (topic_id,))
            self.conn.commit()
    
    def add_completed_topic_with_skills(self, topic_name, skills, date=None):
        """Добавляет выполненную тему с записью освоённых навыков."""
        cursor = self.conn.cursor()
        
        # Добавляем или получаем тему
        cursor.execute('SELECT id FROM topics WHERE topic_name = ?', (topic_name,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute(
                'INSERT INTO topics (topic_name, category, status) VALUES (?, ?, ?)',
                (topic_name, 'advanced', 'completed')
            )
            self.conn.commit()
            topic_id = cursor.lastrowid
        else:
            topic_id = row[0]
        
        # Проверяем и добавляем колонку skills, если её нет
        cursor.execute("PRAGMA table_info(topics)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'skills' not in columns:
            self.cursor.execute('ALTER TABLE topics ADD COLUMN skills TEXT')
            self.conn.commit()
        
        # Обновляем навыки для темы
        cursor.execute(
            'UPDATE topics SET skills = ? WHERE id = ?',
            (skills, topic_id)
        )
        
        # Добавляем запись о завершении с указанной датой
        completion_date = date if date else CURRENT_TIMESTAMP
        cursor.execute('''
            INSERT OR IGNORE INTO progress (topic_id, completion_date) 
            VALUES (?, ?)
        ''', (topic_id, completion_date))
        
        self.conn.commit()
    
    def add_homework(self, file_name, topic_name, notes=None):
        self.cursor.execute(
            'INSERT OR REPLACE INTO homeworks (file_name, topic_name, status, notes) VALUES (?, ?, ?, ?)',
            (file_name, topic_name, 'completed', notes)
        )
        self.conn.commit()
    
    def get_progress(self):
        cursor = self.conn.cursor()
        
        # Статистика по категориям
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM topics 
            GROUP BY category
        ''')
        stats = dict(cursor.fetchall())
        
        # Выполненные темы
        cursor.execute('''
            SELECT t.topic_name, p.completion_date, t.skills
            FROM topics t
            JOIN progress p ON t.id = p.topic_id
        ''')
        completed = list(cursor.fetchall())
        
        return {
            'stats': stats,
            'completed': completed
        }
    
    def get_homeworks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT file_name, status FROM homeworks ORDER BY id')
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()


# Инициализация базы данных и заполнение данными
db = LearningDatabase()

# Добавляем изученные темы
topics = [
    'datetime.strptime',
    'strftime форматирование дат',
    'timedelta интервалы времени',
    'Unix timestamp',
    'парсинг CSV логов'
]

for topic in topics:
    db.add_topic(topic, category='datetime')

# Отмечаем как выполненные
for topic in topics:
    db.mark_completed(topic)

# Добавляем продвинутый pandas с навыками
db.add_topic('Продвинутый pandas', category='advanced')
db.add_completed_topic_with_skills(
    'Продвинутый pandas',
    'conditional transformations, regex filtering, groupby aggregation, table merging',
    date='2026-06-07'
)

# Добавляем домашние задания
homeworks = [
    ('datatypes_cycles_1.ipynb', 'Python basics'),
    ('datatypes_cycles_2.ipynb', 'Datatypes and loops'),
    ('functions_1.ipynb', 'Functions')
]

for file_name, topic in homeworks:
    db.add_homework(file_name, topic)

# Вывод прогресса
progress = db.get_progress()
print("=== Статистика обучения ===")
for category, count in progress['stats'].items():
    print(f"{category}: {count} тем")

print("\n=== Выполненные темы ===")
for topic, date, skills in progress['completed']:
    if skills:
        print(f"[DONE] {topic} (skills: {skills})")
    else:
        print(f"[DONE] {topic}")

homeworks_list = db.get_homeworks()
print("\n=== Домашние задания ===")
for file_name, status in homeworks_list:
    print(f"- {file_name}: {status}")

db.close()
