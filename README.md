## Getting Started

1) Clone repo:

```bash
git clone https://github.com/ArtemSerdechnyi/fastaip-meduzzen.git
```

2) Create .env in root directory base on .env.sample;


3) Use Makefile for run server:

```bash
make run
```

4) Check '/' path, by default 'http://localhost:8000/'.

5) Run tests:

```bash
make tests
```

6) Docker:
```bash
docker-compose build
```

```bash
docker-compose up
```

```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
```