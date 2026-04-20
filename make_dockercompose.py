import yaml

DOCKER_COMPOSE_HEADER = '''\
version: '3.2'
services:
'''

SERVICE_TEMPLATE = '''
  cactus:
    stdin_open: true
    tty: true
    build:
      context: ./
      dockerfile: Dockerfiles/Cactus/Dockerfile
    volumes:
      - type: bind
        source: ./results
        target: /results
      - type: bind
        source: ./input_data
        target: /input_data
    command:
      - /bin/bash
      - -c
      - |
        cactus-pangenome --help
'''

def main():
    with open('tools_config.yml', 'r') as file:
        config = yaml.safe_load(file)

    if not config or 'Cactus' not in config:
        raise ValueError("Cactus non trovato in tools_config.yml")

    with open('docker-compose.yml', 'w') as file_tmp:
        file_tmp.write(DOCKER_COMPOSE_HEADER)
        file_tmp.write(SERVICE_TEMPLATE)

    print("\nSuccessfully created docker-compose.yml for Cactus help test.\n")

if __name__ == '__main__':
    main()