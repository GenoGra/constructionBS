import yaml

DOCKER_COMPOSE_HEADER = '''\
services:
'''

SERVICE_TEMPLATE = {
    'Cactus': '''  
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
''',

    'Minigraph': '''
  minigraph:
    stdin_open: true
    tty: true
    build:
      context: ./
      dockerfile: Dockerfiles/Minigraph/Dockerfile
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
        cd /minigraph && ./minigraph
''',

    'MinigraphCactus': '''\
  minigraphcactus:
    stdin_open: true
    tty: true
    build:
      context: ./
      dockerfile: Dockerfiles/MinigraphCactus/Dockerfile
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
''',

    'PGGB': '''\
  pggb:
    stdin_open: true
    tty: true
    build:
      context: ./
      dockerfile: Dockerfiles/PGGB/Dockerfile
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
        cd /pggb && ./pggb
''',

    'ProgressiveCactus': '''\
  progressivecactus:
    stdin_open: true
    tty: true
    build:
      context: ./
      dockerfile: Dockerfiles/ProgressiveCactus/Dockerfile
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
        cactus --help
''',
}

def main():
    with open('tools_config.yml', 'r') as file:
        config = yaml.safe_load(file)

    with open('docker-compose.yml', 'w') as file_tmp:
        file_tmp.write(DOCKER_COMPOSE_HEADER)

        for tool in config:
            if tool not in SERVICE_TEMPLATE:
                raise ValueError(f"Nessun service template definito per {tool}")
            file_tmp.write(SERVICE_TEMPLATE[tool])

    print("\nSuccessfully created docker-compose.yml for help tests.\n")

if __name__ == '__main__':
    main()