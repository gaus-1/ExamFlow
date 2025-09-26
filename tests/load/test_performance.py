"""
Load тесты для ExamFlow - проверка производительности под нагрузкой
"""

import time
import random
from locust import HttpUser, task, between


class ExamFlowUser(HttpUser):
    """Пользователь ExamFlow для load тестирования"""
    
    wait_time = between(1, 3)  # Пауза между запросами
    
    def on_start(self):
        """Инициализация пользователя"""
        self.user_id = random.randint(1000, 9999)
        self.telegram_id = random.randint(100000, 999999)
        self.session_data = {}
        
        # Регистрируем пользователя
        self.register_user()
    
    def register_user(self):
        """Регистрация пользователя через Telegram Login Widget"""
        try:
            # Имитируем данные от Telegram Login Widget
            auth_data = {
                'id': self.telegram_id,
                'first_name': f'TestUser{self.user_id}',
                'username': f'testuser{self.user_id}',
                'auth_date': int(time.time()),
                'hash': 'test_hash_for_load_testing'
            }
            
            response = self.client.post('/telegram_auth/login/', 
                                      data=auth_data,
                                      name="telegram_auth_login")
            
            if response.status_code == 200:
                self.session_data = response.json()
                print(f"Пользователь {self.user_id} зарегистрирован")
            else:
                print(f"Ошибка регистрации пользователя {self.user_id}: {response.status_code}")
                
        except Exception as e:
            print(f"Ошибка в register_user: {e}")
    
    @task(3)
    def visit_homepage(self):
        """Посещение главной страницы"""
        response = self.client.get('/', name="homepage")
        
        if response.status_code != 200:
            print(f"Ошибка загрузки главной страницы: {response.status_code}")
    
    @task(2)
    def view_subjects(self):
        """Просмотр списка предметов"""
        response = self.client.get('/learning/subjects/', name="subjects_list")
        
        if response.status_code == 200:
            # Парсим список предметов
            try:
                subjects = response.json()
                if subjects and len(subjects) > 0:
                    # Выбираем случайный предмет
                    subject = random.choice(subjects)
                    self.view_subject_tasks(subject['id'])
            except:
                pass
    
    def view_subject_tasks(self, subject_id):
        """Просмотр заданий по предмету"""
        response = self.client.get(f'/learning/subjects/{subject_id}/tasks/', 
                                 name="subject_tasks")
        
        if response.status_code == 200:
            try:
                tasks = response.json()
                if tasks and len(tasks) > 0:
                    # Выбираем случайное задание
                    task = random.choice(tasks)
                    self.view_task_detail(task['id'])
            except:
                pass
    
    def view_task_detail(self, task_id):
        """Просмотр деталей задания"""
        response = self.client.get(f'/learning/tasks/{task_id}/', 
                                 name="task_detail")
        
        if response.status_code != 200:
            print(f"Ошибка загрузки задания {task_id}: {response.status_code}")
    
    @task(1)
    def use_ai_chat(self):
        """Использование AI чата"""
        if not self.session_data:
            return
            
        # Случайные вопросы для AI
        questions = [
            "Как решить квадратное уравнение?",
            "Объясни правило правописания 'жи-ши'",
            "Что такое производная?",
            "Как определить падеж существительного?",
            "Расскажи про теорему Пифагора"
        ]
        
        question = random.choice(questions)
        
        ai_data = {
            'prompt': question,
            'subject': random.choice(['математика', 'русский язык']),
            'user_id': self.telegram_id
        }
        
        response = self.client.post('/ai/chat/', 
                                  json=ai_data,
                                  headers={'Content-Type': 'application/json'},
                                  name="ai_chat")
        
        if response.status_code != 200:
            print(f"Ошибка AI чата: {response.status_code}")
    
    @task(1)
    def check_user_progress(self):
        """Проверка прогресса пользователя"""
        if not self.session_data:
            return
            
        response = self.client.get(f'/api/user/{self.telegram_id}/progress/', 
                                 name="user_progress")
        
        if response.status_code != 200:
            print(f"Ошибка получения прогресса: {response.status_code}")
    
    @task(1)
    def view_faq(self):
        """Просмотр FAQ"""
        response = self.client.get('/faq/', name="faq")
        
        if response.status_code != 200:
            print(f"Ошибка загрузки FAQ: {response.status_code}")
    
    @task(1)
    def view_features(self):
        """Просмотр функций"""
        response = self.client.get('/features/', name="features")
        
        if response.status_code != 200:
            print(f"Ошибка загрузки функций: {response.status_code}")


