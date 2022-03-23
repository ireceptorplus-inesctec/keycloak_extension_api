# Keycloak Extension API

Service that extends the features of Keycloak by providing additional endpoints. The service connects directly to Keycloak's database.

Docker image availible at: https://hub.docker.com/r/irpinesctec/keycloak_extension_api

### Requirements

- Python 3 
- Keycloak running based on a PostreSQL database
- Check `requirements.txt` for additional package requirements. Can be installed through PIP or Conda.

### Running 

#### Natively 

1. Copy the `.env.example`and rename it to `.env`. 
   Open the file and edit it to match your environment.

2. Install requirements using your Python package manager of choice. With PIP:
   `pip install -r requirements.txt`
   
3. `python3 api.py`

#### Docker
1. Copy the `db_connection.env.example`and rename it to `db_connection.env`. 
   Open the file and edit it to match your environment.
   
2. Edit the `docker-compose.yml` to match your requirements`

3. `docker-compose up`