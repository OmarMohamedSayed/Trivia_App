import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random


from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def get_paginate_questions(request, selection):
  page = request.args.get('page',1,type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  set up CORS. Allow '*' for origins.
  '''
  CORS(app)

  '''
  set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  @app.route('/categories')
  def get_all_categories():

    """Get all Categories with id and type
       or status code 500 due to server error
    """
    
    try:
      categories_query = Category.query.order_by(Category.id).all()
      formated_categorys = [category.format() for category in categories_query]

      return jsonify({
        'success':True,
        'categories':formated_categorys,
        'total_categories': len(formated_categorys)
      }),200
    except:
      abort(500)

  @app.route('/questions')
  def get_all_questions():
    """Get All Questions With Current Categories
      or Get status code 404 due to not have questions in this page"""
    try:
      questions = Question.query.order_by(Question.id).all()
      selected_question = get_paginate_questions(request,questions)

      categories = Category.query.order_by(Category.id).all()
      formated_categorys = [categ.format() for categ in categories]
      
      current_category = list(set(question['category'] for question in selected_question))

      if (len(selected_question) == 0):
        abort(404)

      return jsonify({
        'success':True,
        'questions':selected_question,
        'total_questions':len(questions),
        'categories':formated_categorys,
        'current_category': current_category
      }),200
    except:
      abort(404)

  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
    """Delete item by id
       or get status code 404 for noy found the item"""
    try:
      question_query = Question.query.filter_by(id=id).one_or_none()
      question_query.delete()

      return jsonify({
        'success':True,
        'deleted_item_id': id,
        'message':'question deleted'
      }),200
    except:
      abort(404)

  @app.route('/questions' , methods=['POST'])
  def create_question():
    body = request.get_json()
    

    question = body.get('question', '')
    answer = body.get('answer', '')
    difficulty = body.get('difficulty', '')
    category = body.get('category', '')

    if ((question == '') or (answer == '') or (difficulty == '') or (category == '')):
      abort(422)

    try:
      question_insert = Question(question=question , answer=answer, category=category, difficulty=difficulty)
      question_insert.insert()
      
      return jsonify({
      'success':True,
      'inserted': question_insert.id,
      'message':'question created'
      }),201

    except:
      abort(422)


  @app.route('/questions_search', methods=['POST'])
  def search_question():
    """Search question and return all questions like,
      or status code 422 if nothing in search 
      or status code 404 if not like any question"""

    body = request.get_json()
    search = body.get('searchTerm', '')
    if search == '':
      abort(422)

    try:
      search_result = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
      
      if len(search_result) == 0:
        abort(404)

      selected_items = get_paginate_questions(request, search_result)

      return jsonify({
        'success':True,
        'questions':selected_items,
        'total_questions':len(search_result)
      }),200

    except:
      abort(404)


  @app.route('/categories/<int:id>/questions')
  def get_questions_category(id):
    """get question by selected category
    or get status code 422 if category not found"""
    category = Category.query.filter(Category.id==id).one_or_none()
    if category is None:
      abort(422)

    question = Question.query.filter(Question.category==str(id)).order_by(Question.id).all()

    selected_question =  get_paginate_questions(request, question)
    
    return jsonify({
      'success': True,
      'questions': selected_question,
      'total_questions': len(question),
      'current_category': category.format()['type']
    })
    

  @app.route('/quizzes', methods=['POST'])
  def play_quiz_question():
    """Generate question on previous category without get same previous questions"""
    try:

      body = request.get_json()

      if not ('quiz_category' in body and 'previous_questions' in body):
          abort(400)

      quiz_category = body.get('quiz_category',None)
      previous_questions = body.get('previous_questions',None)
      
      if ((quiz_category is None) or (previous_questions is None)):
          abort(400)

      if quiz_category['id'] == 0:
          available_questions = Question.query.all()
      else:
          available_questions = Question.query.filter_by(category=quiz_category['id']).all()
      
      def new_question_gen():
        return available_questions[random.randrange(0, len(available_questions))].format() if len(available_questions) > 0 else None

      new_question = new_question_gen()
      
      while True:
        if new_question['id'] in previous_questions:
          new_question = new_question_gen()
        else:
          break

      return jsonify({
          'success': True,
          'question': new_question
      }),200  
    except:
      abort(400)

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "Bad Request"
      }), 400


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


  @app.errorhandler(422)
  def unprocessable_entity(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "Unprocessable"
      }), 422

  @app.errorhandler(500)
  def unprocessable_entity(error):
      return jsonify({
          "success": False,
          "error": 500,
          "message": "server error"
      }), 422

  return app

if __name__ == "__main__":
  app = create_app().run(debug=True)
    