class ExamFlowAPIUser(HttpUser):
    """API пользователь для тестирования REST API"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Инициализация API пользователя"""
        self.user_id = random.randint(1000, 9999)
        self.telegram_id = random.randint(100000, 999999)
    
    @task(5)
    def test_api_endpoints(self):
        """Тестирование основных API endpoints"""
        
        # Тест получения списка предметов
        response = self.client.get('/api/subjects/', name="api_subjects")
        
        if response.status_code == 200:
            try:
                subjects = response.json()
                if subjects:
                    subject = random.choice(subjects)
                    
                    # Тест получения заданий по предмету
                    self.client.get(f'/api/subjects/{subject["id"]}/tasks/', 
                                  name="api_subject_tasks")
                    
                    # Тест получения конкретного задания
                    if subject.get('tasks'):
                        task = random.choice(subject['tasks'])
                        self.client.get(f'/api/tasks/{task["id"]}/', 
                                      name="api_task_detail")
            except:
                pass
    
    @task(3)
    def test_ai_api(self):
        """Тестирование AI API"""
        ai_data = {
            'prompt': 'Помоги решить уравнение x^2 + 5x + 6 = 0',
            'subject': 'математика',
            'user_id': self.telegram_id
        }
        
        response = self.client.post('/api/ai/chat/', 
                                  json=ai_data,
                                  headers={'Content-Type': 'application/json'},
                                  name="api_ai_chat")
        
        if response.status_code != 200:
            print(f"Ошибка AI API: {response.status_code}")
    
    @task(2)
    def test_health_check(self):
        """Тестирование health check endpoint"""
        response = self.client.get('/healthz/', name="health_check")
        
        if response.status_code != 200:
            print(f"Ошибка health check: {response.status_code}")


class ExamFlowHeavyUser(HttpUser):
    """Тяжелый пользователь для стресс-тестирования"""
    
    wait_time = between(0.1, 0.5)  # Минимальные паузы
    
    def on_start(self):
        """Инициализация тяжелого пользователя"""
        self.user_id = random.randint(1000, 9999)
        self.telegram_id = random.randint(100000, 999999)
    
    @task(10)
    def rapid_fire_requests(self):
        """Быстрые последовательные запросы"""
        # Быстрая последовательность запросов
        self.client.get('/', name="rapid_homepage")
        self.client.get('/learning/subjects/', name="rapid_subjects")
        self.client.get('/faq/', name="rapid_faq")
    
    @task(5)
    def concurrent_ai_requests(self):
        """Множественные одновременные AI запросы"""
        ai_data = {
            'prompt': f'Вопрос номер {random.randint(1, 1000)}',
            'subject': random.choice(['математика', 'русский язык']),
            'user_id': self.telegram_id
        }
        
        self.client.post('/ai/chat/', 
                        json=ai_data,
                        headers={'Content-Type': 'application/json'},
                        name="rapid_ai_chat")
    
    @task(3)
    def database_intensive_operations(self):
        """Операции, нагружающие базу данных"""
        # Запросы, которые могут нагрузить БД
        self.client.get('/api/subjects/', name="db_subjects")
        self.client.get('/api/tasks/', name="db_tasks")
        self.client.get('/api/users/', name="db_users")
