import os 
from dotenv import load_dotenv

load_dotenv()

# Find the absolute file path to the top level project directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration class. Contains default configuration settings + configuration settings applicable to all environments
    """
    # Default settings
    FLASK_ENV = 'development'
    DEBUG = False
    TESTING = False

    # Settings applicable to all environments
    NUM_CLIENTS_TO_SUM = os.getenv('NUM_CLIENTS_TO_SUM')
    #LOG_FILE = os.getenv('LOG_FILE_DIR') + '/' + os.getenv('LOG_FILE_NAME')
    OAUTH2_PROVIDER_DOMAIN = os.getenv('OAUTH2_PROVIDER_DOMAIN')
    OAUTH2_PROVIDER_AUDIENCE = os.getenv('OAUTH2_PROVIDER_AUDIENCE')
    SERVER_ID = os.getenv('SERVER_ID')

    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    FLASK_ENV = 'production'