from fastapi import FastAPI, HTTPException, Depends
from elasticsearch import Elasticsearch

from pydantic import BaseModel

app = FastAPI()

# Dependency to get the Elasticsearch client
def get_es():
    es = Elasticsearch([{'scheme': 'http', 'host': "localhost", 'port': 9200}])
    return es


class UserCreate(BaseModel):
    username: str
    email: str


class UserUpdate(BaseModel):
    email: str


# Create a user
@app.post("/users", response_model=dict)
def create_user(user: UserCreate, es: Elasticsearch = Depends(get_es)):
    es.index(index='users', body=user.model_dump())
    return {"message": "User created successfully"}


# Get a user
@app.get("/users/{username}", response_model=dict)
def get_user(username: str, es: Elasticsearch = Depends(get_es)):
    result = es.get(index='users', id=username, ignore=404)
    if result['found']:
        return result['_source']
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Update a user
@app.put("/users/{username}", response_model=dict)
def update_user(username: str, user: UserUpdate, es: Elasticsearch = Depends(get_es)):
    es.update(index='users', id=username, body={'doc': user.model_dump()}, ignore=404)
    return {"message": "User updated successfully"}


# Delete a user
@app.delete("/users/{username}", response_model=dict)
def delete_user(username: str, es: Elasticsearch = Depends(get_es)):
    es.delete(index='users', id=username, ignore=404)
    return {"message": "User deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
