class Config:
    DEBUG = True
    SECRET_KEY = 'cnjwn3hnkjjn39jd'
    PG_USER = 'postgres'
    PG_PSSWRD = 'nazar2415'
    PG_HOST = 'localhost'
    PG_PORT = '5050'
    PG_DATABASE = 'sparkchat'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{PG_USER}:{PG_PSSWRD}@{PG_HOST}/{PG_DATABASE}"
