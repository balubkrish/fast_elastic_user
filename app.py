import os

from fastapi import FastAPI, HTTPException, Depends
from elasticsearch import Elasticsearch
from decouple import config
from pydantic import BaseModel

app = FastAPI()

ELASTIC_USER = config('ELASTIC_USER')
ELASTIC_PASSWORD = config('ELASTIC_PASSWORD')
# Dependency to get the Elasticsearch client
def get_es():
    es = Elasticsearch('http://host.docker.internal:9200', http_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
    return es


class UserCreate(BaseModel):
    username: str
    email: str


class UserUpdate(BaseModel):
    email: str


# Create a user
@app.post("/users", response_model=dict)
def create_user(user: UserCreate, es: Elasticsearch = Depends(get_es)):
    try:
        update_index_with_edge_ngram_analyzer('users')
    except Exception as e:
        pass
    es.index(index='users', body=user.model_dump())
    return {"message": "User created successfully"}


@app.get("/users", response_model=dict)
def retrieve_users(es: Elasticsearch = Depends(get_es)):
    body = {
        'size': 100,
        'query': {
            'match_all': {}
        }
    }
    response = es.search(index='users', body=body)
    documents = [{"id": hit['id'], "details": hit['_source']} for hit in response['hits']['hits']]
    return {"message": documents}


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


@app.post("/auto_complete/{search_text}", response_model=dict)
def auto_complete(search_text: str, es: Elasticsearch = Depends(get_es)):
    try:
        update_index_with_edge_ngram_analyzer('users')
    except Exception as e:
        pass
    body = {
        'query': {
            'match': {
                'username': {
                    'query': search_text,
                    'analyzer': 'edge_ngram_analyzer'
                }
            }
        }
    }
    response = es.search(index='users', body=body)
    # Extract relevant information from the response
    hits = response['hits']['hits']
    if hits:
        return {"names": [hit['_source']['username'] for hit in hits]}
    else:
        raise HTTPException(status_code=404, detail="User not found")


def update_index_with_edge_ngram_analyzer(index_name):
    es = get_es()

    # Define an index with a custom analyzer using edge n-grams
    index_settings = {
        "settings": {
            "analysis": {
                'tokenizer': {
                    'edge_ngram_tokenizer': {
                        'type': 'edge_ngram',
                        'min_gram': 1,
                        'max_gram': 50,
                        'token_chars': ['letter', 'digit']
                    }
                },
                'analyzer': {
                    'edge_ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'edge_ngram_tokenizer'
                    }
                }
            }
        },
        "mappings": {
                "properties": {
                    "username": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer"
                    },
                    "email": {
                        "type": "text"
                    }
                }
        }
    }

    # Create the index with the specified settings
    es.indices.create(index=index_name, body=index_settings)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
