import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia"
        self.database_path = "postgresql://{}:{}@{}/{}".format('omar','dodo','localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {
            'answer': 'new_answer',
            'category':'1',
            'difficulty':'2',
            'question': 'new_question'
        }

        self.new_question_id = Question.query.order_by(Question.id.desc()).first()
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass


    def test_get_paginated_questions(self):
        get_req = self.client().get('/questions')
        data = json.loads(get_req.data)

        self.assertEqual(get_req.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['categories']))
        self.assertEqual(len(data['questions']), 10)

    def test_404_questions(self):
        get_res = self.client().get('/questions?page=10000000000000')
        data = json.loads(get_res.data)

        self.assertEqual(get_res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_categories(self):
        get_res = self.client().get('/categories')
        data = json.loads(get_res.data)

        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))
        self.assertEqual(len(data['categories']), 6)

    def test_add_question(self):
        
        total_questions_before = len(Question.query.all())
        get_res = self.client().post('/questions', json=self.new_question)
        data = json.loads(get_res.data)
        total_questions_after = len(Question.query.all())

        self.assertEqual(get_res.status_code, 201)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], 'question created')
        self.assertEqual(total_questions_after, total_questions_before + 1)

    def test_422_add_question(self):
        new_question = {
            'question': '',
            'answer': '',
            'difficulty': '1',
            'category': '1',
        }
        get_res = self.client().post('/questions', json=new_question)
        data = json.loads(get_res.data)

        self.assertEqual(get_res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")


    def test_delete_question(self):

        new_id = int(self.new_question_id.format()['id'])
        get_res = self.client().delete("/questions/{}".format(new_id))
        data = json.loads(get_res.data)

        question = Question.query.filter(Question.id == new_id).one_or_none()

        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted_item_id'], new_id)
        self.assertEqual(data['message'], 'question deleted')
        self.assertEqual(question, None)

    def test_404_delete(self):
        get_res = self.client().delete('/questions/omar')
        data = json.loads(get_res.data)

        self.assertEqual(get_res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    
    def test_search(self):
        new_search = {'searchTerm': 'How'}
        get_res = self.client().post('/questions_search', json=new_search)
        data = json.loads(get_res.data)

        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertIsNotNone(data['questions'])
        self.assertIsNotNone(data['total_questions'])

    def test_422_search(self):
        new_search = {
            'searchTerm': '',
        }
        res = self.client().post('/questions_search', json=new_search)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")
    
    def test_404_search(self):
        new_search = {
            'searchTerm':'qweweqweqwerrrrr'
        }
        res = self.client().post('/questions_search', json=new_search)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_get_questions_category(self):
        res = self.client().get('/categories/2/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], 'Art')
        

    def test_422_invalid_category(self):
        res = self.client().get('/categories/10000/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")

    def test_quizzes(self):
        new_quiz = {"previous_questions": [18,19],"quiz_category": {"type": "Art", "id": "2"}}

        res = self.client().post('/quizzes', json=new_quiz)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertNotEqual(data['question']['id'], 18)
        self.assertNotEqual(data['question']['id'], 19)
        self.assertEqual(data['question']['category'], '2')

    def test_empty_quizzes(self):
        res = self.client().post('/quizzes', json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Bad Request")

    def test_400_quizzes(self):
        res = self.client().post('/quizzes', json={"previous_questions":""})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Bad Request")
    
    


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()