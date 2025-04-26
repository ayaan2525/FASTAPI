from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal, get_db

models.Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    #rating: Optional[int] = None

# Get credentials from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

while True:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            cursor_factory=RealDictCursor
        )
        # create a cursor
        cursor = conn.cursor()
        print("Database connection successful")
        break
    except Exception as error:
        print("Connection to database failed")
        print("Error: ", error)
        time.sleep(2)

my_posts = [{"title": "title of post 1", "content": "content of post 1", "id": 1}, {"title": "title of post 2", "content": "content of post 2", "id": 3}]

def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p

def find_index_post(id):
    for index, post in enumerate(my_posts):
        if post['id'] == id:
            return index

@app.get("/")
def root():
    return {"message": "Welcome to my api"}

@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    # cursor.execute("""SELECT *FROM posts""")
    # posts = cursor.fetchall()
    posts =db.query(models.Post).all()
    return {"data": posts}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post, db: Session = Depends(get_db)):
    #cursor.execute(""" INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""", 
    #               (post.title, post.content, post.published))
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"data": new_post}

@app.get("/posts/latest")
def get_latest_post():
    latest = my_posts[len(my_posts)-1]
    return {"detail": latest}

@app.get("/posts/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    #cursor.execute(""" SELECT * FROM posts WHERE id = %s""", (str(id)))
    #post = cursor.fetchone()
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} not found")   
    return {"post_Detail": post}

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    # cursor.execute(""" DELETE FROM posts WHERE id = %s RETURNING *""", (str(id)))
    # deleted_post = cursor.fetchone()
    # conn.commit()
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post, db: Session = Depends(get_db)):
    #cursor.execute(""" UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *""", (post.title, post.content, post.published, str(id)))
    #onn.commit()
    #updated_post = cursor.fetchone()
    post_update = db.query(models.Post).filter(models.Post.id == id)

    if post_update.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    post_update.update(post.dict(), synchronize_session=False)
    db.commit()

    return {'data': post_update.first()}

        