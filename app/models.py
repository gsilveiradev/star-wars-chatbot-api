from pydantic import BaseModel

class UserQuery(BaseModel):
    user_input: str

class UserPreferences(BaseModel):
    people: str = ""
    planets: str = ""
    films: str = ""
    species: str = ""
    vehicles: str = ""
    starships: str = ""