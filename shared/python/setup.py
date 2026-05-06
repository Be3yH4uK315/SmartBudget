from setuptools import find_packages, setup

setup(
    name="smartbudget-shared",
    version="1.0.0",
    description="Shared utilities and modules for SmartBudget microservices",
    author="SmartBudget Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.110.0",
        "sqlalchemy>=2.0.29",
        "redis>=5.0.1",
        "arq>=0.27.0",
        "pydantic-settings>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
        ],
    },
)
